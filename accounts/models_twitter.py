from django.db import models
from django.utils import timezone
from .models import InfluencerProfile

class TwitterMetrics(models.Model):
    """
    Model to store Twitter metrics for influencers over time.
    This allows tracking changes in metrics and displaying trends.
    """
    influencer = models.ForeignKey(InfluencerProfile, on_delete=models.CASCADE, related_name='twitter_metrics')
    
    # Basic metrics
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    tweet_count = models.PositiveIntegerField(default=0)
    listed_count = models.PositiveIntegerField(default=0)
    
    # Engagement metrics (calculated from recent tweets)
    avg_likes = models.FloatField(default=0.0)
    avg_retweets = models.FloatField(default=0.0)
    avg_replies = models.FloatField(default=0.0)
    avg_quotes = models.FloatField(default=0.0)
    engagement_rate = models.FloatField(default=0.0, help_text="Average engagement rate as percentage")
    
    # Metadata
    fetched_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-fetched_at']
        verbose_name = "Twitter Metrics"
        verbose_name_plural = "Twitter Metrics"
    
    def __str__(self):
        return f"{self.influencer} - {self.fetched_at.strftime('%Y-%m-%d %H:%M')}"

class TwitterPost(models.Model):
    """
    Model to store individual Twitter posts and their metrics.
    This allows for detailed analysis of post performance.
    """
    influencer = models.ForeignKey(InfluencerProfile, on_delete=models.CASCADE, related_name='twitter_posts')
    
    # Post data
    tweet_id = models.CharField(max_length=50, unique=True)
    text = models.TextField()
    created_at = models.DateTimeField()
    
    # Metrics
    retweet_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    quote_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    fetched_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Twitter Post"
        verbose_name_plural = "Twitter Posts"
    
    def __str__(self):
        return f"{self.tweet_id} - {self.text[:50]}"
    
    @property
    def engagement_count(self):
        """Calculate total engagement count"""
        return self.retweet_count + self.reply_count + self.like_count + self.quote_count