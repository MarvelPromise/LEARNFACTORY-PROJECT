# Store/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import Customer


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        strip=False,
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with that email already exists.")
        return email

    def save(self, commit=True):
        # 1. Let the parent form create the User instance (without saving to DB yet)
        user = super().save(commit=False)

        # 2. Generate a base username from the part before '@'
        local_part = self.cleaned_data["email"].split("@")[0]
        base_username = slugify(local_part) or "user"

        # 3. Ensure that username is unique by appending a counter if needed
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user.username = username
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email']

