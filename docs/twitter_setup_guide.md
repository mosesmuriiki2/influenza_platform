# Twitter Developer Account Setup Guide

This guide will walk you through the process of setting up a Twitter Developer Account and configuring the necessary credentials for the Influenza Platform.

## 1. Create a Twitter Developer Account

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/)
2. Sign in with your Twitter account
3. Apply for a developer account if you don't already have one
4. Follow the application process, explaining that you're building an influencer marketing platform that needs to access Twitter metrics

## 2. Create a Project and App

1. Once approved, create a new Project in the Developer Portal
2. Create a new App within that Project
3. Set the App permissions to "Read" (you only need read access for metrics)
4. Set the App type to "Web App"

## 3. Configure OAuth 2.0 Settings

1. In your App settings, navigate to the "Authentication settings" section
2. Enable OAuth 2.0
3. Add the following Redirect URI:
   ```
   https://influenza-platform.vercel.app/social-auth/complete/twitter-oauth2/
   ```
4. Set the Website URL to your platform's URL:
   ```
   https://influenza-platform.vercel.app/
   ```
5. Save your changes

## 4. Get Your API Credentials

1. In your App settings, navigate to the "Keys and tokens" section
2. Note down the following credentials:
   - API Key (Consumer Key): `T3dueW44Qk9NQWlUUWEyWVJnQWo6MTpjaQ`
   - API Key Secret (Consumer Secret): `ndf4BQHHzljudpZ0uVX-4GZNDb0kL-LqHO6s1ubQv3G49JPIZc`
   - App ID: `31085717`
3. Generate a Bearer Token if needed for additional API access

## 5. Configure Your Django Settings

Add the following settings to your `settings.py` file:

```python
# Twitter OAuth2 Settings
SOCIAL_AUTH_TWITTER_OAUTH2_KEY = 'T3dueW44Qk9NQWlUUWEyWVJnQWo6MTpjaQ'
SOCIAL_AUTH_TWITTER_OAUTH2_SECRET = 'ndf4BQHHzljudpZ0uVX-4GZNDb0kL-LqHO6s1ubQv3G49JPIZc'
# TWITTER_BEARER_TOKEN = 'your_bearer_token'  # Add this if you need to use the Twitter API directly
SOCIAL_AUTH_TWITTER_OAUTH2_SCOPE = ['tweet.read', 'users.read', 'offline.access']
SOCIAL_AUTH_TWITTER_OAUTH2_PROFILE_EXTRA_PARAMS = {
    'include_email': 'true',
    'include_entities': 'false',
    'include_status': 'false'
}
SOCIAL_AUTH_TWITTER_OAUTH2_REDIRECT_URI = 'https://influenza-platform.vercel.app/social-auth/complete/twitter-oauth2/'
```

These credentials are already configured in the project's settings.py file.

## 6. Testing the Integration

1. Deploy your changes to your Vercel environment
2. Visit your login page
3. Click the "Sign in with X (Twitter)" button
4. You should be redirected to Twitter for authentication
5. After successful authentication, you should be redirected back to your platform
6. Check that your Twitter metrics are being displayed correctly in the dashboard

## Troubleshooting

### Common Issues

1. **Redirect URI Mismatch**: Ensure that the Redirect URI in your Twitter Developer Portal exactly matches the one in your Django settings.

2. **API Credentials**: Double-check that you've correctly copied your API Key, API Secret, and Bearer Token.

3. **Rate Limiting**: Twitter API has rate limits. If you're making too many requests, you might get rate-limited. Implement caching to reduce API calls.

4. **Scope Issues**: If you're not getting all the data you need, check that you've included the necessary scopes in your settings.

### Getting Help

If you encounter issues with the Twitter API, consult the following resources:

- [Twitter API Documentation](https://developer.twitter.com/en/docs)
- [Twitter OAuth 2.0 Documentation](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
- [Twitter API Rate Limits](https://developer.twitter.com/en/docs/twitter-api/rate-limits)