from django import forms
from .models import Transaction, Goal, UserProfile, Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class TransactionForm(forms.ModelForm):
    class Meta:
        model=Transaction
        fields=['type', 'category', 'amount','date','description','goal']
        widgets={
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter a description (optional)'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter amount'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'placeholder': 'Enter category'}),
            'goal':forms.Select(attrs={'placeholder': 'Select A Goal'})
        }
        labels={
            'type': 'Transaction Type',
            'category': 'Category',
            'amount': 'Amount',
            'date': 'Date',
            'description': 'Description (optional)',
            'goal':'Select Goal (if Savings)'
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TransactionForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['goal'].queryset = Goal.objects.filter(user=user)
            self.fields['goal'].required = False
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
    phone_number=forms.CharField(max_length=15, required=False)
    risk_tolerance = forms.ChoiceField(choices=UserProfile.RISK_TYPES, required=False)
    profile_picture= forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 'risk_tolerance', 'profile_picture')
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', ''),
                risk_tolerance=self.cleaned_data.get('risk_tolerance', 'no_risk'),
                profile_picture=self.cleaned_data.get('profile_picture', None)
            )
        return user
