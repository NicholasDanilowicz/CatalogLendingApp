from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.db import models
from .auth_utils import is_librarian

TAG_CHOICES = [
    ('sports', 'Sports'),
    ('exercise', 'Exercise'),
    ('outdoor', 'Outdoor'),
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=9, choices=[
        ('patron', 'Patron'), 
        ('librarian', 'Librarian')
    ])
    real_name = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    join_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"User: {self.user.username} Role: {self.role}"

    @property
    def profile_picture_url(self):
        if self.profile_picture:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.profile_picture}"
        return 'https://upload.wikimedia.org/wikipedia/en/b/b1/Portrait_placeholder.png'

class Equipment(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    collections = models.ManyToManyField('Collection', blank=True, related_name='equipment_items')

    def __str__(self):
        return self.name
    
    @property
    def display_image_url(self):
        first_image = self.images.first()
        if first_image and first_image.image:
            return first_image.image_url
        return 'https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png'
    
    @property
    def all_images(self):
        images = list(self.images.all())
        if not images:
            return [{'url': 'https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png', 'is_default': False}]
        return [{'url': img.image_url, 'is_default': False} for img in images]

class EquipmentImage(models.Model):
    equipment = models.ForeignKey(Equipment, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='equipment/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.equipment.name}"
    
    @property
    def image_url(self):
        if self.image:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.image}"
        return None

    class Meta:
        ordering = ['-is_primary', '-created_at']

class Collection(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    allowed_users = models.ManyToManyField(User, blank=True, related_name='accessible_collections')
    tags = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_collections', null=True, blank=True)

    def __str__(self):
        return self.title

    def can_user_access(self, user):
        if is_librarian(user):
            return True
        if self.is_public:
            return True
        return user in self.allowed_users.all()

    def can_add_equipment(self, equipment_item):
        if self.is_public:
            return not equipment_item.collections.filter(is_public=False).exists()
        else:
            return equipment_item.collections.count() == 0

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class Rental(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rented_on = models.DateTimeField(default=timezone.now)
    return_by = models.DateTimeField(null=True, blank=True)
    returned_on = models.DateTimeField(null=True, blank=True)

    def can_user_rate(self, user, equipment):
        return Rental.objects.filter(user=user, equipment=equipment, returned_on__isnull=False).exists()

    def __str__(self):
        return f"{self.user.username} rented {self.equipment.name}"

    @property
    def is_overdue(self):
        if self.returned_on is None and self.return_by and timezone.now() > self.return_by:
            return True
        return False

class CollectionAccessRequest(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='access_requests')
    patron = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collection_access_requests')
    status = models.CharField(max_length=10, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request by {self.patron.username} for {self.collection.title} - {self.status}"

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment_ratings')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'equipment')

    def __str__(self):
        return f"{self.user.username} rated {self.equipment.name} with {self.rating} stars"


class RentalRequest(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    patron = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patron.username} requests {self.equipment.name} - {self.status}"
