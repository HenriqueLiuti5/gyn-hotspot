from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/login/',  views.LoginView.as_view(),  name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/me/',     views.MeView.as_view(),     name='me'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Sessões ativas
    path('sessions/active/', views.ActiveSessionsView.as_view(), name='active-sessions'),

    # Histórico de autenticação
    path('auth-history/', views.AuthHistoryView.as_view(), name='auth-history'),

    # Usuários registrados
    path('users/',             views.RegisteredUsersView.as_view(),      name='registered-users'),
    path('users/<str:username>/', views.RegisteredUserDetailView.as_view(), name='user-detail'),
]