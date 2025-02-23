from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from .models import UserProfile

class TestUserProfile(TestCase):
    def test_str(self):
        userprof = UserProfile.objects.create(user=User.objects.create())
        userprof.user.username = 'John Doe'
        userprof.role = 'patron'
        self.assertEqual(str(userprof), "User: John Doe Role: patron")


