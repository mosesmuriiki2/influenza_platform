from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect

from .models import User, InfluencerProfile, BusinessProfile

def home(request):
    """Home page view"""
    return render(request, 'accounts/home.html')

def register_choice(request):
    """View to choose registration type (influencer or business)"""
    return render(request, 'accounts/register_choice.html')

class CustomLoginView(LoginView):
    """Custom login view with redirection based on user type"""
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        """Override form_valid to add success message and redirect based on user type"""
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back! You've successfully logged in.")
        return response
    
    def form_invalid(self, form):
        """Override form_invalid to add error message for incorrect login"""
        messages.error(self.request, "Invalid email or password. Please try again.")
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirect users based on their user type"""
        user = self.request.user
        if user.is_authenticated:
            return reverse_lazy('dashboard')
        return reverse_lazy('home')

class InfluencerRegistrationView(CreateView):
    """View for influencer registration"""
    model = User
    template_name = 'accounts/influencer_register.html'
    fields = ['email', 'first_name', 'last_name', 'password']
    success_url = reverse_lazy('influencer_profile_create')
    
    def form_valid(self, form):
        # Set user type to influencer
        user = form.save(commit=False)
        user.user_type = 'influencer'
        user.set_password(form.cleaned_data['password'])
        user.save()
        login(self.request, user)
        messages.success(self.request, "Registration successful! Please complete your profile.")
        return super().form_valid(form)

class BusinessRegistrationView(CreateView):
    """View for business registration"""
    model = User
    template_name = 'accounts/business_register.html'
    fields = ['email', 'first_name', 'last_name', 'password']
    success_url = reverse_lazy('business_profile_create')
    
    def form_valid(self, form):
        # Set user type to business
        user = form.save(commit=False)
        user.user_type = 'business'
        user.set_password(form.cleaned_data['password'])
        user.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, "Registration successful! Please complete your business profile.")
        return super().form_valid(form)

class InfluencerProfileCreateView(CreateView):
    """View for creating influencer profile after registration"""
    model = InfluencerProfile
    template_name = 'accounts/influencer_profile_create.html'
    fields = ['full_name', 'bio', 'profile_picture', 'phone_number', 'date_of_birth',
              'instagram_handle', 'twitter_handle', 'tiktok_handle', 'youtube_channel',
              'facebook_page', 'categories']
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Your influencer profile has been created successfully!")
        return super().form_valid(form)

class BusinessProfileCreateView(CreateView):
    """View for creating business profile after registration"""
    model = BusinessProfile
    template_name = 'accounts/business_profile_create.html'
    fields = ['company_name', 'company_logo', 'industry', 'company_size', 'website',
              'description', 'contact_person', 'contact_email', 'contact_phone',
              'address', 'business_type', 'year_established']
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Your business profile has been created successfully!")
        return super().form_valid(form)

@login_required
def dashboard(request):
    """Dashboard view based on user type"""
    user = request.user
    
    if user.user_type == 'influencer':
        try:
            profile = user.influencer_profile
            # Calculate total followers across platforms
            total_followers = 0
            social_media_stats = {}
            
            # Instagram followers
            if profile.instagram_handle:
                instagram_followers = 1000  # Placeholder - integrate with Instagram API
                total_followers += instagram_followers
                social_media_stats['instagram'] = instagram_followers
            
            # Twitter followers
            if profile.twitter_handle:
                twitter_followers = 800  # Placeholder - integrate with Twitter API
                total_followers += twitter_followers
                social_media_stats['twitter'] = twitter_followers
            
            # TikTok followers
            if profile.tiktok_handle:
                tiktok_followers = 2000  # Placeholder - integrate with TikTok API
                total_followers += tiktok_followers
                social_media_stats['tiktok'] = tiktok_followers
            
            # YouTube subscribers
            if profile.youtube_channel:
                youtube_subscribers = 5000  # Placeholder - integrate with YouTube API
                total_followers += youtube_subscribers
                social_media_stats['youtube'] = youtube_subscribers
            
            # Facebook followers
            if profile.facebook_page:
                facebook_followers = 1500  # Placeholder - integrate with Facebook API
                total_followers += facebook_followers
                social_media_stats['facebook'] = facebook_followers
            
            # Get active campaigns that the influencer has been accepted for
            from campaigns.models import Campaign, CampaignApplication
            
            # Get applications made by this influencer
            applications = CampaignApplication.objects.filter(influencer=profile)
            applications_count = applications.count()
            
            # Get active campaigns where the influencer's application has been accepted
            active_campaigns = Campaign.objects.filter(
                applications__influencer=profile,
                applications__status='accepted',
                status='active'
            )
            
            # Add progress percentage to each campaign (placeholder calculation)
            import datetime
            for campaign in active_campaigns:
                # Calculate progress based on start and end dates
                today = datetime.date.today()
                if today < campaign.start_date:
                    campaign.progress = 0
                elif today > campaign.end_date:
                    campaign.progress = 100
                else:
                    total_days = (campaign.end_date - campaign.start_date).days
                    days_passed = (today - campaign.start_date).days
                    campaign.progress = min(100, int((days_passed / total_days) * 100))
            
            # Get available campaigns that the influencer hasn't applied to
            available_campaigns = Campaign.objects.filter(
                status='active'
            ).exclude(
                applications__influencer=profile
            )[:6]  # Limit to 6 campaigns
            
            return render(request, 'accounts/influencer_dashboard.html', {
                'profile': profile,
                'total_followers': total_followers,
                'social_media_stats': social_media_stats,
                'unread_messages': get_unread_messages_count(user),
                'applications': applications[:5],  # Show only the 5 most recent applications
                'applications_count': applications_count,
                'active_campaigns': active_campaigns,
                'available_campaigns': available_campaigns
            })
        except InfluencerProfile.DoesNotExist:
            messages.warning(request, "Please complete your influencer profile to access your dashboard.")
            return redirect('influencer_profile_create')
    
    elif user.user_type == 'business':
        try:
            profile = user.business_profile
            # Get all influencers for the business to view
            influencers = InfluencerProfile.objects.all()
            
            # Get campaigns created by this business
            campaigns = profile.campaigns.all()
            
            # Calculate campaign stats for business dashboard
            campaign_stats = {
                'completion_rate': profile.get_campaign_completion_rate() if hasattr(profile, 'get_campaign_completion_rate') else 0,
                'total_influencers': influencers.count(),
                'active_campaigns': campaigns.filter(status='active').count(),
                'total_campaigns': campaigns.count()
            }
            
            return render(request, 'accounts/business_dashboard.html', {
                'profile': profile,
                'campaign_stats': campaign_stats,
                'influencers': influencers,
                'campaigns': campaigns,
                'unread_messages': get_unread_messages_count(user)
            })
        except BusinessProfile.DoesNotExist:
            messages.warning(request, "Please complete your business profile to access your dashboard.")
            return redirect('business_profile_create')
    
    else:  # Admin
        return render(request, 'accounts/admin_dashboard.html')

def get_unread_messages_count(user):
    """Helper function to get unread messages count"""
    from messaging.models import Message
    return Message.objects.filter(recipient=user, read=False)

class InfluencerProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating influencer profile"""
    model = InfluencerProfile
    template_name = 'accounts/influencer_profile_edit.html'
    fields = ['full_name', 'bio', 'profile_picture', 'phone_number', 'date_of_birth',
              'instagram_handle', 'twitter_handle', 'tiktok_handle', 'youtube_channel',
              'facebook_page', 'categories']
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        return self.request.user.influencer_profile
    
    def form_valid(self, form):
        messages.success(self.request, "Your influencer profile has been updated successfully!")
        return super().form_valid(form)

class BusinessProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating business profile"""
    model = BusinessProfile
    template_name = 'accounts/business_profile_edit.html'
    fields = ['company_name', 'company_logo', 'industry', 'company_size', 'website',
              'description', 'contact_person', 'contact_email', 'contact_phone',
              'address', 'business_type', 'year_established']
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        return self.request.user.business_profile
    
    def form_valid(self, form):
        messages.success(self.request, "Your business profile has been updated successfully!")
        return super().form_valid(form)

class InfluencerProfileDetailView(DetailView):
    """View for displaying an individual influencer's profile"""
    model = InfluencerProfile
    template_name = 'accounts/influencer_profile.html'
    context_object_name = 'profile'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        influencer = self.get_object()
        
        # Calculate total followers across platforms
        total_followers = 0
        if influencer.instagram_followers:
            total_followers += influencer.instagram_followers
        if influencer.twitter_followers:
            total_followers += influencer.twitter_followers
        if influencer.tiktok_followers:
            total_followers += influencer.tiktok_followers
        if influencer.youtube_subscribers:
            total_followers += influencer.youtube_subscribers
        if influencer.facebook_followers:
            total_followers += influencer.facebook_followers
            
        context['total_followers'] = total_followers
        # Split categories string into a list for template usage
        categories_str = influencer.categories if influencer.categories else ''
        context['categories_list'] = [cat.strip() for cat in categories_str.split(',') if cat.strip()]
        
        # Add campaign data for the influencer
        from campaigns.models import Campaign, CampaignApplication
        context['active_campaigns'] = CampaignApplication.objects.filter(
            influencer=influencer, 
            status='approved', 
            campaign__status='active'
        ).select_related('campaign')
        
        context['completed_campaigns'] = CampaignApplication.objects.filter(
            influencer=influencer, 
            status='approved', 
            campaign__status='completed'
        ).select_related('campaign')
        
        # Add social media engagement metrics for charts
        context['engagement_data'] = {
            'labels': ['Instagram', 'Twitter', 'TikTok', 'YouTube', 'Facebook'],
            'followers': [
                influencer.instagram_followers or 0,
                influencer.twitter_followers or 0,
                influencer.tiktok_followers or 0,
                influencer.youtube_subscribers or 0,
                influencer.facebook_followers or 0
            ]
        }
        
        # Check if the current user is the owner of this profile
        # This will be used to determine if edit buttons should be shown
        if self.request.user.is_authenticated and hasattr(self.request.user, 'influencer_profile'):
            context['is_owner'] = (self.request.user.influencer_profile == influencer)
        else:
            context['is_owner'] = False
            
        return context

