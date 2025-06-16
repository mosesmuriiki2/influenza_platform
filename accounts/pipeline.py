from .models import InfluencerProfile
import requests
from django.conf import settings

def set_user_type_influencer(backend, user, response, *args, **kwargs):
    """
    Custom pipeline function to set user type to 'influencer' for social auth users
    and create a basic influencer profile.
    """
    # Only set user type if it's a new user or if user type is not already set
    if user and (user.user_type is None or user.user_type == ''):
        user.user_type = 'influencer'
        user.save()
        
        # Check if user already has an influencer profile
        try:
            profile = user.influencer_profile
        except InfluencerProfile.DoesNotExist:
            # Create a basic profile with information from social auth
            profile = InfluencerProfile(user=user)
            
            # Try to get name from social auth response
            if backend.name == 'facebook':
                if response.get('name'):
                    profile.full_name = response.get('name')
                
                # Store Facebook page information if available
                if response.get('id') and kwargs.get('social') and kwargs['social'].extra_data.get('access_token'):
                    # Store the Facebook user ID
                    profile.facebook_page = response.get('id')
                    
                    # Get Facebook follower count if possible
                    try:
                        access_token = kwargs['social'].extra_data['access_token']
                        fb_api_url = f"https://graph.facebook.com/v18.0/{response.get('id')}?fields=followers_count&access_token={access_token}"
                        fb_response = requests.get(fb_api_url)
                        fb_data = fb_response.json()
                        
                        if 'followers_count' in fb_data:
                            profile.facebook_followers = fb_data['followers_count']
                    except Exception as e:
                        # Just log the error but continue with profile creation
                        print(f"Error fetching Facebook followers: {str(e)}")
            elif backend.name == 'google-oauth2':
                # Get name from Google response
                name_parts = []
                if response.get('given_name'):
                    name_parts.append(response.get('given_name'))
                if response.get('family_name'):
                    name_parts.append(response.get('family_name'))
                if name_parts:
                    profile.full_name = ' '.join(name_parts)
                
                # Get profile picture if available
                if response.get('picture'):
                    # Google returns picture as a URL, we could download it or store the URL
                    # For now, we'll just log that we have a picture URL
                    print(f"Google profile picture URL available: {response.get('picture')}")
            
            # Save the basic profile
            profile.save()
    
    return {'user': user, 'is_new': kwargs.get('is_new', False)}

def store_facebook_token(backend, user, response, *args, **kwargs):
    """
    Store the Facebook access token for later use with the Facebook Graph API.
    This is only called for Facebook authentication.
    """
    if backend.name == 'facebook' and user and kwargs.get('social') and kwargs['social'].extra_data.get('access_token'):
        # Store the token in the session for later use
        if hasattr(backend, 'strategy') and hasattr(backend.strategy, 'request') and backend.strategy.request:
            backend.strategy.request.session['facebook_access_token'] = kwargs['social'].extra_data['access_token']
    
    return None