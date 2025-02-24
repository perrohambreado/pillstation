from django.db import models
from django import forms

# Create your models here.
class UserForm(forms.Form):
    username = forms.CharField(max_length=15)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)