@login_required
def update_profile_picture(request):
    """View for updating profile picture"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        if request.user.user_type == 'influencer':
            try:
                profile = request.user.influencer_profile
                profile.profile_picture = request.FILES['profile_picture']
                profile.save()
                messages.success(request, "Profile picture updated successfully!")
            except InfluencerProfile.DoesNotExist:
                messages.error(request, "You need to create a profile first.")
                return redirect('influencer_profile_create')
        elif request.user.user_type == 'business':
            try:
                profile = request.user.business_profile
                profile.company_logo = request.FILES['profile_picture']
                profile.save()
                messages.success(request, "Company logo updated successfully!")
            except BusinessProfile.DoesNotExist:
                messages.error(request, "You need to create a business profile first.")
                return redirect('business_profile_create')
    else:
        messages.error(request, "No image file provided.")
    
    # Redirect back to the page they came from, or to dashboard if referrer not available
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('dashboard')

@login_required
def update_bio(request):
    """View for updating bio and categories"""
    if request.method == 'POST':
        bio = request.POST.get('bio', '')
        categories = request.POST.get('categories', '')
        
        if request.user.user_type == 'influencer':
            try:
                profile = request.user.influencer_profile
                profile.bio = bio
                profile.categories = categories
                profile.save()
                messages.success(request, "Profile information updated successfully!")
            except InfluencerProfile.DoesNotExist:
                messages.error(request, "You need to create a profile first.")
                return redirect('influencer_profile_create')
        elif request.user.user_type == 'business':
            try:
                profile = request.user.business_profile
                profile.description = bio
                profile.save()
                messages.success(request, "Business description updated successfully!")
            except BusinessProfile.DoesNotExist:
                messages.error(request, "You need to create a business profile first.")
                return redirect('business_profile_create')
    
    # Redirect back to the page they came from, or to dashboard if referrer not available
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('dashboard')
