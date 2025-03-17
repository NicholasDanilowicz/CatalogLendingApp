from django import forms
from .models import Collection, TAG_CHOICES

class SearchForm(forms.Form):
    query = forms.CharField(
        label='',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search for equipment...', 'class': 'search-input'})
    )

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