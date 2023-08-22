from django.urls import path, include

from .views.auth_views import UserLoginView, user_logout_view
from .views.dashboard_views import index as dashboard_index, table as table_index

urlpatterns = [
    path('', dashboard_index, name='index'),
    path('tables', table_index, name='table_index'),
    path('login/', UserLoginView.as_view(), name='login-user'),
    path('logout/', user_logout_view, name='logout'),
]
