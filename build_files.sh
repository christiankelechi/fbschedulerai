#!/bin/bash
echo "Installing project dependencies..."
python3 -m pip install -r requirements.txt

echo "Running database migrations..."
python3 manage.py migrate --noinput

echo "Collecting static assets..."
python3 manage.py collectstatic --noinput --clear

echo "Vercel Build Complete."

