from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Skill
from organizations.models import Organization

User = get_user_model()

class RecruitmentPost(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='recruitment_posts')
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, related_name='recruitment_posts', blank=True)
    deadline = models.DateField()
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recruitment_posts_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.organization.name}"

class RecruitmentApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    post = models.ForeignKey(RecruitmentPost, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications_submitted')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'applicant')

    def __str__(self):
        return f"{self.applicant.username} for {self.post.title}"
