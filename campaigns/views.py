from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.forms import modelformset_factory
from .models import Campaign, CampaignImage, CampaignApplication, Message
from accounts.models import BusinessProfile, InfluencerProfile

@login_required
def campaign_list(request):
    """View to display all available campaigns"""
    campaigns = Campaign.objects.filter(status='active')
    return render(request, 'campaigns/campaign_list.html', {'campaigns': campaigns})

@login_required
def campaign_detail(request, campaign_id):
    """View to display campaign details"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    return render(request, 'campaigns/campaign_detail.html', {'campaign': campaign})

@login_required
def create_campaign(request):
    """View for businesses to create a new campaign with multiple images"""
    if request.user.user_type != 'business':
        return HttpResponseForbidden("Only business accounts can create campaigns")
    
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, "Please complete your business profile first")
        return redirect('business_profile_create')
    
    ImageFormSet = modelformset_factory(CampaignImage, fields=('image', 'caption'), extra=3)
    
    if request.method == 'POST':
        # Process campaign data
        campaign = Campaign.objects.create(
            business=business_profile,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            requirements=request.POST.get('requirements'),
            budget=request.POST.get('budget'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            status=request.POST.get('status'),
            target_audience=request.POST.get('target_audience')
        )
        
        # Process image formset
        formset = ImageFormSet(request.POST, request.FILES)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    image = form.save()
                    campaign.campaign_images.add(image)
        
        messages.success(request, "Campaign created successfully")
        return redirect('campaign_detail', campaign_id=campaign.id)
    
    formset = ImageFormSet(queryset=CampaignImage.objects.none())
    return render(request, 'campaigns/campaign_create.html', {'formset': formset})

@login_required
def edit_campaign(request, campaign_id):
    """View for businesses to edit their campaigns"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Check if user is the owner of the campaign
    if campaign.business.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this campaign")
    
    if request.method == 'POST':
        # Process form data
        campaign.title = request.POST.get('title')
        campaign.description = request.POST.get('description')
        campaign.requirements = request.POST.get('requirements')
        campaign.budget = request.POST.get('budget')
        campaign.start_date = request.POST.get('start_date')
        campaign.end_date = request.POST.get('end_date')
        campaign.status = request.POST.get('status')
        campaign.target_platforms = request.POST.get('target_platforms')
        campaign.target_audience = request.POST.get('target_audience')
        campaign.target_metrics = request.POST.get('target_metrics')
        campaign.save()
        
        messages.success(request, "Campaign updated successfully")
        return redirect('campaign_detail', campaign_id=campaign.id)
    
    return render(request, 'campaigns/campaign_edit.html', {'campaign': campaign})

@login_required
def apply_campaign(request, campaign_id):
    """View for influencers to apply for campaigns"""
    if request.user.user_type != 'influencer':
        return HttpResponseForbidden("Only influencers can apply for campaigns")
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    influencer = request.user.influencer_profile
    
    if request.method == 'POST':
        message = request.POST.get('message')
        application = CampaignApplication.objects.create(
            campaign=campaign,
            influencer=influencer,
            message=message
        )
        messages.success(request, "Application submitted successfully")
        return redirect('campaign_detail', campaign_id=campaign_id)
    
    return render(request, 'campaigns/apply_campaign.html', {'campaign': campaign})

@login_required
def send_message(request, campaign_id):
    """View for sending messages between businesses and influencers"""
    if request.method == 'POST':
        campaign = get_object_or_404(Campaign, id=campaign_id)
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')
        
        receiver = get_object_or_404(User, id=receiver_id)
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            campaign=campaign,
            content=content
        )
        
        return JsonResponse({'status': 'success', 'message': 'Message sent successfully'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def message_list(request, campaign_id):
    """View to display messages for a specific campaign"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    messages = Message.objects.filter(campaign=campaign).order_by('created_at')
    return render(request, 'campaigns/message_list.html', {'messages': messages, 'campaign': campaign})
    """View for influencers to apply to campaigns"""
    # This is a placeholder for future implementation
    messages.info(request, "Application functionality will be implemented soon")
    return redirect('campaign_detail', campaign_id=campaign_id)

@login_required
def campaign_applications(request, campaign_id):
    """View for businesses to see applications for their campaigns"""
    # This is a placeholder for future implementation
    messages.info(request, "Applications view will be implemented soon")
    return redirect('campaign_detail', campaign_id=campaign_id)