from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return self.name
