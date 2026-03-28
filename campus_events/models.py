from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CampusEvent(models.Model):
    CATEGORY_CHOICES = [
        ('Hackathon', 'Hackathon'),
        ('Cultural', 'Cultural Fest'),
        ('Seminar', 'Seminar/Workshop'),
        ('Sports', 'Sports Event'),
        ('Placement', 'Placement Drive'),
        ('Other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='campus_events/', blank=True, null=True)
    organizer = models.CharField(max_length=150, help_text="Department or Club name")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['date']
