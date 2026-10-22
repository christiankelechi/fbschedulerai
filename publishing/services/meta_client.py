import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
import requests
from django.conf import settings
from publishing.models import MetaTokenVault, TokenVerificationStatus

logger = logging.getLogger(__name__)


class MetaAPIError(Exception):
    """Custom exception raised when Meta Graph API returns an error response."""
    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None, error_data: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.error_data = error_data or {}


class MetaGraphClient:
    """
    OOP Client for the Meta Graph API (v19.0+).
    Supports:
    1. Token & Page verification
    2. Feed Text Posts: POST /{page-id}/feed
    3. Branded Photos: POST /{page-id}/photos
    4. Video Reels: Full 3-Step Protocol (Start -> RUpload Binary Transfer -> Finish)
    """

    GRAPH_VERSION = "v19.0"
    BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

    def __init__(
        self,
        page_id: Optional[str] = None,
        access_token: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        vault = MetaTokenVault.objects.filter(is_active=True).first()
        self.page_id = (
            page_id
            or (vault.page_id if vault else None)
            or getattr(settings, 'META_PAGE_ID', '')
            or os.environ.get('META_PAGE_ID', '')
        )
        self.access_token = (
            access_token
            or (vault.access_token if vault else None)
            or getattr(settings, 'META_PAGE_ACCESS_TOKEN', '')
            or os.environ.get('META_PAGE_ACCESS_TOKEN', '')
        )
        self.app_secret = (
            app_secret
            or (vault.app_secret if vault else None)
            or getattr(settings, 'META_APP_SECRET', '')
            or os.environ.get('META_APP_SECRET', '')
        )

    def is_configured(self) -> bool:
        return bool(self.page_id and self.access_token)

    def verify_token(self) -> Dict[str, Any]:
        """
        Validates page ID and access token against the Meta Graph API.
        Updates MetaTokenVault record with the latest health status.
        """
        if not self.is_configured():
            return {
                'valid': False,
                'status': 'unconfigured',
                'message': 'Meta Page ID or Access Token is missing.'
            }

        url = f"{self.BASE_URL}/{self.page_id}"
        params = {
            "fields": "id,name,category,link",
            "access_token": self.access_token
        }

        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()

            if resp.status_code == 200 and 'id' in data:
                # Update vault in DB
                MetaTokenVault.objects.filter(page_id=self.page_id).update(
                    page_name=data.get('name', 'Facebook Page'),
                    verification_status=TokenVerificationStatus.VALID,
                    error_details=''
                )
                return {
                    'valid': True,
                    'status': 'valid',
                    'page_name': data.get('name'),
                    'page_id': data.get('id')
                }
            else:
                err_msg = data.get('error', {}).get('message', 'Unknown token validation failure.')
                MetaTokenVault.objects.filter(page_id=self.page_id).update(
                    verification_status=TokenVerificationStatus.INVALID,
                    error_details=err_msg
                )
                return {
                    'valid': False,
                    'status': 'invalid',
                    'message': err_msg,
                    'raw_error': data.get('error')
                }
        except Exception as e:
            logger.error(f"Failed to verify Meta token: {e}")
            return {
                'valid': False,
                'status': 'network_error',
                'message': str(e)
            }

    def publish_feed_post(self, message: str) -> Dict[str, Any]:
        """
        Publishes a standard text post directly to /{page-id}/feed.
        """
        self._require_configuration()
        url = f"{self.BASE_URL}/{self.page_id}/feed"
        payload = {
            "message": message,
            "access_token": self.access_token
        }

        logger.info(f"Publishing text feed post to Page {self.page_id}...")
        resp = requests.post(url, data=payload, timeout=30)
        return self._handle_response(resp)

    def publish_photo_post(self, photo_path: str, caption: str) -> Dict[str, Any]:
        """
        Uploads and publishes a photo post with caption to /{page-id}/photos.
        """
        self._require_configuration()
        if not os.path.isfile(photo_path):
            raise FileNotFoundError(f"Photo file not found at path: {photo_path}")

        url = f"{self.BASE_URL}/{self.page_id}/photos"
        data = {
            "caption": caption,
            "access_token": self.access_token
        }

        logger.info(f"Publishing photo post to Page {self.page_id} from {photo_path}...")
        with open(photo_path, "rb") as f:
            files = {"source": f}
            resp = requests.post(url, data=data, files=files, timeout=60)

        return self._handle_response(resp)

    def publish_reel_video(self, video_path: str, description: str) -> Dict[str, Any]:
        """
        Executes Meta's 3-step Reels upload protocol:
        Phase 1: Start Phase to generate video session ID and rupload URL.
        Phase 2: Transfer Phase to upload raw binary video data.
        Phase 3: Finish Phase to apply caption and trigger indexing/publishing.
        """
        self._require_configuration()
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found at path: {video_path}")

        file_size = os.path.getsize(video_path)
        logger.info(f"Initiating 3-step Reels upload ({file_size} bytes): {video_path}")

        # -------------------------------------------------------------
        # Step 1: Start Phase
        # -------------------------------------------------------------
        start_url = f"{self.BASE_URL}/{self.page_id}/video_reels"
        start_payload = {
            "upload_phase": "start",
            "access_token": self.access_token
        }

        start_resp = requests.post(start_url, data=start_payload, timeout=30)
        start_data = self._handle_response(start_resp)

        video_id = start_data.get("video_id")
        upload_url = start_data.get("upload_url")

        if not video_id or not upload_url:
            raise MetaAPIError("Meta did not return a valid video_id or upload_url during Phase 1.", error_data=start_data)

        logger.info(f"Reels Phase 1 OK. Video ID: {video_id}, Upload URL obtained.")

        # -------------------------------------------------------------
        # Step 2: Binary Transfer Phase
        # -------------------------------------------------------------
        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "offset": "0",
            "file_size": str(file_size)
        }

        logger.info("Reels Phase 2: Transferring binary video stream to Meta rupload infrastructure...")
        with open(video_path, "rb") as f:
            transfer_resp = requests.post(upload_url, headers=headers, data=f, timeout=180)

        self._handle_response(transfer_resp)
        logger.info("Reels Phase 2 OK. Binary transfer complete.")

        # -------------------------------------------------------------
        # Step 3: Finish Phase
        # -------------------------------------------------------------
        finish_url = f"{self.BASE_URL}/{self.page_id}/video_reels"
        finish_payload = {
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description,
            "access_token": self.access_token
        }

        logger.info(f"Reels Phase 3: Finishing publishing for video {video_id}...")
        finish_resp = requests.post(finish_url, data=finish_payload, timeout=45)
        finish_data = self._handle_response(finish_resp)

        logger.info(f"Reels Phase 3 OK. Video Reel successfully published: ID {video_id}")
        return {
            "id": video_id,
            "success": True,
            "phase": "finished",
            "meta_response": finish_data
        }

    def _require_configuration(self):
        if not self.is_configured():
            raise MetaAPIError(
                "Meta Graph API credentials are not configured. "
                "Please configure META_PAGE_ID and META_PAGE_ACCESS_TOKEN in .env or via MetaTokenVault."
            )

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except Exception:
            data = {"raw_text": response.text}

        if response.status_code >= 400 or "error" in data:
            error_info = data.get("error", {})
            message = error_info.get("message", f"HTTP {response.status_code}: {response.text}")
            code = error_info.get("code")
            subcode = error_info.get("error_subcode")
            logger.error(f"Meta Graph API Error [Code {code}:{subcode}]: {message}")
            raise MetaAPIError(message, code=code, subcode=subcode, error_data=data)

        return data
