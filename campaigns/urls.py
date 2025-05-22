from django.urls import path
from . import views

urlpatterns = [
    path('', views.campaign_list, name='campaigns'),
    path('<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('create/', views.create_campaign, name='create_campaign'),
    path('<int:campaign_id>/edit/', views.edit_campaign, name='edit_campaign'),
    path('<int:campaign_id>/apply/', views.apply_campaign, name='apply_campaign'),
    path('<int:campaign_id>/applications/', views.campaign_applications, name='campaign_applications'),
]