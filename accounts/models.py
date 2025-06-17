from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model with email as the unique identifier"""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_type_choices = [
        ('admin', 'Admin'),
        ('influencer', 'Influencer'),
        ('business', 'Business'),
    ]
    user_type = models.CharField(max_length=10, choices=user_type_choices, default='influencer')
    
    # Fields for tracking privacy policy and terms acceptance
    privacy_policy_accepted = models.BooleanField(default=False)
    terms_conditions_accepted = models.BooleanField(default=False)
    privacy_policy_accepted_date = models.DateTimeField(null=True, blank=True)
    terms_conditions_accepted_date = models.DateTimeField(null=True, blank=True)
    
    # Fields for email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_token_created = models.DateTimeField(null=True, blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email

class InfluencerProfile(models.Model):
    """Profile for influencers with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='influencer_profile')
    full_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Social media accounts
    instagram_handle = models.CharField(max_length=50, blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    tiktok_handle = models.CharField(max_length=50, blank=True)
    youtube_channel = models.CharField(max_length=100, blank=True)
    
    # Facebook specific fields
    facebook_page = models.CharField(max_length=100, blank=True, help_text='Facebook page ID')
    facebook_page_name = models.CharField(max_length=100, blank=True, help_text='Facebook page name')
    facebook_page_category = models.CharField(max_length=100, blank=True, help_text='Facebook page category')
    facebook_url = models.URLField(blank=True, help_text='Facebook profile or page URL')
    profile_picture_url = models.URLField(blank=True, help_text='URL to profile picture from social media')
    
    # Metrics
    instagram_followers = models.PositiveIntegerField(default=0)
    twitter_followers = models.PositiveIntegerField(default=0)
    tiktok_followers = models.PositiveIntegerField(default=0)
    youtube_subscribers = models.PositiveIntegerField(default=0)
    facebook_followers = models.PositiveIntegerField(default=0)
    
    # Categories and interests
    categories = models.CharField(max_length=255, blank=True, help_text='Comma separated categories')
    
    # Payment information
    payment_email = models.EmailField(blank=True)
    bank_account_info = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"

class BusinessProfile(models.Model):
    """Profile for businesses with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    company_name = models.CharField(max_length=100)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    
    # Contact information
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    # Business details
    business_type = models.CharField(max_length=50, blank=True, help_text='e.g., Private, Public, Non-profit')
    year_established = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.company_name

class Campaign(models.Model):
    """Marketing campaigns created by businesses"""
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='account_campaigns')
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    image = models.ImageField(upload_to='campaign_images/', blank=True, null=True)
    
    # Campaign status
    status_choices = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='draft')
    
    # Target audience and metrics
    target_platforms = models.CharField(max_length=255, help_text='Comma separated platforms')
    target_audience = models.TextField(blank=True)
    target_metrics = models.TextField(blank=True, help_text='Expected engagement metrics')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class CampaignApplication(models.Model):
    """Applications from influencers to participate in campaigns"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='applications')
    influencer = models.ForeignKey(InfluencerProfile, on_delete=models.CASCADE, related_name='account_applications')
    proposal = models.TextField()
    proposed_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    status_choices = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('campaign', 'influencer')
    
    def __str__(self):
        return f"{self.influencer} - {self.campaign}"

class CampaignMetrics(models.Model):
    """Metrics for campaign performance tracking"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='metrics')
    influencer = models.ForeignKey(InfluencerProfile, on_delete=models.CASCADE, related_name='campaign_metrics')
    
    # Post information
    post_url = models.URLField()
    post_date = models.DateTimeField()
    platform = models.CharField(max_length=50)
    
    # Engagement metrics
    impressions = models.PositiveIntegerField(default=0)
    reach = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.campaign} - {self.influencer} - {self.platform}"

class Payment(models.Model):
    """Payments made to influencers for campaigns"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='payments')
    influencer = models.ForeignKey(InfluencerProfile, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status_choices = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='pending')
    
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment of {self.amount} to {self.influencer}"
