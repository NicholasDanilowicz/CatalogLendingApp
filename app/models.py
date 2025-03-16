from django.db import models
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=9, choices=[
        ('patron', 'Patron'), 
        ('librarian', 'Librarian')
    ])
    def __str__(self):
        return f"User: {self.user.username} Role: {self.role}"

class Equipment(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='equipment/', blank=True, null=True, default='equipment_images/placeholder.jpg')
    def __str__(self):
        return self.name
    
    @property
    def image_url(self):
        if self.image:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.image}"
        return None

class Collection(models.Model):
    TAG_CHOICES = [
        ('sports', 'Sports'),
        ('exercise', 'Exercise'),
        ('outdoor', 'Outdoor'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    is_public = models.BooleanField(default=True)
    equipment = models.ManyToManyField('Equipment', blank=True, related_name='collections')
    allowed_users = models.ManyToManyField(User, blank=True, related_name='accessible_collections')
    tag = models.CharField(max_length=10, choices=TAG_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def can_user_access(self, user):
        if user.groups.filter(name='Librarian').exists():
            return True
        if self.is_public:
            return True
        return user in self.allowed_users.all()

    def can_add_equipment(self, equipment_item):
        if self.is_public:
            return not equipment_item.collections.filter(is_public=False).exists()
        else:
            return equipment_item.collections.count() == 0
