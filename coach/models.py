from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_delete
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal = models.ForeignKey('Goal', on_delete=models.SET_NULL, null=True, blank=True)  
            
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Optional validation: prevent exceeding target
        if self.current_amount > self.target_amount:
            raise ValueError("Current amount cannot exceed target amount")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

@receiver(pre_save, sender=Transaction)
def track_old_transaction(sender, instance, **kwargs):
    """
    Before updating a Transaction, keep track of its old state.
    """
    if instance.pk:  # Only for updates
        old_instance = Transaction.objects.get(pk=instance.pk)
        instance._old_amount = old_instance.amount
        instance._old_type = old_instance.type
        instance._old_goal = old_instance.goal
    else:
        instance._old_amount = None
        instance._old_type = None
        instance._old_goal = None


@receiver(post_save, sender=Transaction)
def update_goal_progress_on_save(sender, instance, created, **kwargs):
    """
    Adjust goal amounts on transaction create/update.
    """
    # Case 1: New savings transaction
    if created and instance.type == 'savings' and instance.goal:
        instance.goal.current_amount += instance.amount
        instance.goal.save()

    # Case 2: Updating an existing transaction
    elif not created:
        old_amount = instance._old_amount
        old_type = instance._old_type
        old_goal = instance._old_goal

        # If it was savings and linked to a goal before → revert the old value
        if old_type == 'savings' and old_goal:
            old_goal.current_amount -= old_amount
            old_goal.save()

        # If it is savings now → add the new value
        if instance.type == 'savings' and instance.goal:
            instance.goal.current_amount += instance.amount
            instance.goal.save()


@receiver(post_delete, sender=Transaction)
def update_goal_progress_on_delete(sender, instance, **kwargs):
    """
    Adjust goal when a savings transaction is deleted.
    """
    if instance.type == 'savings' and instance.goal:
        instance.goal.current_amount -= instance.amount
        instance.goal.save()