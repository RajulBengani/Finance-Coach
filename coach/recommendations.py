from django.db import models
from .models import Transaction
from decimal import Decimal
from django.db.models import Sum

def generate_savings_recommendation(user):
    income_total=Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    savings_total=Transaction.objects.filter(
        user=user, type='savings'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')


    if income_total ==0:
        return "You have no income recorded. Please add your income to get savings recommendations."
    
    saving_ratio= (savings_total / income_total) * 100 if income_total > 0 else 0

    if saving_ratio < 10:
        return "Your savings ratio is below 10%. Consider increasing your savings to improve your financial health."
    elif saving_ratio < 20:
        return "Your savings ratio is between 10% and 20%. This is a good start, but you can aim for a higher savings rate."
    elif saving_ratio < 30:
        return "Your savings ratio is between 20% and 30%. You're doing well, but there's room for improvement."
    else:
        return "Great job! Your savings ratio is above 30%. Keep up the good work!"

def generate_expense_recommendation(user):
    income_total = Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    expenses_total = Transaction.objects.filter(
        user=user, type='expense'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    if income_total == 0:
        return "You have no income recorded. Please add your income to get expense recommendations."
    
    expense_ratio = (expenses_total / income_total) * 100 if income_total > 0 else 0
    if expense_ratio > 90:
        return "⚠️ Your expenses are above 90% of your income. Try reducing discretionary spending."
    elif expense_ratio > 70:
        return "Your expenses are a bit high (70–90% of income). Consider saving more aggressively."
    elif expense_ratio > 50:
        return "Balanced spending. Aim to keep expenses under 50% for better savings."
    else:
        return "Great job! Your expenses are well under control."

def calculate_tax_recommendation(user):
    income_total = Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    if income_total == 0:
        return "You have no income recorded. Please add your income to get tax recommendations."

    # Example tax brackets (these should be updated based on actual tax laws)
    if income_total <= 250000:
        return "No tax liability (Income ≤ ₹2.5L)."
    elif income_total <= 500000:
        tax = (income_total - 250000) * Decimal('0.05')
        return f"Estimated Tax: ₹{tax:.2f} (5% Slab)."
    elif income_total <= 1000000:
        tax = Decimal('12500') + (income_total - 500000) * Decimal('0.20')
        return f"Estimated Tax: ₹{tax:.2f} (20% Slab)."
    else:
        tax = Decimal('112500') + (income_total - 1000000) * Decimal('0.30')
        return f"Estimated Tax: ₹{tax:.2f} (30% Slab)."

def generate_category_expense_recommendation(user):
    income_total=Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal ('0.00')

    if income_total == 0:
        return "You have no income recorded. Please add your income to get expense recommendations."
    
    category_expenses=Transaction.objects.filter(
        user=user, type='expense'
        ).values('category__name'
                 ).annotate(total=Sum('amount'))
    
    recommendations=[]
    for ce in category_expenses:
        category_name = ce['category__name']
        category_total = ce['total'] or Decimal('0')
        category_ratio = (category_total / income_total) * 100

        if category_ratio > 25:
            recommendations.append(
                f"⚠️ You spend {category_ratio:.0f}% of your income on {category_name}. Consider reducing to ≤25%."
            )
        elif category_ratio > 15:
            recommendations.append(
                f"Your spending on {category_name} is {category_ratio:.0f}% of income. Monitor it closely."
            )
        else:
            recommendations.append(
                f"Good! Spending on {category_name} is {category_ratio:.0f}% of your income."
            )

    if not recommendations:
        recommendations.append("No expenses recorded yet.")

    return recommendations
