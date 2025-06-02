from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_choice, name='register_choice'),
    path('register/influencer/', views.InfluencerRegistrationView.as_view(), name='influencer_register'),
    path('register/business/', views.BusinessRegistrationView.as_view(), name='business_register'),
    path('profile/influencer/create/', views.InfluencerProfileCreateView.as_view(), name='influencer_profile_create'),
    path('profile/business/create/', views.BusinessProfileCreateView.as_view(), name='business_profile_create'),
    path('profile/influencer/edit/', views.InfluencerProfileUpdateView.as_view(), name='influencer_profile_edit'),
    path('profile/business/edit/', views.BusinessProfileUpdateView.as_view(), name='business_profile_edit'),
    path('profile/influencer/<int:pk>/', views.InfluencerProfileDetailView.as_view(), name='influencer_profile'),
    path('profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('profile/update-bio/', views.update_bio, name='update_bio'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]