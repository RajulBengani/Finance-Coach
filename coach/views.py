from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Category, UserProfile, Goal
from .forms import TransactionForm, GoalForm, SignupForm
from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDate
from .recommendations import generate_savings_recommendation, calculate_tax_recommendation
from .recommendations import generate_expense_recommendation, generate_category_expense_recommendation 
from .recommendations import get_investment_opportunities
from django.core.cache import cache
from .services import dashboard_service, advice_service
# Create your views here.
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard after login
        else:
            error_message = "Invalid username or password"
            return render(request, 'coach/login.html', {'error': error_message})
    else:
        return render(request, 'coach/login.html')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'coach/signup.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    
    # --- Business Logic via Services ---
    income, expenses, savings, net_income = dashboard_service.get_income_expenses_savings(user)
    category_expenses = dashboard_service.get_category_expenses(user)
    goals, goal_progress = dashboard_service.get_goal_progress(user)
    expenses_last_30_days = dashboard_service.get_expenses_last_30_days(user)
    profile = dashboard_service.get_profile(user)

    warning_msg = "⚠️ Expenses and savings exceed your income!" if net_income < 0 else ""

    # --- Recommendations ---
    savings_msg = generate_savings_recommendation(user)
    tax_msg = calculate_tax_recommendation(user)
    expense_msg = generate_expense_recommendation(user)
    category_expense_msgs = generate_category_expense_recommendation(user)

    # Cached investment opportunities
    cache_key = f"dash_invest_ops:{user.id}"
    investment_opportunities = cache.get(cache_key)
    if investment_opportunities is None:
        investment_opportunities = get_investment_opportunities(user)
        cache.set(cache_key, investment_opportunities, 300)

    adaptive_msg = advice_service.adaptive_advice(income, expenses, savings, investment_opportunities)

   
    # --- Context ---
    context = {
        "name": user.username,
        "profile": profile,
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "net_income": net_income,
        "warning_msg": warning_msg,
        "category_expenses": list(category_expenses),
        "goals": goals,
        "goal_progress": goal_progress,
        "expenses_last_30_days": expenses_last_30_days,
        "savings_msg": savings_msg,
        "tax_msg": tax_msg,
        "expense_msg": expense_msg,
        "category_expense_msgs": category_expense_msgs,
        "investment_opportunities": investment_opportunities,
        "adaptive_msg": adaptive_msg,
        
    }
    return render(request, "coach/dashboard.html", context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user  # Set the user to the current logged-in user
            transaction.save()
            return redirect('dashboard')  # Redirect to the dashboard after saving
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'coach/add_transaction.html', {'form': form})

@login_required
def view_transactions(request):
    user = request.user

    # Fetch all transactions for the user
    transactions = Transaction.objects.filter(user=user).select_related("category").order_by("-date")

    # Optional filtering by type (income / expense / savings)
    tx_type = request.GET.get("type")
    if tx_type in ["income", "expense", "savings"]:
        transactions = transactions.filter(type=tx_type)

    # Optional filtering by category
    category_id = request.GET.get("category")
    if category_id:
        transactions = transactions.filter(category_id=category_id)

    # Aggregates for quick totals
    total_income = transactions.filter(type="income").aggregate(total=Sum("amount"))["total"] or 0
    total_expenses = transactions.filter(type="expense").aggregate(total=Sum("amount"))["total"] or 0
    total_savings = transactions.filter(type="savings").aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "transactions": transactions,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_savings": total_savings,
        "filter_type": tx_type,
        "filter_category": category_id,
        "categories": Category.objects.all()  # for dropdown filters
    }

    return render(request, "coach/view_transactions.html", context)

@login_required
def add_goal(request):
    if request.method=='POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('dashboard')  # Redirect to the dashboard after saving
    else:
        form = GoalForm()
    return render(request, 'coach/add_goal.html', {'form': form})

@login_required
def edit_goal(request,goal_id):
    goal=get_object_or_404(Goal,pk=goal_id, user=request.user )
    if request.method=='POST':
        form=GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = GoalForm(instance=goal)
    return render(request, 'coach/edit_goal.html', {'form': form, 'goal': goal})

def _adaptive_advice(income, expenses, savings, investments):

    """
    Tiny rule-based adaptive coach message based on user's cashflows and current recs.
    Non-invasive and requires no DB changes.
    """
    try:
        income_f = float(income)
        expenses_f = float(expenses)
        savings_f = float(savings)
    except Exception:
        income_f = expenses_f = savings_f = 0.0

    # Safely detect any high-vol items in current recs
    high_vol = False
    for inv in investments or []:
        vol = inv.get("volatility_1m")
        if isinstance(vol, (int, float)) and vol >= 0.02:
            high_vol = True
            break

    if income_f == 0:
        return "Add at least one income entry to unlock personalized investing advice."
    if expenses_f > income_f * 0.9:
        return "⚠️ Your expenses are ~90% of income. Reduce spending before adding higher-risk investments."
    if savings_f < income_f * 0.1:
        return "💡 Boost savings (≥10% of income) to create a safety buffer before taking market risk."
    if high_vol:
        return "⚠️ Several suggestions are volatile. Balance with ETFs or bonds for stability."
    return "✅ Good balance! You can explore more opportunities that fit your horizon and risk."

@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect("view_transactions")
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, "coach/edit_transaction.html", {"form": form, "transaction": transaction})


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == "POST":
        transaction.delete()
        return redirect("view_transactions")
    return render(request, "coach/delete_transaction.html", {"transaction": transaction})



