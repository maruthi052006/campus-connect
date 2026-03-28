from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()

class Organization(models.Model):
    ORG_TYPES = (
        ('Club', 'Club'),
        ('Startup', 'Startup'),
    )
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    type = models.CharField(max_length=20, choices=ORG_TYPES)
    description = models.TextField()
    domain = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='orgs/', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='orgs/covers/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_organizations')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class OrganizationMember(models.Model):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Moderator', 'Moderator'),
        ('Member', 'Member'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.organization.name} ({self.role})"

class JoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_join_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'user')
        
    def __str__(self):
        return f"Request: {self.user.username} to {self.organization.name}"

class RecruitmentPost(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_recruitment_posts')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='org_created_recruitment_posts')
    title = models.CharField(max_length=200)
    description = models.TextField()
    skills_required = models.CharField(max_length=500, blank=True)  # comma-separated skill names
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def skills_list(self):
        """Return skills_required as a list of stripped strings."""
        if not self.skills_required:
            return []
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

    def days_remaining(self):
        if not self.deadline:
            return None
        from django.utils import timezone
        delta = self.deadline - timezone.now().date()
        return delta.days

    def __str__(self):
        return f"{self.title} @ {self.organization.name}"

class RecruitmentApplication(models.Model):
    post = models.ForeignKey(RecruitmentPost, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_recruitment_applications')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.post.title}"
class Event(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.organization.name}"

    class Meta:
        ordering = ['date']
