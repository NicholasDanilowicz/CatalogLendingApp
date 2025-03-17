# *************************************************************************************
# *  REFERENCES
# *  Title: Django Forms
# *  URL: https://www.geeksforgeeks.org/django-forms/
# *************************************************************************************

from django import forms
from .models import Collection, TAG_CHOICES, Equipment, EquipmentImage, UserProfile

class SearchForm(forms.Form):
    query = forms.CharField(
        label='',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search for equipment...', 'class': 'search-input'})
    )

class EquipmentEditForm(forms.ModelForm):
    collections = forms.ModelMultipleChoiceField(
        queryset=Collection.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Collections'
    )

    class Meta:
        model = Equipment
        fields = ['name', 'description', 'available', 'collections']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Equipment Name',
            'description': 'Description',
            'available': 'Available for Checkout',
        }
        help_texts = {
            'description': 'Provide a detailed description of the equipment.',
            'available': 'Check this box if the equipment is available for checkout.',
            'collections': 'Select the collections this equipment belongs to.',
        }

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
        help_texts = {
            'real_name': 'Enter your full name',
            'profile_picture': 'Upload a profile picture (optional)'
        }