from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from accounts.models import User, InfluencerProfile, BusinessProfile

class Campaign(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='campaigns')
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    requirements = models.TextField(blank=True, null=True)
    target_audience = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    campaign_images = models.ManyToManyField('CampaignImage', related_name='campaigns', blank=True)
    
    def __str__(self):
        return self.title

class CampaignImage(models.Model):
    image = models.ImageField(upload_to='campaign_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Image for {self.campaigns.first().title if self.campaigns.exists() else "No Campaign"}'

class CampaignApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='applications')
    influencer = models.ForeignKey(InfluencerProfile, on_delete=models.CASCADE, related_name='campaign_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['campaign', 'influencer']

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns_sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns_received_messages')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

@receiver(post_save, sender=CampaignApplication)
def notify_application_status_change(sender, instance, created, **kwargs):
    if created:
        # Notify business about new application
        send_mail(
            'New Campaign Application',
            f'New application received for campaign: {instance.campaign.title}',
            'noreply@influenza.com',
            [instance.campaign.business.user.email],
            fail_silently=True,
        )
    else:
        # Notify influencer about application status change
        send_mail(
            'Campaign Application Status Update',
            f'Your application for {instance.campaign.title} has been {instance.status}',
            'noreply@influenza.com',
            [instance.influencer.user.email],
            fail_silently=True,
        )

@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    if created:
        send_mail(
            'New Message Received',
            f'You have received a new message regarding campaign: {instance.campaign.title if instance.campaign else "General Message"}',
            'noreply@influenza.com',
            [instance.receiver.email],
            fail_silently=True,
        )