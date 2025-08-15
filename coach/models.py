from django.db import models
from django.utils import timezone

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('savings', 'Savings'),
        ('investment', 'Investment'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='income')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type} - {self.category} - {self.amount} on {self.date}"

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Investment(models.Model):
    INVESTMENT_TYPES = [
        ('stock', 'Stock'),
        ('mutual_fund', 'Mutual Fund'),
        ('bond', 'Bond'),
        ('crypto', 'Cryptocurrency'),
        ('gold', 'Gold'),
        ('other', 'Other'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    name = models.CharField(max_length=100)
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPES, default='other')
    total_amount_invested = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='medium')
    date_created = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    
    def profit_loss(self):
        """Calculate profit/loss if current_value is available"""
        if self.current_value is not None:
            return self.current_value - self.total_amount_invested
        return None

    def __str__(self):
        return f"{self.name} ({self.investment_type}) - {self.total_amount_invested}"

class InvestmentTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        """Automatically update total_amount_invested on the Investment"""
        if not self.pk:  # only update totals if new transaction
            if self.transaction_type == 'buy':
                self.investment.total_amount_invested += self.amount
            elif self.transaction_type == 'sell':
                self.investment.total_amount_invested -= self.amount
            self.investment.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type} - {self.investment.name} - {self.amount}"


    
    