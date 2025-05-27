# ====================
# File: docs/twitter_api_usage.md (Usage Documentation)
# ====================

# Twitter API Module Usage Guide

## Overview

The TwitterAPIModule provides a comprehensive interface to Twitter API v2 with built-in rate limiting, error handling, and authentication management.

## Quick Start

### 1. Configuration

Set up environment variables:

```bash
export TWITTER_CLIENT_ID="your_client_id"
export TWITTER_CLIENT_SECRET="your_client_secret"
export TWITTER_REDIRECT_URI="http://localhost:8000/auth/twitter/callback"
```

### 2. Basic Usage

```python
from modules.twitter_api import TwitterAPIClient

# Initialize client
client = TwitterAPIClient(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Create a tweet
result = client.create_tweet(
    user_token="user_access_token",
    text="Hello, Twitter! 🐦"
)

# Search tweets
tweets = client.search_tweets(
    user_token="user_access_token",
    query="python programming",
    max_results=50
)

# Get trending topics
trends = client.get_trends_for_location(
    user_token="user_access_token",
    location_id="1"  # Global trends
)
```

## API Reference

### Tweet Operations

#### Create Tweet
```python
client.create_tweet(
    user_token="access_token",
    text="Tweet content",
    reply_settings="everyone",  # 'everyone', 'mentionedUsers', 'followers'
    in_reply_to_tweet_id="123456789",  # Optional: reply to tweet
    quote_tweet_id="987654321",  # Optional: quote tweet
    media_ids=["media_123", "media_456"],  # Optional: attach media
    poll_options=["Option 1", "Option 2"],  # Optional: create poll
    poll_duration_minutes=1440  # Optional: poll duration (24 hours)
)
```

#### Search Tweets
```python
client.search_tweets(
    user_token="access_token",
    query="(python OR javascript) -RT",  # Search query with operators
    max_results=100,  # 10-100 results
    start_time="2024-01-01T00:00:00Z",  # ISO 8601 format
    end_time="2024-01-31T23:59:59Z",
    tweet_fields=["created_at", "public_metrics", "context_annotations"],
    user_fields=["verified", "public_metrics"],
    expansions=["author_id", "referenced_tweets.id"]
)
```

### Retweet Operations

#### Create Retweet
```python
# Get user's Twitter ID first
user_info = client.get_me(user_token)
twitter_user_id = user_info['data']['id']

# Create retweet
client.create_retweet(
    user_token="access_token",
    authenticating_user_id=twitter_user_id,
    target_tweet_id="123456789"
)
```

### User Operations

#### Get Current User
```python
user_info = client.get_me(user_token="access_token")
print(f"Username: {user_info['data']['username']}")
print(f"Followers: {user_info['data']['public_metrics']['followers_count']}")
```

### Trends Operations

#### Get Trending Topics
```python
# Global trends
global_trends = client.get_trends_for_location(
    user_token="access_token",
    location_id="1"
)

# US trends
us_trends = client.get_trends_for_location(
    user_token="access_token", 
    location_id="23424977"
)

for trend in global_trends:
    print(f"Trend: {trend['name']}")
    print(f"Volume: {trend.get('tweet_volume', 'N/A')}")
```

## Advanced Features

### Rate Limiting

The module automatically handles rate limiting:

```python
# Check rate limit status
status = client.get_rate_limit_status()
print(status)

# The client automatically waits when rate limits are reached
# No manual handling required
```

### Error Handling

```python
from modules.twitter_api import (
    TwitterAPIError, RateLimitError, AuthenticationError
)

try:
    result = client.create_tweet(user_token, "Hello World!")
except AuthenticationError:
    print("Invalid access token")
except RateLimitError as e:
    print(f"Rate limit exceeded. Reset in {e.reset_time} seconds")
except TwitterAPIError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

### Search Query Operators

Build powerful search queries using Twitter operators:

```python
# Examples of search queries
queries = [
    # Basic text search
    "machine learning",
    
    # Hashtag search
    "#python #datascience",
    
    # From specific user
    "from:twitter",
    
    # Exclude retweets
    "python -is:retweet",
    
    # Only verified users
    "AI is:verified",
    
    # Minimum engagement
    "startup min_faves:100",
    
    # Language specific
    "bonjour lang:fr",
    
    # Complex query
    "(python OR javascript) #programming -is:retweet min_faves:10"
]

for query in queries:
    results = client.search_tweets(user_token, query, max_results=20)
```

### Field Selection

Optimize API responses by selecting specific fields:

```python
# Minimal tweet data
basic_tweets = client.search_tweets(
    user_token="access_token",
    query="python",
    tweet_fields=["id", "text"],
    user_fields=["username"],
    expansions=["author_id"]
)

# Rich tweet data
detailed_tweets = client.search_tweets(
    user_token="access_token",
    query="python",
    tweet_fields=[
        "id", "text", "created_at", "public_metrics",
        "context_annotations", "lang", "reply_settings"
    ],
    user_fields=[
        "id", "username", "name", "verified", "description",
        "public_metrics", "location"
    ],
    expansions=[
        "author_id", "referenced_tweets.id", 
        "referenced_tweets.id.author_id"
    ]
)
```

## Best Practices

### 1. Authentication Management
- Always validate tokens before making requests
- Implement token refresh logic for long-running applications
- Store tokens securely (encrypted)

### 2. Rate Limiting
- Monitor rate limit status regularly
- Implement exponential backoff for retries
- Use appropriate request frequencies for your use case

### 3. Error Handling
- Always wrap API calls in try-catch blocks
- Log errors for debugging
- Implement fallback strategies

### 4. Query Optimization
- Use specific search operators to reduce noise
- Request only needed fields to reduce bandwidth
- Implement pagination for large result sets

### 5. Performance
- Reuse client instances
- Implement connection pooling for high-volume applications
- Cache frequently accessed data

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   AuthenticationError: Invalid or expired token
   ```
   - Solution: Refresh the user's access token

2. **Rate Limit Errors**
   ```
   RateLimitError: Rate limit exceeded
   ```
   - Solution: Wait for rate limit reset or implement request queuing

3. **Invalid Query Errors**
   ```
   TwitterAPIBadRequestError: Invalid search query
   ```
   - Solution: Check query syntax and operators

4. **Network Timeouts**
   ```
   TwitterAPIError: Network error: timeout
   ```
   - Solution: Increase timeout values or implement retry logic

### Health Check

Run the health check script to verify configuration:

```bash
python scripts/twitter_health_check.py
```

This will validate:
- Configuration settings
- API connectivity
- Rate limiting functionality
- Endpoint configurations

### Logging

Enable detailed logging for debugging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('modules.twitter_api')
```

## Migration Notes

### From Twitter API v1.1
- Update endpoint URLs (handled automatically)
- Adjust field names in responses
- Update authentication method to OAuth 2.0

### Rate Limit Changes
- v2 has different rate limits than v1.1
- Monitor usage patterns and adjust accordingly
- Implement proper error handling for 429 responses