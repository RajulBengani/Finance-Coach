from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
class UserProfile(models.Model):
    RISK_TYPES=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk'),
        ('no_risk', 'No Risk'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    risk_tolerance = models.CharField(max_length=50, choices=RISK_TYPES, default='no_risk')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)

    def __str__(self):
        return self.user.username
    

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('savings', 'Savings'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='income')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    goal = models.ForeignKey('Goal', on_delete=models.SET_NULL, null=True, blank=True)  

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Automatically update goal's current_amount if this is a savings transaction
        if self.type == 'savings' and self.goal:
            self.goal.current_amount += self.amount
            self.goal.save()
            
    def __str__(self):
        return f"{self.type} - {self.category} - {self.amount} on {self.date}"

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Goal(models.Model):
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    target_date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.name

@receiver(pre_save, sender=Goal)  
def track_goal_progress(sender, instance, **kwargs):
    if instance.pk:
        old_instance=Goal.objects.get(pk=instance.pk)
        instance._old_current_amount = old_instance.current_amount
    else:
        instance._old_current_amount = 0

@receiver(post_save, sender=Goal)
def add_savings_transactions(sender, instance, created, **kwargs):
    from .models import Transaction, Category

    #Ensure "Goal Savinge" category exists
    category, _ = Category.objects.get_or_create(name="Goal Savings")

    # If this is an update to an existing goal
    old_amount= getattr(instance, '_old_current_amount', 0)
    if instance.current_amount > old_amount:
        # Calculate the difference
        difference = instance.current_amount - old_amount

        # Create a new savings transaction for the savings
        Transaction.objects.create(
            type='savings',
            category=category,
            amount=difference,
            date=timezone.now(),
            description=f"Goal Savings for {instance.name}",
            user=instance.user
        )
    