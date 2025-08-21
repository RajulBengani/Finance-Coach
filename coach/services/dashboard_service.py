from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from ..models import Transaction, Goal, UserProfile

def get_income_expenses_savings(user):
    totals = (Transaction.objects
              .filter(user=user)
              .values("type")
              .annotate(total=Sum("amount")))

    income = next((x["total"] for x in totals if x["type"] == "income"), 0) or 0
    expenses = next((x["total"] for x in totals if x["type"] == "expense"), 0) or 0
    savings = next((x["total"] for x in totals if x["type"] == "savings"), 0) or 0

    net_income = income - (expenses + savings)
    return income, expenses, savings, net_income


def get_category_expenses(user):
    return (Transaction.objects.filter(user=user, type="expense")
            .values("category__name")
            .annotate(total=Sum("amount")))


def get_goal_progress(user):
    goals = Goal.objects.filter(user=user)
    progress = []
    for g in goals:
        percent = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
        progress.append({
            "id": g.id,
            "name": g.name,
            "current": g.current_amount,
            "target": g.target_amount,
            "percent": round(percent, 2)
        })
    return goals, progress


def get_expenses_last_30_days(user):
    today = timezone.now().date()
    start = today - timedelta(days=29)
    expenses = (Transaction.objects.filter(user=user, type="expense", date__range=[start, today])
                .values("date").annotate(total=Sum("amount")))

    expenses_dict = {item["date"]: item["total"] for item in expenses}
    result = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        result.append({"date": day.strftime("%d %b"), "total": expenses_dict.get(day, 0)})
    return result


def get_profile(user):
    return UserProfile.objects.filter(user=user).first()
