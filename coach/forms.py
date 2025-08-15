from django import forms
from .models import Transaction, Category, Investment, InvestmentTransaction

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

class TransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories"
    )
    TYPE_CHOICES = [
        ('', 'All Types'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('savings', 'Savings'),
        ('investment', 'Investment'),
    ]
    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False
    )

class NewInvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['name', 'investment_type', 'total_amount_invested', 
                  'current_value', 'risk_level', 'date_created', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter investment name'}),
            'investment_type': forms.Select(attrs={'class': 'form-select'}),
            'total_amount_invested': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter initial amount'}),
            'current_value': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter current value (optional)'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'date_created': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter a description (optional)'}),
        }
        labels = {
            'name': 'Investment Name',
            'investment_type': 'Investment Type',
            'total_amount_invested': 'Initial Amount',
            'current_value': 'Current Value (optional)',
            'risk_level': 'Risk Level',
            'date_created': 'Investment Date',
            'description': 'Description (optional)',
        }

class AddToExistingInvestmentForm(forms.ModelForm):
    investment = forms.ModelChoiceField(
        queryset=Investment.objects.all(),
        required=True,
        label="Select Investment",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    transaction_type = forms.ChoiceField(
        choices=InvestmentTransaction.TRANSACTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = InvestmentTransaction
        fields = ['investment', 'transaction_type', 'amount', 'date', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter amount'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter a description (optional)'}),
        }
        labels = {
            'investment': 'Investment',
            'transaction_type': 'Transaction Type',
            'amount': 'Amount',
            'date': 'Date',
            'description': 'Description (optional)',
        }
