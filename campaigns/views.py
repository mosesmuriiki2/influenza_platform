from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from .models import Campaign, CampaignApplication
from .forms import CampaignForm, CampaignApplicationForm
import json
from datetime import timedelta

@login_required
def campaign_list(request):
    """
    View to display a list of campaigns with filtering based on user type
    """
    if request.user.user_type == 'influencer':
        # For influencers, show active campaigns they haven't applied to
        campaigns = Campaign.objects.filter(
            status='active'
        ).exclude(
            applications__influencer=request.user.influencer_profile
        )
    elif request.user.user_type == 'business':
        # For businesses, show their own campaigns
        campaigns = Campaign.objects.filter(
            business=request.user.business_profile
        )
    else:
        # For admins, show all campaigns
        campaigns = Campaign.objects.all()
    
    return render(request, 'campaigns/campaign_list.html', {'campaigns': campaigns})

@login_required
def filterable_campaign_list(request):
    """
    View to display a filterable list of campaigns for influencers
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "This page is only available to influencers.")
        return redirect('dashboard')
    
    # Get active campaigns that the influencer hasn't applied to
    campaigns = Campaign.objects.filter(
        status='active'
    ).exclude(
        applications__influencer=request.user.influencer_profile
    )
    
    return render(request, 'campaigns/filterable_campaign_list.html', {'campaigns': campaigns})

@login_required
def business_campaign_dashboard(request):
    """
    View for businesses to manage their campaigns with performance metrics
    """
    if request.user.user_type != 'business':
        messages.error(request, "This page is only available to businesses.")
        return redirect('dashboard')
    
    # Get campaigns by status
    active_campaigns = Campaign.objects.filter(
        business=request.user.business_profile,
        status='active'
    )
    completed_campaigns = Campaign.objects.filter(
        business=request.user.business_profile,
        status='completed'
    )
    draft_campaigns = Campaign.objects.filter(
        business=request.user.business_profile,
        status='draft'
    )
    
    # Count metrics
    active_campaigns_count = active_campaigns.count()
    completed_campaigns_count = completed_campaigns.count()
    
    # Count total influencers assigned to campaigns
    total_influencers = CampaignApplication.objects.filter(
        campaign__business=request.user.business_profile,
        status='accepted'
    ).values('influencer').distinct().count()
    
    # Placeholder for total engagement (would be calculated from actual metrics in a real app)
    total_engagement = 10000  # Placeholder value
    
    # Generate sample performance data for charts
    # In a real app, this would come from actual campaign metrics
    performance_data = {
        'labels': json.dumps(["Jan", "Feb", "Mar", "Apr", "May", "Jun"]),
        'engagement': json.dumps([1500, 2500, 3200, 4100, 3800, 5000]),
        'reach': json.dumps([5000, 7500, 10000, 12500, 11000, 15000]),
        'conversions': json.dumps([120, 180, 240, 280, 260, 350])
    }
    
    # Platform engagement distribution
    platform_data = {
        'labels': json.dumps(["Instagram", "TikTok", "Twitter", "Facebook", "YouTube"]),
        'values': json.dumps([45, 25, 10, 15, 5])
    }
    
    context = {
        'active_campaigns': active_campaigns,
        'completed_campaigns': completed_campaigns,
        'draft_campaigns': draft_campaigns,
        'active_campaigns_count': active_campaigns_count,
        'completed_campaigns_count': completed_campaigns_count,
        'total_influencers': total_influencers,
        'total_engagement': total_engagement,
        'performance_data': performance_data,
        'platform_data': platform_data
    }
    
    return render(request, 'campaigns/business_campaign_dashboard.html', context)

@login_required
def update_campaign_status(request, campaign_id):
    """
    View to update campaign status (complete, reopen, activate)
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [status[0] for status in Campaign.STATUS_CHOICES]:
            campaign.status = new_status
            
            # If reopening a campaign, update the end date
            if new_status == 'active' and campaign.status == 'completed':
                new_end_date = request.POST.get('end_date')
                if new_end_date:
                    campaign.end_date = new_end_date
                else:
                    # Default to 30 days from now if no date provided
                    campaign.end_date = timezone.now().date() + timedelta(days=30)
            
            campaign.save()
            messages.success(request, f"Campaign status updated to {campaign.get_status_display()}.")
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('business_campaign_dashboard')

