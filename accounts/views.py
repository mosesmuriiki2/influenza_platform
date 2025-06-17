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

def privacy_policy(request):
    """View for privacy policy page"""
    return render(request, 'accounts/privacy_policy.html')

def terms_conditions(request):
    """View for terms and conditions page"""
    return render(request, 'accounts/terms_conditions.html')

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
    success_url = reverse_lazy('verify_otp')
    
    def form_valid(self, form):
        # Check if passwords match
        password = form.cleaned_data['password']
        confirm_password = self.request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(self.request, "Passwords do not match.")
            return self.form_invalid(form)
            
        # Check if email already exists
        email = form.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            messages.error(self.request, "A user with that email already exists.")
            return self.form_invalid(form)
        
        # Check if privacy policy and terms are accepted
        privacy_policy_accepted = self.request.POST.get('privacy_policy_accepted')
        terms_conditions_accepted = self.request.POST.get('terms_conditions_accepted')
        
        if not privacy_policy_accepted:
            messages.error(self.request, "You must accept the Privacy Policy to register.")
            return self.form_invalid(form)
            
        if not terms_conditions_accepted:
            messages.error(self.request, "You must accept the Terms and Conditions to register.")
            return self.form_invalid(form)
            
        # Set user type to influencer
        user = form.save(commit=False)
        user.user_type = 'influencer'
        user.set_password(password)
        
        # Record privacy policy and terms acceptance
        from django.utils import timezone
        user.privacy_policy_accepted = True
        user.terms_conditions_accepted = True
        user.privacy_policy_accepted_date = timezone.now()
        user.terms_conditions_accepted_date = timezone.now()
        
        # Generate OTP for email verification
        import random
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        user.otp = otp
        user.otp_created = timezone.now()
        
        user.save()
        
        # Send verification email with OTP
        self.send_verification_email(user, otp)
        
        # Store user ID in session for OTP verification
        self.request.session['user_id_for_verification'] = user.id
        
        messages.success(self.request, "Registration successful! Please check your email for the verification code.")
        return super().form_valid(form)
        
    def send_verification_email(self, user, otp):
        """Send verification email with OTP"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from django.conf import settings
        
        subject = 'Verify Your Influenza Platform Account'
        html_message = render_to_string('accounts/email/verification_email.html', {
            'user': user,
            'otp': otp,
        })
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email
        
        try:
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        except Exception as e:
            print(f"Error sending email: {e}")
            # Log the error in production

class BusinessRegistrationView(CreateView):
    """View for business registration"""
    model = User
    template_name = 'accounts/business_register.html'
    fields = ['email', 'first_name', 'last_name', 'password']
    success_url = reverse_lazy('verify_otp')
    
    def form_valid(self, form):
        # Check if passwords match
        password = form.cleaned_data['password']
        confirm_password = self.request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(self.request, "Passwords do not match.")
            return self.form_invalid(form)
            
        # Check if email already exists
        email = form.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            messages.error(self.request, "A user with that email already exists.")
            return self.form_invalid(form)
        
        # Check if privacy policy and terms are accepted
        privacy_policy_accepted = self.request.POST.get('privacy_policy_accepted')
        terms_conditions_accepted = self.request.POST.get('terms_conditions_accepted')
        
        if not privacy_policy_accepted:
            messages.error(self.request, "You must accept the Privacy Policy to register.")
            return self.form_invalid(form)
            
        if not terms_conditions_accepted:
            messages.error(self.request, "You must accept the Terms and Conditions to register.")
            return self.form_invalid(form)
            
        # Set user type to business
        user = form.save(commit=False)
        user.user_type = 'business'
        user.set_password(password)
        
        # Record privacy policy and terms acceptance
        from django.utils import timezone
        user.privacy_policy_accepted = True
        user.terms_conditions_accepted = True
        user.privacy_policy_accepted_date = timezone.now()
        user.terms_conditions_accepted_date = timezone.now()
        
        # Generate OTP for email verification
        import random
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        user.otp = otp
        user.otp_created = timezone.now()
        
        user.save()
        
        # Send verification email with OTP
        self.send_verification_email(user, otp)
        
        # Store user ID in session for OTP verification
        self.request.session['user_id_for_verification'] = user.id
        
        messages.success(self.request, "Registration successful! Please check your email for the verification code.")
        return super().form_valid(form)
        
    def send_verification_email(self, user, otp):
        """Send verification email with OTP"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from django.conf import settings
        
        subject = 'Verify Your Influenza Platform Account'
        html_message = render_to_string('accounts/email/verification_email.html', {
            'user': user,
            'otp': otp,
        })
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email
        
        try:
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        except Exception as e:
            print(f"Error sending email: {e}")
            # Log the error in production

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

