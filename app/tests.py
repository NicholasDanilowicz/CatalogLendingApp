import datetime
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, Equipment, Collection, Rental
from .forms import SearchForm, EquipmentForm, CollectionCreateForm, CommentForm

# class TestUserProfile(TestCase):
#     def test_str(self):
#         userprof = UserProfile.objects.create(user=User.objects.create())
#         userprof.user.username = 'John Doe'
#         userprof.role = 'patron'
#         self.assertEqual(str(userprof), "User: John Doe Role: patron")


# ***************************************************************************************
# *  REFERENCES
# *  Title: Debugging Django Static Files in Tests
# *  Author: OpenAI (ChatGPT)
# *  Date: 2025
# *  Code version: GPT-4o
# *  URL: https://chat.openai.com/
# *  Software License: OpenAI Terms of Use
# *  Description: Used to debug and resolve static files issues in Django tests by implementing the @override_settings decorator
# ***************************************************************************************

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
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

class TestEquipment(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.equipment = Equipment.objects.create(
            name='Test Equipment',
            description='Test Description',
            available=True
        )
    
    def test_equipment_str(self):
        self.assertEqual(str(self.equipment), 'Test Equipment')
    
    def test_equipment_isbn_generation(self):
        self.assertIsNotNone(self.equipment.isbn)
        self.assertEqual(len(self.equipment.isbn), 13)
    
    def test_equipment_available(self):
        self.assertTrue(self.equipment.available)
    
    def test_equipment_display_image_url(self):
        self.assertIsNotNone(self.equipment.display_image_url)

class TestCollection(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='user')
        cls.collection = Collection.objects.create(
            title='Test Collection',
            description='Test Description',
            is_public=True,
            creator=cls.user
        )
    
    def test_collection_str(self):
        self.assertEqual(str(self.collection), 'Test Collection')
    
    def test_collection_is_public(self):
        self.assertTrue(self.collection.is_public)
    
    def test_collection_can_user_access_public(self):
        other_user = User.objects.create(username='otheruser')
        self.assertTrue(self.collection.can_user_access(other_user))
    
    def test_collection_get_tags_list(self):
        self.collection.tags = 'sports,exercise'
        self.collection.save()
        self.assertEqual(self.collection.get_tags_list(), ['sports', 'exercise'])
    

