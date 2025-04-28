import datetime
from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from .models import UserProfile

# class TestUserProfile(TestCase):
#     def test_str(self):
#         userprof = UserProfile.objects.create(user=User.objects.create())
#         userprof.user.username = 'John Doe'
#         userprof.role = 'patron'
#         self.assertEqual(str(userprof), "User: John Doe Role: patron")

class TestPageExists(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create()

    def test_app(self):
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        response = self.client.get('/app/logout/')
        self.assertEqual(response.status_code, 302)

    def test_search(self):
        response = self.client.get('/app/search/')
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        response = self.client.get('/app/profile/')
        self.assertEqual(response.status_code, 302)

    def test_search_query(self):
        response = self.client.get('/app/search/?query=ball')
        self.assertEqual(response.status_code, 200)

    def test_createcollection(self):
        response = self.client.get('/app/collection/create/')
        self.assertEqual(response.status_code, 302)
#
# class TestSearchEquipment(TestCase):
#     def test_content_search_fullword(self):
#         equipment = Equipment.objects.create(name='Ball', description='desc', available=True, collections=Collection.collections.set())
#         query = 'ball'
#         response = self.client.get('/app/search/?query=' + query)
#         self.assertContains(response, "Ball")

