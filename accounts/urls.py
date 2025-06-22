from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_twitter

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_choice, name='register_choice'),
    path('register/influencer/', views.InfluencerRegistrationView.as_view(), name='influencer_register'),
    path('register/business/', views.BusinessRegistrationView.as_view(), name='business_register'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
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
    
    # Twitter metrics URLs
    path('twitter-metrics/', views_twitter.twitter_metrics_dashboard, name='twitter_metrics_dashboard'),
    path('twitter-metrics/refresh/', views_twitter.refresh_twitter_metrics, name='refresh_twitter_metrics'),
    path('api/twitter-metrics/', views_twitter.twitter_metrics_api, name='twitter_metrics_api'),
    path('api/twitter-posts/', views_twitter.twitter_posts_api, name='twitter_posts_api'),
]