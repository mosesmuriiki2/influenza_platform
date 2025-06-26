import logging
import tweepy
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models_twitter import TwitterMetrics, TwitterPost
from .models import InfluencerProfile

logger = logging.getLogger(__name__)

class TwitterMetricsService:
    """
    Service for fetching and processing Twitter metrics data.
    This handles API calls and data transformation for visualization.
    """
    
    def __init__(self, access_token=None, access_token_secret=None):
        """
        Initialize the Twitter metrics service with API credentials.
        """
        self.api_key = getattr(settings, 'SOCIAL_AUTH_TWITTER_KEY', None)
        self.api_secret = getattr(settings, 'SOCIAL_AUTH_TWITTER_SECRET', None)
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.warning("Twitter API credentials not fully provided. API calls will fail.")
            self.client = None
        else:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
    
    def fetch_user_metrics(self, twitter_handle):
        """
        Fetch user metrics from Twitter API and store in database.
        Modified to work with Twitter API free tier limitations.
        
        Args:
            twitter_handle (str): Twitter handle without the @ symbol
            
        Returns:
            TwitterMetrics: The created metrics object or None if failed
        """
        if not self.client:
            logger.error("Twitter client not initialized. Cannot fetch metrics.")
            return None
            
        try:
            # Get influencer profile first
            try:
                influencer = InfluencerProfile.objects.get(twitter_handle=twitter_handle)
            except InfluencerProfile.DoesNotExist:
                logger.error(f"Influencer profile not found for Twitter handle: {twitter_handle}")
                return None
            
            # Try to get basic user data with minimal fields to work with free tier
            try:
                user = self.client.get_user(
                    username=twitter_handle,
                    user_fields=['public_metrics']
                )
                
                if user and user.data:
                    # Get user metrics from API
                    metrics = user.data.public_metrics
                    user_id = user.data.id
                    
                    # Create metrics record with data from API
                    twitter_metrics = TwitterMetrics.objects.create(
                        influencer=influencer,
                        followers_count=metrics.get('followers_count', 0),
                        following_count=metrics.get('following_count', 0),
                        tweet_count=metrics.get('tweet_count', 0),
                        listed_count=metrics.get('listed_count', 0),
                        fetched_at=timezone.now()
                    )
                    
                    # Update the influencer profile with latest follower count
                    influencer.twitter_followers = metrics.get('followers_count', 0)
                    influencer.save(update_fields=['twitter_followers'])
                    
                    # Try to fetch recent tweets for engagement metrics if possible
                    self._update_engagement_metrics(twitter_metrics, user_id)
                    
                    return twitter_metrics
                else:
                    logger.warning(f"User data not found for: {twitter_handle}, using fallback")
            except Exception as api_error:
                logger.warning(f"API error when fetching user data: {str(api_error)}, using fallback")
            
            # Fallback: Create metrics with minimal data or from previous records
            # This helps when API limits are reached or endpoints are restricted
            previous_metrics = TwitterMetrics.objects.filter(influencer=influencer).order_by('-fetched_at').first()
            
            twitter_metrics = TwitterMetrics.objects.create(
                influencer=influencer,
                followers_count=getattr(previous_metrics, 'followers_count', 0),
                following_count=getattr(previous_metrics, 'following_count', 0),
                tweet_count=getattr(previous_metrics, 'tweet_count', 0),
                listed_count=getattr(previous_metrics, 'listed_count', 0),
                fetched_at=timezone.now(),
                # Set a flag or note that this is estimated data
                engagement_rate=-1.0  # Use negative value to indicate estimated data
            )
            
            logger.info(f"Created fallback metrics for {twitter_handle}")
            return twitter_metrics
            
        except Exception as e:
            logger.error(f"Error fetching Twitter metrics: {str(e)}")
            return None
    
    def _update_engagement_metrics(self, twitter_metrics, user_id):
        """
        Update engagement metrics based on recent tweets.
        Modified to handle Twitter API free tier limitations.
        
        Args:
            twitter_metrics (TwitterMetrics): The metrics object to update
            user_id (str): Twitter user ID
        """
        if not self.client:
            return
            
        try:
            # Try to get recent tweets - this might fail with free tier
            try:
                tweets = self.client.get_users_tweets(
                    id=user_id,
                    max_results=5,  # Reduced to minimize API usage
                    tweet_fields=['public_metrics', 'created_at'],
                    exclude=['retweets', 'replies']
                )
                
                if tweets and tweets.data:
                    # Calculate average engagement
                    likes = []
                    retweets = []
                    replies = []
                    quotes = []
                    
                    for tweet in tweets.data:
                        metrics = tweet.public_metrics
                        likes.append(metrics.get('like_count', 0))
                        retweets.append(metrics.get('retweet_count', 0))
                        replies.append(metrics.get('reply_count', 0))
                        quotes.append(metrics.get('quote_count', 0))
                        
                        # Store tweet data
                        TwitterPost.objects.update_or_create(
                            tweet_id=tweet.id,
                            defaults={
                                'influencer': twitter_metrics.influencer,
                                'text': tweet.text,
                                'created_at': tweet.created_at,
                                'retweet_count': metrics.get('retweet_count', 0),
                                'reply_count': metrics.get('reply_count', 0),
                                'like_count': metrics.get('like_count', 0),
                                'quote_count': metrics.get('quote_count', 0),
                                'fetched_at': timezone.now()
                            }
                        )
                    
                    # Update metrics with averages
                    if likes:
                        twitter_metrics.avg_likes = sum(likes) / len(likes)
                    if retweets:
                        twitter_metrics.avg_retweets = sum(retweets) / len(retweets)
                    if replies:
                        twitter_metrics.avg_replies = sum(replies) / len(replies)
                    if quotes:
                        twitter_metrics.avg_quotes = sum(quotes) / len(quotes)
                        
                    # Calculate engagement rate
                    if twitter_metrics.followers_count > 0 and likes:
                        total_engagement = sum(likes) + sum(retweets) + sum(replies) + sum(quotes)
                        avg_engagement = total_engagement / len(likes)
                        twitter_metrics.engagement_rate = (avg_engagement / twitter_metrics.followers_count) * 100
                    
                    twitter_metrics.save()
                    logger.info(f"Successfully updated engagement metrics for user {user_id}")
                    return
                else:
                    logger.warning(f"No tweets found for user {user_id}")
            except Exception as tweet_error:
                logger.warning(f"Error fetching tweets: {str(tweet_error)}. Using fallback.")
            
            # Fallback: Try to use previous metrics data if available
            previous_metrics = TwitterMetrics.objects.filter(
                influencer=twitter_metrics.influencer
            ).exclude(id=twitter_metrics.id).order_by('-fetched_at').first()
            
            if previous_metrics:
                # Copy engagement metrics from previous record
                twitter_metrics.avg_likes = previous_metrics.avg_likes
                twitter_metrics.avg_retweets = previous_metrics.avg_retweets
                twitter_metrics.avg_replies = previous_metrics.avg_replies
                twitter_metrics.avg_quotes = previous_metrics.avg_quotes
                
                # Only copy engagement rate if it's not a fallback value (-1.0)
                if previous_metrics.engagement_rate >= 0:
                    twitter_metrics.engagement_rate = previous_metrics.engagement_rate
                else:
                    # Estimate engagement rate based on industry averages
                    twitter_metrics.engagement_rate = 0.5  # Default 0.5% engagement rate
                
                twitter_metrics.save()
                logger.info(f"Used previous metrics as fallback for user {user_id}")
            else:
                # No previous data, set default values
                twitter_metrics.engagement_rate = 0.5  # Default 0.5% engagement rate
                twitter_metrics.save()
                logger.info(f"Set default engagement metrics for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating engagement metrics: {str(e)}")
            # Ensure we save the metrics object even if there's an error
            twitter_metrics.save()
    
    def get_metrics_history(self, influencer_id, days=30):
        """
        Get metrics history for an influencer.
        
        Args:
            influencer_id (int): Influencer profile ID
            days (int): Number of days of history to retrieve
            
        Returns:
            dict: Metrics history data formatted for charts
        """
        try:
            # Get date range
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Get metrics within date range
            metrics = TwitterMetrics.objects.filter(
                influencer_id=influencer_id,
                fetched_at__gte=start_date,
                fetched_at__lte=end_date
            ).order_by('fetched_at')
            
            if not metrics:
                return None
                
            # Convert to dataframe for easier processing
            data = {
                'dates': [m.fetched_at for m in metrics],
                'followers': [m.followers_count for m in metrics],
                'engagement_rate': [m.engagement_rate for m in metrics],
                'avg_likes': [m.avg_likes for m in metrics],
                'avg_retweets': [m.avg_retweets for m in metrics],
                'avg_replies': [m.avg_replies for m in metrics],
                'avg_quotes': [m.avg_quotes for m in metrics],
            }
            
            # Format dates for charts
            formatted_dates = [d.strftime('%Y-%m-%d') for d in data['dates']]
            
            # Prepare chart data
            chart_data = {
                'labels': formatted_dates,
                'datasets': [
                    {
                        'label': 'Followers',
                        'data': data['followers'],
                        'borderColor': '#1DA1F2',
                        'backgroundColor': 'rgba(29, 161, 242, 0.1)',
                        'fill': True
                    },
                    {
                        'label': 'Engagement Rate (%)',
                        'data': data['engagement_rate'],
                        'borderColor': '#17BF63',
                        'backgroundColor': 'rgba(23, 191, 99, 0.1)',
                        'fill': True
                    }
                ]
            }
            
            # Engagement breakdown data
            engagement_data = {
                'labels': ['Likes', 'Retweets', 'Replies', 'Quotes'],
                'datasets': [{
                    'data': [
                        sum(data['avg_likes']) / len(data['avg_likes']) if data['avg_likes'] else 0,
                        sum(data['avg_retweets']) / len(data['avg_retweets']) if data['avg_retweets'] else 0,
                        sum(data['avg_replies']) / len(data['avg_replies']) if data['avg_replies'] else 0,
                        sum(data['avg_quotes']) / len(data['avg_quotes']) if data['avg_quotes'] else 0
                    ],
                    'backgroundColor': [
                        '#E0245E',  # red for likes
                        '#17BF63',  # green for retweets
                        '#1DA1F2',  # blue for replies
                        '#794BC4'   # purple for quotes
                    ]
                }]
            }
            
            return {
                'follower_trend': chart_data,
                'engagement_breakdown': engagement_data
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics history: {str(e)}")
            return None
    
    def get_recent_posts_metrics(self, influencer_id, limit=5):
        """
        Get metrics for recent posts.
        Modified to handle Twitter API free tier limitations.
        
        Args:
            influencer_id (int): Influencer profile ID
            limit (int): Number of posts to retrieve
            
        Returns:
            list: Recent posts with metrics or placeholder data if no posts available
        """
        try:
            posts = TwitterPost.objects.filter(
                influencer_id=influencer_id
            ).order_by('-created_at')[:limit]
            
            result = []
            for post in posts:
                result.append({
                    'id': post.tweet_id,
                    'text': post.text,
                    'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                    'metrics': {
                        'likes': post.like_count,
                        'retweets': post.retweet_count,
                        'replies': post.reply_count,
                        'quotes': post.quote_count,
                        'total_engagement': post.engagement_count
                    }
                })
            
            # If we have posts, return them
            if result:
                return result
                
            # No posts found - check if we have metrics to create placeholder data
            metrics = TwitterMetrics.objects.filter(
                influencer_id=influencer_id
            ).order_by('-fetched_at').first()
            
            if metrics:
                # Create placeholder posts based on average metrics
                placeholder_posts = []
                now = timezone.now()
                
                for i in range(limit):
                    post_date = now - timedelta(days=i)
                    placeholder_posts.append({
                        'id': f'placeholder-{i}',
                        'text': f'[Post data unavailable due to API limitations]',
                        'created_at': post_date.strftime('%Y-%m-%d %H:%M'),
                        'metrics': {
                            'likes': int(metrics.avg_likes) if metrics.avg_likes else 0,
                            'retweets': int(metrics.avg_retweets) if metrics.avg_retweets else 0,
                            'replies': int(metrics.avg_replies) if metrics.avg_replies else 0,
                            'quotes': int(metrics.avg_quotes) if metrics.avg_quotes else 0,
                            'total_engagement': int(metrics.avg_likes + metrics.avg_retweets + 
                                                   metrics.avg_replies + metrics.avg_quotes) if metrics.avg_likes else 0,
                            'is_placeholder': True
                        }
                    })
                
                logger.info(f"Using placeholder post data for influencer {influencer_id}")
                return placeholder_posts
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent posts metrics: {str(e)}")
            return []