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
    user=request.user
    profile=UserProfile.objects.filter(user=user).first()

    #income, expense, and savings totals
    income= Transaction.objects.filter(user=user, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = Transaction.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    savings=Transaction.objects.filter(user=user, type='savings').aggregate(Sum('amount'))['amount__sum'] or 0
    net_income = income - (expenses + savings)
    warning_msg=""
    if net_income < 0:
        warning_msg="⚠️ Your expenses and savings exceed your income! Consider reducing them."


    #Category-wise expense
    category_expenses = Transaction.objects.filter(user=user, type='expense').values('category__name').annotate(total=Sum('amount'))

    #Goals
    goals = Goal.objects.filter(user=user)
    goal_progress = []
    for g in goals:
        percent = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
        goal_progress.append({
            'id': g.id,
            'name': g.name,
            'current': g.current_amount,
            'target': g.target_amount,
            'percent': round(percent, 2)
    })

    # Last 30 days transactions
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=29)  # last 30 days including today

    # Group by date
    expenses_per_day = (
        Transaction.objects.filter(user=user, type='expense', date__range=[thirty_days_ago, today])
        .values('date')
        .annotate(total=Sum('amount'))
    )

    # Convert to dict {date: total}
    expenses_dict = {item['date']: item['total'] for item in expenses_per_day}

    # Build final list with 0s for missing days
    expenses_last_30_days = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        total = expenses_dict.get(day, 0)
        expenses_last_30_days.append({'date': day.strftime("%d %b"), 'total': total})


    #Get recommendations
    
    savings_msg= generate_savings_recommendation(user)
    tax_msg = calculate_tax_recommendation(user)
    expense_msg = generate_expense_recommendation(user)
    category_expense_msgs=generate_category_expense_recommendation(user)
    investment_opportunities = get_investment_opportunities(user)

    # Cache investment opportunities to prevent repeated yfinance calls on refresh
    cache_key = f"dash_invest_ops:{user.id}"
    investment_opportunities = cache.get(cache_key)
    if investment_opportunities is None:
        investment_opportunities = get_investment_opportunities(user)
        cache.set(cache_key, investment_opportunities, 300)  # 5 minutes

    # Lightweight post-processing for UI badges (works even if some fields are None)
    for inv in investment_opportunities if isinstance(investment_opportunities, list) else []:
        r1m = inv.get("return_1m")
        vol = inv.get("volatility_1m")
        if isinstance(r1m, (int, float)) and r1m > 0.05:
            inv["buy_signal"] = "✅ Potential Buy"
        elif isinstance(r1m, (int, float)) and r1m < -0.05:
            inv["buy_signal"] = "⚠️ Weak Momentum"
        else:
            inv["buy_signal"] = "⏳ Watchlist"
        # Normalize % strings for template (no crash if None)
        inv["return_1m_pct"] = f"{r1m*100:.1f}%" if isinstance(r1m, (int, float)) else "—"
        r1y = inv.get("return_1y")
        inv["return_1y_pct"] = f"{r1y*100:.1f}%" if isinstance(r1y, (int, float)) else "—"
        inv["volatility_1m_pct"] = f"{vol*100:.1f}%" if isinstance(vol, (int, float)) else "—"
        dy = inv.get("dividend_yield")
        inv["dividend_yield_pct"] = f"{dy*100:.1f}%" if isinstance(dy, (int, float)) else "—"

    adaptive_msg = _adaptive_advice(income, expenses, savings, investment_opportunities)
    context = {
        'name': user.username,
        'net_income': net_income,
        'expenses': expenses,
        'savings': savings,
        'category_expenses': list(category_expenses),
        'goals': goals,
        'expenses_last_30_days': expenses_last_30_days,
        'goal_progress': goal_progress,
        'profile': profile,
        'savings_msg': savings_msg,
        'tax_msg': tax_msg,
        'expense_msg': expense_msg,
        "category_expense_msgs": category_expense_msgs,
        'income':income,
        'warning_msg':warning_msg,
        'investment_opportunities': investment_opportunities,
        'adaptive_msg':adaptive_msg,

    }
    return render(request, 'coach/dashboard.html',context)

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