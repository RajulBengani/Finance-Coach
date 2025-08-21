from django.urls import path
from . import views
urlpatterns=[
    path("", views.login_view, name="login"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("add_transaction/", views.add_transaction, name="add_transaction"),
    path("add_goal/", views.add_goal, name="add_goal"),
    path("edit_goal/<int:goal_id>/", views.edit_goal, name="edit_goal"),
    path("view_transactions", views.view_transactions,name="view_transactions"),
    path("transaction/<int:transaction_id>/edit/", views.edit_transaction, name="edit_transaction"),
    path("transaction/<int:transaction_id>/delete/", views.delete_transaction, name="delete_transaction"),
]