@login_required
def campaign_detail(request, campaign_id):
    """
    View to display detailed information about a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Check if current user has applied to this campaign
    has_applied = False
    if request.user.user_type == 'influencer':
        has_applied = campaign.applications.filter(influencer=request.user.influencer_profile).exists()
    
    context = {
        'campaign': campaign,
        'has_applied': has_applied,
    }
    
    return render(request, 'campaigns/campaign_detail.html', context)

@login_required
def create_campaign(request):
    """
    View for business users to create new campaigns
    """
    if request.user.user_type != 'business':
        messages.error(request, "Only business accounts can create campaigns.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.business = request.user.business_profile
            campaign.save()
            messages.success(request, "Campaign created successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm()
    
    return render(request, 'campaigns/campaign_create.html', {'form': form})

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm(instance=campaign)
    
    return render(request, 'campaigns/campaign_edit.html', {'form': form, 'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """
    View for influencers to apply to campaigns
    """
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can apply to campaigns.")
        return redirect('campaign_list')
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if campaign.status != 'active':
        messages.error(request, "This campaign is not currently accepting applications.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if campaign.applications.filter(influencer=request.user.influencer_profile).exists():
        messages.error(request, "You have already applied to this campaign.")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    if request.method == 'POST':
        form = CampaignApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.campaign = campaign
            application.influencer = request.user.influencer_profile
            application.save()
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('campaign_detail', campaign_id=campaign_id)
    else:
        form = CampaignApplicationForm()
    
    return render(request, 'campaigns/campaign_apply.html', {
        'form': form,
        'campaign': campaign
    })

@login_required
def campaign_applications(request, campaign_id):
    """
    View to display all applications for a specific campaign
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to view these applications.")
        return redirect('campaign_list')
    
    applications = campaign.applications.all()
    
    return render(request, 'campaigns/campaign_applications.html', {
        'campaign': campaign,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    """
    View for businesses to accept or reject influencer applications
    """
    application = get_object_or_404(CampaignApplication, id=application_id)
    
    # Check if user is the campaign owner
    if request.user.user_type != 'business' or application.campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to update this application.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            status_display = "accepted" if new_status == "accepted" else "rejected"
            messages.success(request, f"Application {status_display} successfully.")
            
            # Send notification to the influencer (in a real app, this would be more robust)
            # This is handled by the post_save signal in models.py
        else:
            messages.error(request, "Invalid status provided.")
    
    return redirect('campaign_applications', campaign_id=application.campaign.id)

@login_required
def send_campaign_message(request, campaign_id, recipient_id):
    """
    View for sending messages related to a campaign
    """
    from accounts.models import User
    from messaging.models import Message as MessagingMessage
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipient = get_object_or_404(User, id=recipient_id)
    
    # Check permissions
    if request.user.user_type == 'business' and campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to send messages for this campaign.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create message in the messaging app
            message = MessagingMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                related_campaign=campaign
            )
            messages.success(request, "Message sent successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")
    
    # Redirect back to the appropriate page
    if request.user.user_type == 'business':
        return redirect('campaign_applications', campaign_id=campaign_id)
    else:  # influencer
        return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def edit_campaign(request, campaign_id):
    """
    View for business users to edit their existing campaigns
    """
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    if request.user.user_type != 'business' or campaign.business != request.user.business_profile:
        messages.error(request, "You don't have permission to edit this campaign.")
        return redirect('campaign_list')
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success