from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, InfluencerProfile, BusinessProfile, Campaign, CampaignApplication, CampaignMetrics, Payment

class UserAdmin(BaseUserAdmin):
    """Custom User Admin that uses email as the unique identifier"""
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    list_filter = ['user_type', 'is_staff', 'is_active']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )

class InfluencerProfileAdmin(admin.ModelAdmin):
    """Admin for Influencer Profiles"""
    list_display = ['user', 'full_name', 'instagram_followers', 'twitter_followers', 'created_at']
    search_fields = ['user__email', 'full_name', 'instagram_handle', 'twitter_handle']
    list_filter = ['created_at']

class BusinessProfileAdmin(admin.ModelAdmin):
    """Admin for Business Profiles"""
    list_display = ['user', 'company_name', 'industry', 'contact_person', 'created_at']
    search_fields = ['user__email', 'company_name', 'contact_person', 'industry']
    list_filter = ['created_at', 'industry']

class CampaignAdmin(admin.ModelAdmin):
    """Admin for Campaigns"""
    list_display = ['title', 'business', 'budget', 'start_date', 'end_date', 'status']
    search_fields = ['title', 'business__company_name', 'description']
    list_filter = ['status', 'start_date', 'end_date']

class CampaignApplicationAdmin(admin.ModelAdmin):
    """Admin for Campaign Applications"""
    list_display = ['campaign', 'influencer', 'proposed_fee', 'status', 'created_at']
    search_fields = ['campaign__title', 'influencer__full_name']
    list_filter = ['status', 'created_at']

class CampaignMetricsAdmin(admin.ModelAdmin):
    """Admin for Campaign Metrics"""
    list_display = ['campaign', 'influencer', 'platform', 'impressions', 'likes', 'comments', 'shares']
    search_fields = ['campaign__title', 'influencer__full_name', 'platform']
    list_filter = ['platform', 'post_date']

class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payments"""
    list_display = ['campaign', 'influencer', 'amount', 'status', 'payment_date']
    search_fields = ['campaign__title', 'influencer__full_name', 'transaction_id']
    list_filter = ['status', 'payment_date', 'payment_method']

# Register models
admin.site.register(User, UserAdmin)
admin.site.register(InfluencerProfile, InfluencerProfileAdmin)
admin.site.register(BusinessProfile, BusinessProfileAdmin)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(CampaignApplication, CampaignApplicationAdmin)
admin.site.register(CampaignMetrics, CampaignMetricsAdmin)
admin.site.register(Payment, PaymentAdmin)
