from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Campaign
from .forms import CampaignForm, CampaignApplicationForm
from django.db.models import Q

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