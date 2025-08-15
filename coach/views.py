from django.shortcuts import render, redirect, get_object_or_404
from .forms import TransactionForm, TransactionFilterForm, NewInvestmentForm, AddToExistingInvestmentForm
from .models import Transaction, Category, Investment, InvestmentTransaction
from django.contrib import messages
from django.db.models import Sum, Prefetch, Case, When, F, DecimalField
# Create your views here.
def home(request):
    total_income = Transaction.objects.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    total_savings = Transaction.objects.filter(type='savings').aggregate(Sum('amount'))['amount__sum'] or 0
    total_investment = Transaction.objects.filter(type='investment').aggregate(Sum('amount'))['amount__sum'] or 0
    total_balance = total_income - total_expense- total_savings - total_investment

    return render(request, 'coach/home.html', {
        'total_income': total_income,
        'total_expense': total_expense,
        'total_balance': total_balance
    })

def transactions(request):
    transactions = Transaction.objects.all().order_by('-date')
    form=TransactionFilterForm(request.GET or None)
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        category = form.cleaned_data.get('category')
        type = form.cleaned_data.get('type')

        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)
        if category:
            transactions = transactions.filter(category=category)
        if type:
            transactions = transactions.filter(type=type)
    return render(request, 'coach/transactions.html', {'form':form, 'transactions': transactions})

def add_transaction(request):
    if request.method=="POST":
        form= TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('transactions')
    else:
        form = TransactionForm()
    return render(request, 'coach/add_transaction.html', {'form': form})

def transactions_details(request, id):
    transaction = get_object_or_404(Transaction, pk=id)
    if request.method=="POST":
        if "delete" in request.POST:
            transaction.delete()
            messages.success(request, "Transaction deleted successfully!")
            return redirect('transactions')
        form= TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated successfully!")
            return redirect('transactions')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'coach/transaction_details.html', {'form':form, 'transaction': transaction})

def investments(request):
    investments = Investment.objects.prefetch_related(
        Prefetch(
            'transactions',
            queryset=InvestmentTransaction.objects.only(
                'id', 'date', 'transaction_type', 'description', 'amount'
            ).order_by('-date')
        )
    ).annotate(
        total_amount=Sum(
            Case(
                When(transactions__transaction_type='buy', then=F('transactions__amount')),
                When(transactions__transaction_type='sell', then=-F('transactions__amount')),
                default=0,
                output_field=DecimalField()
            )
        )
    ).order_by('-date_created')

    return render(request, 'coach/investments.html', {'investments': investments})

def add_investment(request):
    if request.method == "POST":
        form = NewInvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save()
            # Automatically create initial 'buy' transaction if total_amount_invested > 0
            if investment.total_amount_invested > 0:
                InvestmentTransaction.objects.create(
                    investment=investment,
                    transaction_type='buy',
                    amount=investment.total_amount_invested,
                    date=investment.date_created
                )
            messages.success(request, "Investment added successfully!")
            return redirect('investments')
    else:
        form = NewInvestmentForm()
    return render(request, 'coach/add_investment.html', {'form': form})


def add_to_investment(request):
    if request.method == "POST":
        form = AddToExistingInvestmentForm(request.POST)
        if form.is_valid():
            transaction = form.save()  # total_amount_invested updates automatically via save()
            messages.success(request, "Investment Transaction added successfully!")
            return redirect('investments')
    else:
        form = AddToExistingInvestmentForm()
    return render(request, 'coach/add_transaction.html', {'form': form})

def investment_details(request, id):
    investment = get_object_or_404(Investment, pk=id)
    if request.method == "POST":
        if "delete" in request.POST:
            investment.delete()
            messages.success(request, "Investment deleted successfully!")
            return redirect('investments')
        form = NewInvestmentForm(request.POST, instance=investment)
        if form.is_valid():
            form.save()
            messages.success(request, "Investment updated successfully!")
            return redirect('investments')
    else:
        form = NewInvestmentForm(instance=investment)

    return render(request, 'coach/investment_details.html', {
        'form': form,
        'investment': investment,
    })


#def transaction_history(request, investment_id=None):
    if investment_id:
        investment = get_object_or_404(Investment, pk=investment_id)
        transactions = investment.transactions.all().order_by('-date')
    else:
        transactions = InvestmentTransaction.objects.all().order_by('-date')
    
    context = {
        'transactions': transactions
    }
    return render(request, 'coach/transaction_history.html', context)



def savings(request):
    return render(request, 'coach/savings.html')