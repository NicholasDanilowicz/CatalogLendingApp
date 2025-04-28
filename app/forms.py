# ***************************************************************************************
# *  REFERENCES
# *  Title: Form and Field Validation
# *  Author: Django Software Foundation
# *  Date: 2024
# *  Code version: Django 5.1
# *  URL: https://docs.djangoproject.com/en/5.1/ref/forms/validation/
# *
# *  Title: Django form field custom widgets
# *  Author: GeeksforGeeks
# *  Date: 2023
# *  URL: https://www.geeksforgeeks.org/django-form-field-custom-widgets/
# *
# *  Title: Django Forms
# *  Author: GeeksforGeeks
# *  Date: 2023
# *  URL: https://www.geeksforgeeks.org/django-forms/
# *
# *  Title: Debugging Django Code Errors with ChatGPT
# *  Author: OpenAI (ChatGPT)
# *  Date: 2025
# *  Code version: GPT-4o
# *  URL: https://chat.openai.com/
# *  Software License: OpenAI Terms of Use
# *  Description: Used to debug Django form errors while developing functionality for creating and editing equipment and collections (mainly with the save, clean, and init methods)
# ***************************************************************************************


from django import forms
from .models import Collection, TAG_CHOICES, Equipment, EquipmentImage, UserProfile, User, Comment
from django.contrib.auth.models import User
from .auth_utils import is_librarian

class SearchForm(forms.Form):
    query = forms.CharField(
        label='',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search for equipment...', 'class': 'search-input'})
    )

class EquipmentForm(forms.ModelForm):
    collections = forms.ModelMultipleChoiceField(
        queryset=Collection.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Collections'
    )

    class Meta:
        model = Equipment
        fields = ['name', 'location', 'description', 'available', 'collections']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location (e.g., UVA Recreation Center, Storage Room, etc.)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Provide a detailed description of the equipment...'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'collections': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Equipment Name',
            'location': 'Location',
            'description': 'Description',
            'available': 'Available for Checkout',
            'collections': 'Collections',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collections'].choices = [
            (collection.id, f"{collection.title} ({', '.join(collection.get_tags_list())})")
            for collection in Collection.objects.all()
        ]

    def clean_collections(self):
        collections = self.cleaned_data.get('collections')
        if not collections:
            return collections

        private_collections = collections.filter(is_public=False)
        public_collections = collections.filter(is_public=True)

        if private_collections.count() > 1:
            raise forms.ValidationError("Equipment can only be added to one private collection.")
        
        if private_collections.exists() and public_collections.exists():
            raise forms.ValidationError("Equipment cannot be added to both private and public collections simultaneously.")

        return collections

class CollectionAdminForm(forms.ModelForm):
    tags = forms.MultipleChoiceField(
        choices=TAG_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Collection
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.tags:
            self.initial['tags'] = self.instance.get_tags_list()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tags = ','.join(self.cleaned_data['tags'])
        if commit:
            instance.save()
        return instance

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['real_name', 'profile_picture']
        widgets = {
            'real_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'real_name': 'Full Name',
            'profile_picture': 'Profile Picture'
        }

class CollectionCreateForm(forms.ModelForm):
    tags = forms.MultipleChoiceField(
        choices=TAG_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Tags',
    )
    allowed_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(userprofile__role='patron'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'allowed-users-field'}),
        label='Allowed Users',
    )
    visibility = forms.ChoiceField(
        choices=[('public', 'Public Collection'), ('private', 'Private Collection')],
        widget=forms.RadioSelect,
        initial='public',
        label='Collection Visibility'
    )

    class Meta:
        model = Collection
        fields = ['title', 'description', 'tags', 'visibility', 'allowed_users']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'allowed_users': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
        }
        labels = {
            'title': 'Collection Title',
            'description': 'Description',
            'tags': 'Tags',
            'allowed_users': 'Allowed Users'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not is_librarian(self.user):
            self.fields.pop('visibility', None)
            self.fields.pop('allowed_users', None)
            if self.instance:
                self.instance.is_public = True
        else:
            if 'visibility' in self.initial and self.initial['visibility'] == 'private':
                self.fields['allowed_users'].widget.attrs['style'] = 'display: block;'
            else:
                self.fields['allowed_users'].widget.attrs['style'] = 'display: none;'

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get('visibility')
        
        if visibility == 'public':
            cleaned_data['is_public'] = True
            cleaned_data['allowed_users'] = []
        else:
            cleaned_data['is_public'] = False
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        visibility = self.cleaned_data.get('visibility')
        instance.is_public = (visibility == 'public')
        if 'tags' in self.cleaned_data:
            tags = self.cleaned_data['tags']
            if not tags:
                instance.tags = 'other'
            else:
                instance.tags = ','.join(tags)
        if commit:
            instance.save()
            if not instance.is_public and self.cleaned_data.get('allowed_users'):
                instance.allowed_users.set(self.cleaned_data['allowed_users'])
            else:
                instance.allowed_users.clear()
        return instance

class CollectionEditForm(CollectionCreateForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.get('user', None)
        super().__init__(*args, **kwargs)
        self.user = user
        
        if self.user and not is_librarian(self.user):
            if 'visibility' in self.fields:
                self.fields.pop('visibility')
            if 'allowed_users' in self.fields:
                self.fields.pop('allowed_users')
            self.instance.is_public = True
        else:
            if self.instance and hasattr(self.instance, 'is_public'):
                self.initial['visibility'] = 'private' if not self.instance.is_public else 'public'

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.creator and self.instance.creator != self.user and not is_librarian(self.user):
            raise forms.ValidationError("You don't have permission to edit this collection.")
        return cleaned_data

class PutItemInPublicCollectionForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['collections']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['collections'] = forms.ModelMultipleChoiceField(
                queryset=Collection.objects.filter(is_public=True, creator=self.user),
                required=False,
                widget=forms.CheckboxSelectMultiple,
                label='Public Collections'
            )

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your comment here...',
                'rows': 3,
            }),
        }