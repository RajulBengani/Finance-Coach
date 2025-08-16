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
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log in the user after signup
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'coach/signup.html', {'form': form})

@login_required
def dashboard(request):
    user=request.user

    #income, expense, and savings totals
    income= Transaction.objects.filter(user=user, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = Transaction.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    savings=Transaction.objects.filter(user=user, type='savings').aggregate(Sum('amount'))['amount__sum'] or 0

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

    #Last 10 days transactions
    today = timezone.now().date()
    ten_days_ago = today - timedelta(days=9)

    # Group by date
    expenses_per_day = (
        Transaction.objects.filter(user=user, type='expense', date__range=[ten_days_ago, today])
        .values('date')
        .annotate(total=Sum('amount'))
    )

    # Convert to dict {date: total}
    expenses_dict = {item['date']: item['total'] for item in expenses_per_day}

    # Build final list with 0s for missing days
    expenses_last_10_days = []
    for i in range(9, -1, -1):
        day = today - timedelta(days=i)
        total = expenses_dict.get(day, 0)
        expenses_last_10_days.append({'date': day.strftime("%d %b"), 'total': total})

    context = {
        'name': user.username,
        'income': income,
        'expenses': expenses,
        'savings': savings,
        'category_expenses': list(category_expenses),
        'goals': goals,
        'expenses_last_10_days': expenses_last_10_days,
         'goal_progress': goal_progress,
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
        form = TransactionForm()
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
