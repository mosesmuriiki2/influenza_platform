from .models import InfluencerProfile

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
            elif backend.name == 'google-oauth2':
                name_parts = []
                if response.get('given_name'):
                    name_parts.append(response.get('given_name'))
                if response.get('family_name'):
                    name_parts.append(response.get('family_name'))
                if name_parts:
                    profile.full_name = ' '.join(name_parts)
            
            # Save the basic profile
            profile.save()
    
    return {'user': user, 'is_new': kwargs.get('is_new', False)}