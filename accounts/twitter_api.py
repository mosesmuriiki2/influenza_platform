import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class TwitterAPI:
    """
    A utility class for interacting with the X (formerly Twitter) API v2
    to fetch user metrics and other data.
    """
    
    BASE_URL = "https://api.twitter.com/2/"
    
    def __init__(self, bearer_token=None):
        """
        Initialize the TwitterAPI with authentication credentials.
        
        Args:
            bearer_token (str, optional): The bearer token for API authentication.
                If not provided, it will try to use the token from settings.
        """
        self.bearer_token = bearer_token or getattr(settings, 'TWITTER_BEARER_TOKEN', None)
        if not self.bearer_token:
            logger.warning("No Twitter bearer token provided. API calls will fail.")
    
    def _get_headers(self):
        """
        Get the headers required for API requests.
        
        Returns:
            dict: Headers for API requests
        """
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
    
    def get_user_by_username(self, username, fields=None):
        """
        Get user information by username.
        
        Args:
            username (str): The Twitter username (without @)
            fields (list, optional): Additional fields to include in the response
                                    Default includes public_metrics for follower count
        
        Returns:
            dict: User data including metrics if available
        """
        if not self.bearer_token:
            logger.error("Cannot make API request: No bearer token available")
            return None
            
        if fields is None:
            fields = ["public_metrics", "profile_image_url", "description", "created_at"]
            
        params = {"user.fields": ",".join(fields)}
        endpoint = f"users/by/username/{username}"
        
        try:
            response = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Twitter user data: {str(e)}")
            return None
    
    def get_user_metrics(self, username):
        """
        Get user metrics including follower count, tweet count, etc.
        
        Args:
            username (str): The Twitter username (without @)
        
        Returns:
            dict: User metrics or None if request fails
        """
        user_data = self.get_user_by_username(username)
        if user_data and 'data' in user_data and 'public_metrics' in user_data['data']:
            return user_data['data']['public_metrics']
        return None
    
    def get_user_tweets(self, user_id, max_results=10, exclude_replies=True, exclude_retweets=True):
        """
        Get recent tweets for a user.
        Note: This endpoint requires at least Basic tier access.
        
        Args:
            user_id (str): The Twitter user ID
            max_results (int): Maximum number of tweets to return (default 10)
            exclude_replies (bool): Whether to exclude replies (default True)
            exclude_retweets (bool): Whether to exclude retweets (default True)
        
        Returns:
            dict: Tweet data or None if request fails
        """
        if not self.bearer_token:
            logger.error("Cannot make API request: No bearer token available")
            return None
            
        params = {
            "max_results": max_results,
            "tweet.fields": "public_metrics,created_at",
            "expansions": "author_id",
            "user.fields": "public_metrics"
        }
        
        # Add tweet type exclusions if needed
        exclude = []
        if exclude_replies:
            exclude.append("replies")
        if exclude_retweets:
            exclude.append("retweets")
        if exclude:
            params["exclude"] = ",".join(exclude)
        
        endpoint = f"users/{user_id}/tweets"
        
        try:
            response = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Twitter user tweets: {str(e)}")
            return None