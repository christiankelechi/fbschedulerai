from django.core.management.base import BaseCommand
from content.models import ContentPrompt, ContentCategory


class Command(BaseCommand):
    help = "Seeds initial curated Catholic reflection prompt bank for Rev. Fr. Ejiogu Chukwuemeka."

    PROMPT_DEFINITIONS = [
        {
            'category': ContentCategory.MORNING_PRAYER,
            'title': 'Morning Offering & Divine Grace',
            'prompt_text': (
                "Compose a devout, uplifting Catholic Morning Prayer from Rev. Fr. Ejiogu Chukwuemeka. "
                "Themes: Thanksgiving for waking to a new day, offering labors to Christ, protection of families, "
                "and seeking the guidance of the Holy Spirit throughout the day. Conclude with a warm pastoral blessing."
            ),
        },
        {
            'category': ContentCategory.DAILY_REFLECTION,
            'title': 'Living the Gospel in Daily Life',
            'prompt_text': (
                "Write a practical Catholic daily reflection from Rev. Fr. Ejiogu Chukwuemeka. "
                "Themes: Perseverance through daily trials, maintaining inner peace, practicing charity and forgiveness, "
                "and anchoring our hearts in Christ Jesus. Ground the message in a clear scripture citation."
            ),
        },
        {
            'category': ContentCategory.EVENING_REFLECTION,
            'title': 'Evening Examen & Night Blessing',
            'prompt_text': (
                "Craft an evening examen and peaceful bedtime prayer for the faithful from Rev. Fr. Ejiogu Chukwuemeka. "
                "Themes: Gratitude for God's blessings throughout the day, surrendering worries, asking pardon for failings, "
                "and seeking peaceful rest under Mother Mary's maternal mantle."
            ),
        },
        {
            'category': ContentCategory.SCRIPTURE,
            'title': 'Deep Scriptural Meditation',
            'prompt_text': (
                "Select a profound biblical passage and provide an inspiring theological and pastoral meditation "
                "by Rev. Fr. Ejiogu Chukwuemeka. Focus on God's fidelity, the sacraments, and growing in holiness."
            ),
        },
        {
            'category': ContentCategory.SAINT_OF_THE_DAY,
            'title': 'Virtues of the Saints',
            'prompt_text': (
                "Reflect upon the heroic virtues of a Catholic Saint or Doctor of the Church. "
                "Extract applicable spiritual wisdom and courage for Christians in today's world."
            ),
        },
        {
            'category': ContentCategory.SUNDAY_HOMILY,
            'title': 'Sunday Gospel Homily Exhortation',
            'prompt_text': (
                "Deliver an encouraging Sunday homily message breaking open the Word of God with pastoral depth, "
                "theological beauty, and hope in the Resurrection of Our Lord."
            ),
        },
    ]

    def handle(self, *args, **options):
        created_count = 0
        for data in self.PROMPT_DEFINITIONS:
            obj, created = ContentPrompt.objects.get_or_create(
                category=data['category'],
                title=data['title'],
                defaults={'prompt_text': data['prompt_text'], 'is_active': True}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: [{obj.get_category_display()}] {obj.title}"))
            else:
                self.stdout.write(f"Already exists: [{obj.get_category_display()}] {obj.title}")

        self.stdout.write(self.style.SUCCESS(f"\nPrompt bank seeding complete. Added {created_count} prompt(s)."))
