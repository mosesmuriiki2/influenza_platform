from django.conf import settings
from .models import InfluencerProfile
from .twitter_api import TwitterAPI
from .twitter_metrics import TwitterMetricsService
import logging

logger = logging.getLogger(__name__)

def store_twitter_token(backend, user, response, *args, **kwargs):
    """
    Store the Twitter access token for later use with the Twitter API.
    This is only called for Twitter authentication.
    """
    if backend.name == 'twitter' and user and kwargs.get('social') and kwargs['social'].extra_data.get('access_token'):
        # Store the token in the session for later use
        if hasattr(backend, 'strategy') and hasattr(backend.strategy, 'request') and backend.strategy.request:
            backend.strategy.request.session['twitter_access_token'] = kwargs['social'].extra_data['access_token']
            
            # If we have a token secret, store that too
            if kwargs['social'].extra_data.get('access_token_secret'):
                backend.strategy.request.session['twitter_access_token_secret'] = kwargs['social'].extra_data['access_token_secret']
    
    return None

def fetch_twitter_metrics(backend, user, response, *args, **kwargs):
    """
    Fetch Twitter metrics for the user after successful authentication.
    This will update the user's Twitter metrics in the database.
    """
    if backend.name == 'twitter' and user and user.user_type == 'influencer':
        try:
            # Get the influencer profile
            profile = InfluencerProfile.objects.get(user=user)
            
            # Check if we have a Twitter handle
            if profile.twitter_handle:
                # Initialize the Twitter metrics service
                metrics_service = TwitterMetricsService()
                
                # Fetch and store metrics
                metrics = metrics_service.fetch_user_metrics(profile.twitter_handle)
                
                if metrics:
                    logger.info(f"Successfully fetched Twitter metrics for {profile.twitter_handle}")
                else:
                    logger.warning(f"Failed to fetch Twitter metrics for {profile.twitter_handle}")
            else:
                logger.warning(f"User {user.email} has no Twitter handle set")
                
        except InfluencerProfile.DoesNotExist:
            logger.error(f"Influencer profile not found for user {user.email}")
        except Exception as e:
            logger.error(f"Error fetching Twitter metrics: {str(e)}")
    
    return None