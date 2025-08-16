from django import forms
from .models import Transaction, Goal, UserProfile, Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class TransactionForm(forms.ModelForm):
    class Meta:
        model=Transaction
        fields=['type', 'category', 'amount','date','description']
        widgets={
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter a description (optional)'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter amount'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'placeholder': 'Enter category'}),
        }
        labels={
            'type': 'Transaction Type',
            'category': 'Category',
            'amount': 'Amount',
            'date': 'Date',
            'description': 'Description (optional)',
        }
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'current_amount', 'target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter goal name'}),
            'target_amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter target amount'}),
            'current_amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter current amount'}),
        }
        labels = {
            'name': 'Goal Name',
            'target_amount': 'Target Amount',
            'current_amount': 'Current Amount',
            'target_date': 'Target Date',
        }

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        }
        labels = {
            'username': 'Username',
            'email': 'Email',
            'password1': 'Password',
            'password2': 'Confirm Password',
        }
