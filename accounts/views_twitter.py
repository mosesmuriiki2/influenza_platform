from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import InfluencerProfile
from .models_twitter import TwitterMetrics, TwitterPost
from .twitter_metrics import TwitterMetricsService

import logging
import json

logger = logging.getLogger(__name__)

@login_required
def twitter_metrics_dashboard(request):
    """
    View for displaying Twitter metrics dashboard for influencers.
    """
    # Check if user is an influencer
    if request.user.user_type != 'influencer':
        messages.error(request, "Only influencers can access Twitter metrics dashboard.")
        return redirect('dashboard')
    
    try:
        # Get influencer profile
        profile = request.user.influencer_profile
        
        # Check if profile has Twitter handle
        if not profile.twitter_handle:
            messages.warning(request, "Please add your Twitter handle to view metrics.")
            return redirect('profile_update')
        
        # Get metrics history
        metrics_service = TwitterMetricsService()
        metrics_data = metrics_service.get_metrics_history(profile.id)
        
        # Get recent posts
        recent_posts = metrics_service.get_recent_posts_metrics(profile.id)
        
        # Get latest metrics
        try:
            latest_metrics = TwitterMetrics.objects.filter(influencer=profile).latest('fetched_at')
        except TwitterMetrics.DoesNotExist:
            latest_metrics = None
        
        context = {
            'profile': profile,
            'metrics_data': json.dumps(metrics_data) if metrics_data else None,
            'recent_posts': recent_posts,
            'latest_metrics': latest_metrics,
        }
        
        return render(request, 'accounts/twitter_metrics_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error displaying Twitter metrics dashboard: {str(e)}")
        messages.error(request, "An error occurred while loading Twitter metrics.")
        return redirect('dashboard')

@login_required
@require_GET
def refresh_twitter_metrics(request):
    """
    View for manually refreshing Twitter metrics.
    """
    # Check if user is an influencer
    if request.user.user_type != 'influencer':
        return JsonResponse({'success': False, 'message': "Only influencers can refresh Twitter metrics."})
    
    try:
        # Get influencer profile
        profile = request.user.influencer_profile
        
        # Check if profile has Twitter handle
        if not profile.twitter_handle:
            return JsonResponse({'success': False, 'message': "Please add your Twitter handle to view metrics."})
        
        # Check if metrics were recently updated (within last hour)
        last_update = TwitterMetrics.objects.filter(influencer=profile).order_by('-fetched_at').first()
        if last_update and (timezone.now() - last_update.fetched_at) < timedelta(hours=1):
            return JsonResponse({
                'success': True, 
                'message': "Metrics were recently updated. Please wait before refreshing again.",
                'last_update': last_update.fetched_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Fetch new metrics
        metrics_service = TwitterMetricsService()
        metrics = metrics_service.fetch_user_metrics(profile.twitter_handle)
        
        if metrics:
            return JsonResponse({
                'success': True, 
                'message': "Twitter metrics updated successfully.",
                'followers': metrics.followers_count,
                'engagement_rate': round(metrics.engagement_rate, 2),
                'last_update': metrics.fetched_at.strftime('%Y-%m-%d %H:%M')
            })
        else:
            return JsonResponse({'success': False, 'message': "Failed to update Twitter metrics. Please try again later."})
        
    except Exception as e:
        logger.error(f"Error refreshing Twitter metrics: {str(e)}")
        return JsonResponse({'success': False, 'message': "An error occurred while refreshing Twitter metrics."})

@login_required
@require_GET
def twitter_metrics_api(request):
    """
    API endpoint for getting Twitter metrics data for charts.
    """
    # Check if user is an influencer
    if request.user.user_type != 'influencer':
        return JsonResponse({'success': False, 'message': "Only influencers can access Twitter metrics API."})
    
    try:
        # Get influencer profile
        profile = request.user.influencer_profile
        
        # Get time period from request
        days = int(request.GET.get('days', 30))
        if days not in [7, 30, 90, 180, 365]:
            days = 30
        
        # Get metrics history
        metrics_service = TwitterMetricsService()
        metrics_data = metrics_service.get_metrics_history(profile.id, days=days)
        
        if metrics_data:
            return JsonResponse({'success': True, 'data': metrics_data})
        else:
            return JsonResponse({'success': False, 'message': "No metrics data available for the selected period."})
        
    except Exception as e:
        logger.error(f"Error getting Twitter metrics API data: {str(e)}")
        return JsonResponse({'success': False, 'message': "An error occurred while getting Twitter metrics data."})

@login_required
@require_GET
def twitter_posts_api(request):
    """
    API endpoint for getting Twitter posts data.
    """
    # Check if user is an influencer
    if request.user.user_type != 'influencer':
        return JsonResponse({'success': False, 'message': "Only influencers can access Twitter posts API."})
    
    try:
        # Get influencer profile
        profile = request.user.influencer_profile
        
        # Get limit from request
        limit = int(request.GET.get('limit', 5))
        if limit > 20:
            limit = 20
        
        # Get recent posts
        metrics_service = TwitterMetricsService()
        recent_posts = metrics_service.get_recent_posts_metrics(profile.id, limit=limit)
        
        return JsonResponse({'success': True, 'posts': recent_posts})
        
    except Exception as e:
        logger.error(f"Error getting Twitter posts API data: {str(e)}")
        return JsonResponse({'success': False, 'message': "An error occurred while getting Twitter posts data."})