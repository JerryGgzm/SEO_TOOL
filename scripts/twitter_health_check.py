#!/usr/bin/env python3
"""
Twitter API Health Check Script

This script validates Twitter API connectivity and configuration.
Run this script to verify that the Twitter API module is properly configured.
"""

import sys
import os
import logging
import time
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.twitter_api import TwitterAPIClient, TwitterAPIError
from config.twitter_config import twitter_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_configuration() -> Dict[str, Any]:
    """Check Twitter API configuration"""
    logger.info("Checking Twitter API configuration...")
    
    config_status = twitter_config.validate_config()
    
    if config_status['valid']:
        logger.info("✅ Configuration is valid")
        logger.info(f"Client ID: {twitter_config.CLIENT_ID[:10]}..." if twitter_config.CLIENT_ID else "None")
    else:
        logger.error("❌ Configuration errors found:")
        for error in config_status['errors']:
            logger.error(f"  - {error}")
    
    if config_status['warnings']:
        logger.warning("⚠️  Configuration warnings:")
        for warning in config_status['warnings']:
            logger.warning(f"  - {warning}")
    
    return config_status

def check_api_connectivity() -> bool:
    """Check basic API connectivity"""
    logger.info("Checking Twitter API connectivity...")
    
    try:
        # Create client instance
        client = TwitterAPIClient(
            twitter_config.CLIENT_ID,
            twitter_config.CLIENT_SECRET
        )
        
        # Try to get bearer token (app-only auth)
        bearer_token = client.auth.get_bearer_token()
        
        if bearer_token:
            logger.info("✅ Successfully obtained bearer token")
            logger.info(f"Bearer token: {bearer_token[:20]}...")
            return True
        else:
            logger.error("❌ Failed to obtain bearer token")
            return False
            
    except TwitterAPIError as e:
        logger.error(f"❌ Twitter API error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ API connectivity check failed: {e}")
        return False

def check_rate_limiting() -> bool:
    """Check rate limiting functionality"""
    logger.info("Checking rate limiting functionality...")
    
    try:
        from modules.twitter_api.rate_limiter import TwitterRateLimiter, RateLimitInfo
        
        # Test rate limiter
        limiter = TwitterRateLimiter()
        
        # Simulate rate limit info
        test_headers = {
            'x-rate-limit-limit': '300',
            'x-rate-limit-remaining': '299',
            'x-rate-limit-reset': str(int(time.time()) + 900)
        }
        
        limiter.update_rate_limit('test_endpoint', test_headers)
        status = limiter.get_rate_limit_status('test_endpoint')
        
        if status and status['limit'] == 300:
            logger.info("✅ Rate limiting functionality working")
            return True
        else:
            logger.error("❌ Rate limiting functionality failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Rate limiting check failed: {e}")
        return False

def check_endpoints() -> bool:
    """Check endpoint configurations"""
    logger.info("Checking endpoint configurations...")
    
    try:
        from modules.twitter_api.endpoints import TwitterAPIEndpoints
        
        # Test key endpoints
        endpoints_to_test = [
            ('CREATE_TWEET', TwitterAPIEndpoints.CREATE_TWEET),
            ('SEARCH_RECENT_TWEETS', TwitterAPIEndpoints.SEARCH_RECENT_TWEETS),
            ('GET_TRENDS', TwitterAPIEndpoints.GET_TRENDS)
        ]
        
        for name, endpoint in endpoints_to_test:
            url = TwitterAPIEndpoints.get_full_url(endpoint)
            if url and 'api.twitter.com' in url:
                logger.info(f"✅ {name}: {url}")
            else:
                logger.error(f"❌ {name}: Invalid URL")
                return False
        
        logger.info("✅ All endpoint configurations valid")
        return True
        
    except Exception as e:
        logger.error(f"❌ Endpoint configuration check failed: {e}")
        return False

def setup_test_credentials():
    """Setup test credentials using the config system"""
    logger.info("Setting up test credentials...")
    
    # use config class method to set credentials
    test_client_id = "bGoxpxrUUsUDr03gWZvn2o46z"
    test_client_secret = "abpX9L4iqWI7jkbuMJeawqgVrKogQ973hrz9uQsOO9QsmLbB4d"
    
    twitter_config.set_credentials(test_client_id, test_client_secret)
    
    # verify setup
    status = twitter_config.get_credentials_status()
    logger.info(f"credentials status: {status}")
    
    return status['client_id_set'] and status['client_secret_set']

def run_full_health_check() -> bool:
    """Run complete health check"""
    logger.info("=" * 50)
    logger.info("Twitter API Module Health Check")
    logger.info("=" * 50)
    
    # Setup credentials first
    if not setup_test_credentials():
        logger.error("❌ Please setup valid Twitter API v2 credentials first")
        return False
    
    checks = [
        ("Configuration", check_configuration),
        ("API Connectivity", check_api_connectivity),
        ("Rate Limiting", check_rate_limiting),
        ("Endpoints", check_endpoints)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"\n🔍 Running {check_name} check...")
        try:
            if check_name == "Configuration":
                result = check_func()
                results[check_name] = result['valid']
            else:
                results[check_name] = check_func()
        except Exception as e:
            logger.error(f"❌ {check_name} check failed with exception: {e}")
            results[check_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("Health Check Summary")
    logger.info("=" * 50)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All health checks passed! Twitter API module is ready.")
    else:
        logger.error("\n💥 Some health checks failed. Please review the errors above.")
        logger.info("\nTroubleshooting tips:")
        logger.info("1. Ensure you have valid Twitter API v2 credentials")
        logger.info("2. Check that your Twitter Developer account is approved")
        logger.info("3. Verify your app has the necessary permissions")
        logger.info("4. Make sure you're using OAuth 2.0 Client ID/Secret, not v1.1 tokens")
    
    return all_passed

if __name__ == "__main__":
    success = run_full_health_check()
    sys.exit(0 if success else 1)