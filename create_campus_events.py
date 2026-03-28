import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campusconnect.settings')
django.setup()

from campus_events.models import CampusEvent

def create_sample_events():
    events = [
        {
            'title': 'Grand Finale Hackathon 2026',
            'description': 'The ultimate coding showdown. 36 hours of non-stop innovation, mentorship, and thousands in prizes.',
            'category': 'Hackathon',
            'date': timezone.now() + timedelta(days=5, hours=10),
            'location': 'CS Main Auditorium',
            'organizer': 'Computer Science Dept'
        },
        {
            'title': 'Kalakriti Cultural Fest',
            'description': 'Experience the vibrant colors of our campus traditions. Dance, music, and theater from all clubs.',
            'category': 'Cultural',
            'date': timezone.now() + timedelta(days=12, hours=14),
            'location': 'Open Air Theatre (OAT)',
            'organizer': 'Arts & Culture Club'
        },
        {
            'title': 'AI in Fintech Workshop',
            'description': 'A deep dive into how artificial intelligence is transforming the financial sector. Specially for seniors.',
            'category': 'Seminar',
            'date': timezone.now() + timedelta(days=18, hours=9),
            'location': 'Seminar Hall B',
            'organizer': 'Entrepreneurship Cell'
        }
    ]
    
    for e_data in events:
        CampusEvent.objects.get_or_create(
            title=e_data['title'],
            defaults={
                'description': e_data['description'],
                'category': e_data['category'],
                'date': e_data['date'],
                'location': e_data['location'],
                'organizer': e_data['organizer']
            }
        )
    print("New campus events created!")

if __name__ == "__main__":
    create_sample_events()
