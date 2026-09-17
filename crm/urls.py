from django.urls import path

from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('reports/', views.ReportView.as_view(), name='reports'),

    path('counterparties/', views.CounterpartyListView.as_view(), name='counterparty_list'),
    path('counterparties/create/', views.CounterpartyCreateView.as_view(), name='counterparty_create'),
    path('counterparties/<int:pk>/', views.CounterpartyDetailView.as_view(), name='counterparty_detail'),
    path('counterparties/<int:pk>/edit/', views.CounterpartyUpdateView.as_view(), name='counterparty_update'),
    path('counterparties/<int:pk>/delete/', views.CounterpartyDeleteView.as_view(), name='counterparty_delete'),

    path('deals/', views.DealListView.as_view(), name='deal_list'),
    path('deals/create/', views.DealCreateView.as_view(), name='deal_create'),
    path('deals/<int:pk>/', views.DealDetailView.as_view(), name='deal_detail'),
    path('deals/<int:pk>/edit/', views.DealUpdateView.as_view(), name='deal_update'),
    path('deals/<int:pk>/delete/', views.DealDeleteView.as_view(), name='deal_delete'),

    path('interactions/', views.InteractionListView.as_view(), name='interaction_list'),
    path('interactions/create/', views.InteractionCreateView.as_view(), name='interaction_create'),
    path('interactions/<int:pk>/edit/', views.InteractionUpdateView.as_view(), name='interaction_update'),
    path('interactions/<int:pk>/delete/', views.InteractionDeleteView.as_view(), name='interaction_delete'),

    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/toggle/', views.toggle_user_active, name='user_toggle'),

    path('audit/', views.AuditLogListView.as_view(), name='audit_list'),
]