def verify_otp(request):
    """View for OTP verification"""
    # Check if user_id is in session
    user_id = request.session.get('user_id_for_verification')
    if not user_id:
        messages.error(request, "Verification session expired. Please register again.")
        return redirect('register_choice')
    
    # Get the user
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please register again.")
        return redirect('register_choice')
    
    # Check if already verified
    if user.email_verified:
        messages.success(request, "Your email is already verified. Please log in.")
        return redirect('login')
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        
        # Validate OTP
        if not otp_entered:
            messages.error(request, "Please enter the verification code.")
            return render(request, 'accounts/verify_otp.html')
        
        # Check if OTP matches
        if user.otp != otp_entered:
            messages.error(request, "Invalid verification code. Please try again.")
            return render(request, 'accounts/verify_otp.html')
        
        # Check if OTP is expired (30 minutes)
        import datetime
        from django.utils import timezone
        
        if user.otp_created and (timezone.now() - user.otp_created).total_seconds() > 1800:
            # Generate new OTP
            import random
            new_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            user.otp = new_otp
            user.otp_created = timezone.now()
            user.save()
            
            # Send new verification email
            send_verification_email(user, new_otp)
            
            messages.error(request, "Verification code expired. A new code has been sent to your email.")
            return render(request, 'accounts/verify_otp.html')
        
        # Mark email as verified
        user.email_verified = True
        user.email_verification_token = None
        user.otp = None
        user.save()
        
        # Log the user in
        user.backend = 'django.contrib.auth.backends.ModelBackend'  # ✅ Add this
        login(request, user)
        
        # Clear session
        if 'user_id_for_verification' in request.session:
            del request.session['user_id_for_verification']
        
        messages.success(request, "Email verified successfully!")
        
        # Redirect based on user type
        if user.user_type == 'influencer':
            return redirect('influencer_profile_create')
        else:  # business
            return redirect('business_profile_create')
    
    return render(request, 'accounts/verify_otp.html')

def resend_otp(request):
    """View for resending OTP"""
    # Check if user_id is in session
    user_id = request.session.get('user_id_for_verification')
    if not user_id:
        messages.error(request, "Verification session expired. Please register again.")
        return redirect('register_choice')
    
    # Get the user
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please register again.")
        return redirect('register_choice')
    
    # Generate new OTP
    import random
    from django.utils import timezone
    new_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    user.otp = new_otp
    user.otp_created = timezone.now()
    user.save()
    
    # Send new verification email
    send_verification_email(user, new_otp)
    
    messages.success(request, "A new verification code has been sent to your email.")
    return redirect('verify_otp')

def send_verification_email(user, otp):
    """Helper function to send verification email with OTP"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    import logging
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    subject = 'Verify Your Influenza Platform Account'
    html_message = render_to_string('accounts/email/verification_email.html', {
        'user': user,
        'otp': otp,
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    
    # Log the OTP for debugging purposes
    logger.info(f"Sending OTP to {user.email}: {otp}")
    print(f"OTP for {user.email}: {otp}")
    
    try:
        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        logger.info(f"Email with OTP sent successfully to {user.email}")
    except Exception as e:
        error_message = f"Error sending email: {e}"
        logger.error(error_message)
        print(error_message)
        # Log the error in production
