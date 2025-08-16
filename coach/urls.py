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
    ]