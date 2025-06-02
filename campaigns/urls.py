from django.urls import path
from . import views

urlpatterns = [
    path('', views.campaign_list, name='campaigns'),
    path('browse/', views.filterable_campaign_list, name='filterable_campaigns'),
    path('dashboard/', views.business_campaign_dashboard, name='business_campaign_dashboard'),
    path('<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('create/', views.create_campaign, name='create_campaign'),
    path('<int:campaign_id>/edit/', views.edit_campaign, name='edit_campaign'),
    path('<int:campaign_id>/apply/', views.apply_campaign, name='apply_campaign'),
    path('<int:campaign_id>/applications/', views.campaign_applications, name='campaign_applications'),
    path('<int:campaign_id>/update-status/', views.update_campaign_status, name='update_campaign_status'),
    path('application/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('<int:campaign_id>/message/<int:recipient_id>/', views.send_campaign_message, name='send_campaign_message'),
]