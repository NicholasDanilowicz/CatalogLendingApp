from django import forms

class SearchForm(forms.Form):
    search_text = forms.CharField(label='', max_length=100, required=False)