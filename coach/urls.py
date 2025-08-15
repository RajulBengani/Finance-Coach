from django.urls import path
from . import views
urlpatterns=[
    path("", views.home, name="home"),

    path("transactions/", views.transactions, name="transactions"),
    path('transactions_details/<int:id>/', views.transactions_details, name='transactions_details'),
    path("add_transaction/", views.add_transaction, name="add_transaction"),

    path("investments/", views.investments, name="investments"),
    path("add_investment/", views.add_investment, name="add_investment"),
    path("add_to_investment/", views.add_to_investment, name="add_to_investment"),
    path("investment_details/<int:id>/", views.investment_details, name="investment_details"),
    
    path("savings/", views.savings, name="savings"),

]