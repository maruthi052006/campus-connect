import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campusconnect.settings')
django.setup()

from organizations.models import Organization, Event

def create_sample_events():
    org, _ = Organization.objects.get_or_create(
        name="Tech Club",
        defaults={'type': 'Club', 'description': 'The official technology club.'}
    )
    
    events = [
        {
            'title': 'Hackathon 2026',
            'description': 'A 24-hour coding challenge for all students.',
            'date': timezone.now() + timedelta(days=5),
            'location': 'Main Library Basement'
        },
        {
            'title': 'Cultural Fest: Kalakriti',
            'description': 'Showcase your talent in dance, music, and art.',
            'date': timezone.now() + timedelta(days=12),
            'location': 'Open Air Theatre'
        },
        {
            'title': 'Startup Pitch Day',
            'description': 'Pitch your ideas to real investors and win prizes.',
            'date': timezone.now() + timedelta(days=20),
            'location': 'Seminar Hall B'
        }
    ]
    
    for e_data in events:
        Event.objects.get_or_create(
            title=e_data['title'],
            organization=org,
            defaults={
                'description': e_data['description'],
                'date': e_data['date'],
                'location': e_data['location']
            }
        )
    print("Sample events created!")

if __name__ == "__main__":
    create_sample_events()
