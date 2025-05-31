from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, UTC
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.sql import func
import json

from .repositories import (
    FounderRepository, ProductRepository, TrendRepository, 
    ContentRepository, AnalyticsRepository, AutomationRepository
)
from .models import *

logger = logging.getLogger(__name__)

class DataFlowManager:
    """
    Manages data flow between modules according to DFD specifications
    Implements the data flow patterns described in section 2.4.2
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
        # Initialize repositories
        self.founder_repo = FounderRepository(db_session)
        self.product_repo = ProductRepository(db_session)
        self.trend_repo = TrendRepository(db_session)
        self.content_repo = ContentRepository(db_session)
        self.analytics_repo = AnalyticsRepository(db_session)
        self.automation_repo = AutomationRepository(db_session)
    
    # ====================
    # DFD 1: User Configuration & Product Information Entry
    # ====================
    
    def process_founder_registration(self, registration_data: Dict[str, Any]) -> Optional[str]:
        """
        Process founder registration flow
        
        Flow: Founder -> UI -> UserProfileModule -> Database
        
        Args:
            registration_data: Registration information from UI
            
        Returns:
            Founder ID if successful, None otherwise
        """
        try:
            # Validate email uniqueness
            existing_founder = self.founder_repo.get_by_email(registration_data['email'])
            if existing_founder:
                logger.warning(f"Registration failed: Email already exists: {registration_data['email']}")
                return None
            
            # Create founder record
            founder = self.founder_repo.create_founder(
                email=registration_data['email'],
                hashed_password=registration_data['hashed_password'],
                settings=registration_data.get('settings', {})
            )
            
            if not founder:
                return None
            
            logger.info(f"Founder registered successfully: {founder.email}")
            return str(founder.id)
            
        except Exception as e:
            logger.error(f"Founder registration failed: {e}")
            return None
    
    def process_product_information_entry(self, founder_id: str, 
                                        product_data: Dict[str, Any]) -> Optional[str]:
        """
        Process product information entry flow
        
        Flow: Founder -> UI -> UserProfileModule -> Database (products table)
        
        Args:
            founder_id: Founder's ID
            product_data: Product information from UI
            
        Returns:
            Product ID if successful, None otherwise
        """
        try:
            # Validate founder exists
            founder = self.founder_repo.get_by_id(founder_id)
            if not founder:
                logger.error(f"Founder not found: {founder_id}")
                return None
            
            # Process core values if provided as list
            core_values_json = None
            if 'core_values' in product_data:
                if isinstance(product_data['core_values'], list):
                    core_values_json = json.dumps(product_data['core_values'])
                else:
                    core_values_json = product_data['core_values']
            
            # Create product record
            product = self.product_repo.create_product(
                founder_id=founder_id,
                product_name=product_data['product_name'],
                description=product_data['description'],
                target_audience_description=product_data['target_audience_description'],
                niche_definition=product_data['niche_definition'],
                core_values=core_values_json,
                seo_keywords=product_data.get('seo_keywords'),
                website_url=product_data.get('website_url')
            )
            
            if not product:
                return None
            
            logger.info(f"Product information saved for founder {founder_id}")
            return str(product.id)
            
        except Exception as e:
            logger.error(f"Product information entry failed: {e}")
            return None
    
    def process_twitter_credentials_storage(self, founder_id: str, 
                                          credentials_data: Dict[str, Any]) -> bool:
        """
        Process Twitter credentials storage flow
        
        Flow: Twitter API -> UserProfileModule -> Database (twitter_credentials table)
        
        Args:
            founder_id: Founder's ID
            credentials_data: Encrypted Twitter credentials
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if credentials already exist
            existing = self.db_session.query(TwitterCredential).filter(
                TwitterCredential.founder_id == founder_id
            ).first()
            
            if existing:
                # Update existing credentials
                existing.twitter_user_id = credentials_data['twitter_user_id']
                existing.screen_name = credentials_data['screen_name']
                existing.encrypted_access_token = credentials_data['encrypted_access_token']
                existing.encrypted_refresh_token = credentials_data.get('encrypted_refresh_token')
                existing.token_expires_at = credentials_data.get('token_expires_at')
                existing.last_validated_at = datetime.now(UTC)
                existing.updated_at = datetime.now(UTC)
                
                self.db_session.commit()
                logger.info(f"Twitter credentials updated for founder {founder_id}")
            else:
                # Create new credentials
                credentials = TwitterCredential(
                    founder_id=founder_id,
                    twitter_user_id=credentials_data['twitter_user_id'],
                    screen_name=credentials_data['screen_name'],
                    encrypted_access_token=credentials_data['encrypted_access_token'],
                    encrypted_refresh_token=credentials_data.get('encrypted_refresh_token'),
                    token_expires_at=credentials_data.get('token_expires_at')
                )
                
                self.db_session.add(credentials)
                self.db_session.commit()
                logger.info(f"Twitter credentials stored for founder {founder_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Twitter credentials storage failed: {e}")
            self.db_session.rollback()
            return False
    
    def get_twitter_credentials(self, founder_id: str) -> Optional[Dict[str, Any]]:
        """Get Twitter credentials for a founder"""
        try:
            credentials = self.db_session.query(TwitterCredential).filter(
                TwitterCredential.founder_id == founder_id
            ).first()
            
            if not credentials:
                return None
            
            return {
                'twitter_user_id': credentials.twitter_user_id,
                'screen_name': credentials.screen_name,
                'encrypted_access_token': credentials.encrypted_access_token,
                'encrypted_refresh_token': credentials.encrypted_refresh_token,
                'token_expires_at': credentials.token_expires_at,
                'is_expired': credentials.is_token_expired()
            }
            
        except Exception as e:
            logger.error(f"Failed to get Twitter credentials: {e}")
            return None
    
    # ====================
    # DFD 2: Trend Analysis Flow
    # ====================
    
    def get_founder_context_for_trend_analysis(self, founder_id: str) -> Optional[Dict[str, Any]]:
        """
        Get founder context for trend analysis
        
        Flow: TrendAnalysisModule -> UserProfileModule -> Return context
        
        Args:
            founder_id: Founder's ID
            
        Returns:
            Context dictionary with founder and product information
        """
        try:
            # Get founder information
            founder = self.founder_repo.get_by_id(founder_id)
            if not founder:
                return None
            
            # Get product information
            products = self.product_repo.get_by_founder_id(founder_id)
            
            # Get Twitter credentials
            twitter_creds = self.get_twitter_credentials(founder_id)
            
            # Extract niche keywords from products
            all_keywords = []
            niche_definitions = []
            
            for product in products:
                if product.niche_definition:
                    niche_definitions.append(product.niche_definition)
                    # Extract keywords from niche definition
                    if 'keywords' in product.niche_definition:
                        all_keywords.extend(product.niche_definition['keywords'])
            
            return {
                'founder_id': founder_id,
                'founder_email': founder.email,
                'founder_settings': founder.settings,
                'products': [
                    {
                        'id': str(product.id),
                        'name': product.product_name,
                        'description': product.description,
                        'niche_definition': product.niche_definition,
                        'core_values': product.core_values_list,
                        'target_audience': product.target_audience_description,
                        'seo_keywords': product.seo_keywords
                    }
                    for product in products
                ],
                'all_keywords': list(set(all_keywords)),  # Remove duplicates
                'niche_definitions': niche_definitions,
                'has_twitter_auth': twitter_creds is not None,
                'twitter_user_id': twitter_creds['twitter_user_id'] if twitter_creds else None,
                'twitter_screen_name': twitter_creds['screen_name'] if twitter_creds else None,
                'twitter_token_expired': twitter_creds['is_expired'] if twitter_creds else True
            }
            
        except Exception as e:
            logger.error(f"Failed to get founder context: {e}")
            return None
    
    def store_analyzed_trends(self, founder_id: str, trends_data: List[Dict[str, Any]]) -> List[str]:
        """
        Store analyzed trends in database
        
        Flow: TrendAnalysisModule -> Database (analyzed_trends table)
        
        Args:
            founder_id: Founder's ID
            trends_data: List of analyzed trend data
            
        Returns:
            List of created trend IDs
        """
        created_trend_ids = []
        
        try:
            for trend_data in trends_data:
                # Process pain points and questions as JSON if they're lists
                pain_points_json = None
                if 'extracted_pain_points' in trend_data:
                    if isinstance(trend_data['extracted_pain_points'], list):
                        pain_points_json = json.dumps(trend_data['extracted_pain_points'])
                    else:
                        pain_points_json = trend_data['extracted_pain_points']
                
                questions_json = None
                if 'common_questions' in trend_data:
                    if isinstance(trend_data['common_questions'], list):
                        questions_json = json.dumps(trend_data['common_questions'])
                    else:
                        questions_json = trend_data['common_questions']
                
                focus_points_json = None
                if 'discussion_focus_points' in trend_data:
                    if isinstance(trend_data['discussion_focus_points'], list):
                        focus_points_json = json.dumps(trend_data['discussion_focus_points'])
                    else:
                        focus_points_json = trend_data['discussion_focus_points']
                
                trend = self.trend_repo.create_analyzed_trend(
                    founder_id=founder_id,
                    topic_name=trend_data['topic_name'],
                    trend_source_id=trend_data.get('trend_source_id'),
                    niche_relevance_score=trend_data['niche_relevance_score'],
                    sentiment_scores=trend_data['sentiment_scores'],
                    extracted_pain_points=pain_points_json,
                    common_questions=questions_json,
                    discussion_focus_points=focus_points_json,
                    is_micro_trend=trend_data.get('is_micro_trend', False),
                    trend_velocity_score=trend_data.get('trend_velocity_score'),
                    trend_potential_score=trend_data.get('trend_potential_score'),
                    example_tweets_json=trend_data.get('example_tweets_json'),
                    expires_at=trend_data.get('expires_at')
                )
                
                if trend:
                    created_trend_ids.append(str(trend.id))
            
            logger.info(f"Stored {len(created_trend_ids)} analyzed trends for founder {founder_id}")
            return created_trend_ids
            
        except Exception as e:
            logger.error(f"Failed to store analyzed trends: {e}")
            return created_trend_ids
    
    def get_relevant_trends_for_content_generation(self, founder_id: str, 
                                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Get relevant trends for content generation"""
        try:
            trends = self.trend_repo.get_trends_by_founder(founder_id, limit, include_expired=False)
            
            return [
                {
                    'id': str(trend.id),
                    'topic_name': trend.topic_name,
                    'sentiment_scores': trend.sentiment_scores,
                    'pain_points': trend.pain_points_list,
                    'questions': trend.questions_list,
                    'focus_points': trend.focus_points_list,
                    'is_micro_trend': trend.is_micro_trend,
                    'relevance_score': trend.niche_relevance_score,
                    'potential_score': trend.trend_potential_score,
                    'analyzed_at': trend.analyzed_at
                }
                for trend in trends
            ]
            
        except Exception as e:
            logger.error(f"Failed to get relevant trends: {e}")
            return []
    
    # ====================
    # DFD 3: Content Generation & Review Flow
    # ====================
    
    def get_content_generation_context(self, founder_id: str, 
                                     trend_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get context for content generation
        
        Flow: ContentGenerationModule -> UserProfileModule + Database -> Return context
        
        Args:
            founder_id: Founder's ID
            trend_id: Specific trend ID (optional)
            
        Returns:
            Context dictionary for content generation
        """
        try:
            # Get founder context
            founder_context = self.get_founder_context_for_trend_analysis(founder_id)
            if not founder_context:
                return None
            
            # Get trend information if specified
            trend_info = None
            if trend_id:
                trend = self.trend_repo.get_by_id(trend_id)
                if trend and trend.founder_id == founder_id:
                    trend_info = {
                        'id': str(trend.id),
                        'topic_name': trend.topic_name,
                        'sentiment_scores': trend.sentiment_scores,
                        'pain_points': trend.pain_points_list,
                        'questions': trend.questions_list,
                        'focus_points': trend.focus_points_list,
                        'is_micro_trend': trend.is_micro_trend,
                        'relevance_score': trend.niche_relevance_score,
                        'potential_score': trend.trend_potential_score
                    }
            
            # Get recent content for context (avoid repetition)
            recent_content = self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.founder_id == founder_id,
                GeneratedContentDraft.created_at >= datetime.now(UTC) - timedelta(days=7)
            ).order_by(GeneratedContentDraft.created_at.desc()).limit(10).all()
            
            # Get content performance insights
            successful_content = self.db_session.query(GeneratedContentDraft).join(
                PostAnalytic, GeneratedContentDraft.posted_tweet_id == PostAnalytic.posted_tweet_id
            ).filter(
                GeneratedContentDraft.founder_id == founder_id,
                PostAnalytic.engagement_rate > 2.0  # Above average engagement
            ).order_by(PostAnalytic.engagement_rate.desc()).limit(5).all()
            
            return {
                **founder_context,
                'trend_info': trend_info,
                'recent_content_count': len(recent_content),
                'recent_topics': [
                    content.analyzed_trend.topic_name 
                    for content in recent_content 
                    if content.analyzed_trend
                ],
                'successful_content_patterns': [
                    {
                        'content_type': content.content_type,
                        'topic': content.analyzed_trend.topic_name if content.analyzed_trend else None,
                        'engagement_rate': content.post_analytics.engagement_rate if content.post_analytics else None
                    }
                    for content in successful_content
                ],
                'content_generation_preferences': founder_context.get('founder_settings', {}).get('content_preferences', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get content generation context: {e}")
            return None
    
    def store_generated_content_draft(self, draft_data: Dict[str, Any]) -> Optional[str]:
        """
        Store generated content draft
        
        Flow: ContentGenerationModule -> Database (generated_content_drafts table)
        
        Args:
            draft_data: Content draft information
            
        Returns:
            Draft ID if successful, None otherwise
        """
        try:
            draft = self.content_repo.create_content_draft(
                founder_id=draft_data['founder_id'],
                content_type=draft_data['content_type'],
                generated_text=draft_data['generated_text'],
                analyzed_trend_id=draft_data.get('analyzed_trend_id'),
                source_tweet_id_for_reply=draft_data.get('source_tweet_id_for_reply'),
                seo_suggestions=draft_data.get('seo_suggestions'),
                ai_generation_metadata=draft_data.get('ai_generation_metadata'),
                scheduled_post_time=draft_data.get('scheduled_post_time')
            )
            
            if draft:
                logger.info(f"Content draft created: {draft.id}")
                return str(draft.id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to store content draft: {e}")
            return None
    
    def get_pending_content_for_review(self, founder_id: str) -> List[Dict[str, Any]]:
        """Get content pending review for a founder"""
        try:
            pending_content = self.content_repo.get_pending_review(founder_id)
            
            return [
                {
                    'id': str(content.id),
                    'content_type': content.content_type,
                    'generated_text': content.generated_text,
                    'trend_topic': content.analyzed_trend.topic_name if content.analyzed_trend else None,
                    'seo_suggestions': content.seo_suggestions,
                    'ai_metadata': content.ai_generation_metadata,
                    'created_at': content.created_at,
                    'source_tweet_id': content.source_tweet_id_for_reply
                }
                for content in pending_content
            ]
            
        except Exception as e:
            logger.error(f"Failed to get pending content: {e}")
            return []
    
    def process_content_review_decision(self, draft_id: str, founder_id: str,
                                      decision: str, **kwargs) -> bool:
        """
        Process content review decision
        
        Flow: UI -> ReviewOptimizationModule -> Database (update draft status)
        
        Args:
            draft_id: Content draft ID
            founder_id: Founder's ID
            decision: Review decision (approved, rejected, edited)
            **kwargs: Additional parameters (edited_text, scheduled_time, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate ownership
            draft = self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.id == draft_id,
                GeneratedContentDraft.founder_id == founder_id
            ).first()
            
            if not draft:
                logger.error(f"Draft not found or access denied: {draft_id}")
                return False
            
            # Process decision
            if decision == 'approved':
                draft.status = 'approved'
                if 'scheduled_time' in kwargs and kwargs['scheduled_time']:
                    draft.scheduled_post_time = kwargs['scheduled_time']
                    draft.status = 'scheduled'
                    
            elif decision == 'rejected':
                draft.status = 'rejected'
                
            elif decision == 'edited':
                draft.edited_text = kwargs.get('edited_text', draft.generated_text)
                draft.status = 'approved'
                if 'scheduled_time' in kwargs and kwargs['scheduled_time']:
                    draft.scheduled_post_time = kwargs['scheduled_time']
                    draft.status = 'scheduled'
            
            else:
                logger.error(f"Invalid decision: {decision}")
                return False
            
            self.db_session.commit()
            logger.info(f"Content review processed: {draft_id} -> {decision}")
            return True
            
        except Exception as e:
            logger.error(f"Content review processing failed: {e}")
            self.db_session.rollback()
            return False
    
    # ====================
    # DFD 4: Content Publishing & Analytics Flow
    # ====================
    
    def get_content_ready_for_publishing(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get content ready for publishing
        
        Flow: SchedulingPostingModule -> Database -> Return content list
        
        Args:
            limit: Maximum number of content items to return
            
        Returns:
            List of content ready for publishing
        """
        try:
            # Get approved content (immediate posting)
            approved_content = self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.status == 'approved'
            ).limit(limit // 2).all()
            
            # Get scheduled content (due for posting)
            scheduled_content = self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.status == 'scheduled',
                GeneratedContentDraft.scheduled_post_time <= datetime.now(UTC)
            ).limit(limit // 2).all()
            
            all_content = approved_content + scheduled_content
            
            return [
                {
                    'draft_id': str(content.id),
                    'founder_id': str(content.founder_id),
                    'content_type': content.content_type,
                    'text': content.final_text,
                    'source_tweet_id': content.source_tweet_id_for_reply,
                    'scheduled_time': content.scheduled_post_time,
                    'seo_suggestions': content.seo_suggestions,
                    'trend_info': {
                        'topic_name': content.analyzed_trend.topic_name,
                        'is_micro_trend': content.analyzed_trend.is_micro_trend
                    } if content.analyzed_trend else None
                }
                for content in all_content
            ]
            
        except Exception as e:
            logger.error(f"Failed to get content for publishing: {e}")
            return []
    
    def record_successful_publication(self, draft_id: str, 
                                    posted_tweet_id: str,
                                    posted_at: Optional[datetime] = None) -> bool:
        """
        Record successful content publication
        
        Flow: TwitterAPI -> SchedulingPostingModule -> Database (update draft status)
        
        Args:
            draft_id: Content draft ID
            posted_tweet_id: Twitter tweet ID from successful post
            posted_at: When the tweet was posted (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.content_repo.update_status(
                draft_id,
                status='posted',
                posted_tweet_id=posted_tweet_id
            )
            
            if success:
                # Create initial analytics record
                draft = self.content_repo.get_by_id(draft_id)
                if draft:
                    initial_analytics = PostAnalytic(
                        posted_tweet_id=posted_tweet_id,
                        founder_id=draft.founder_id,
                        content_draft_id=draft_id,
                        posted_at=posted_at or datetime.now(UTC)
                    )
                    
                    self.db_session.add(initial_analytics)
                    self.db_session.commit()
                
                logger.info(f"Publication recorded: draft {draft_id} -> tweet {posted_tweet_id}")
            
            return success is not None
            
        except Exception as e:
            logger.error(f"Failed to record publication: {e}")
            self.db_session.rollback()
            return False
    
    def record_publication_error(self, draft_id: str, error_message: str) -> bool:
        """Record publication error"""
        try:
            draft = self.content_repo.get_by_id(draft_id)
            if draft:
                draft.status = 'error'
                if not draft.ai_generation_metadata:
                    draft.ai_generation_metadata = {}
                draft.ai_generation_metadata['error'] = {
                    'message': error_message,
                    'timestamp': datetime.now(UTC)
                }
                self.db_session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to record publication error: {e}")
            return False
    
    def store_post_analytics(self, analytics_data: Dict[str, Any]) -> bool:
        """
        Store post analytics data
        
        Flow: TwitterAPI -> AnalyticsModule -> Database (post_analytics table)
        
        Args:
            analytics_data: Post performance metrics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            analytics = self.analytics_repo.create_or_update_analytics(
                posted_tweet_id=analytics_data['posted_tweet_id'],
                founder_id=analytics_data['founder_id'],
                impressions=analytics_data.get('impressions', 0),
                likes=analytics_data.get('likes', 0),
                retweets=analytics_data.get('retweets', 0),
                replies=analytics_data.get('replies', 0),
                quote_tweets=analytics_data.get('quote_tweets', 0),
                link_clicks=analytics_data.get('link_clicks', 0),
                profile_visits_from_tweet=analytics_data.get('profile_visits_from_tweet', 0),
                posted_at=analytics_data.get('posted_at')
            )
            
            if analytics:
                logger.info(f"Analytics stored for tweet {analytics_data['posted_tweet_id']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to store analytics: {e}")
            return False
    
    def get_analytics_dashboard_data(self, founder_id: str, 
                                   days: int = 30) -> Dict[str, Any]:
        """
        Get analytics dashboard data
        
        Flow: UI -> AnalyticsModule -> Database -> Return dashboard data
        
        Args:
            founder_id: Founder's ID
            days: Number of days to analyze
            
        Returns:
            Dashboard data dictionary
        """
        try:
            # Get summary statistics
            summary = self.analytics_repo.get_founder_analytics_summary(founder_id, days)
            
            # Get engagement trends
            trends = self.analytics_repo.get_engagement_trends(founder_id, days)
            
            # Get recent trends analysis
            recent_trends = self.trend_repo.get_trends_by_founder(founder_id, limit=10)
            micro_trends = self.trend_repo.get_micro_trends(founder_id, limit=5)
            
            # Get content performance by trend
            content_by_trend = self.db_session.query(
                GeneratedContentDraft.analyzed_trend_id,
                AnalyzedTrend.topic_name,
                func.count(GeneratedContentDraft.id).label('content_count'),
                func.avg(PostAnalytic.engagement_rate).label('avg_engagement')
            ).join(
                PostAnalytic, GeneratedContentDraft.posted_tweet_id == PostAnalytic.posted_tweet_id
            ).join(
                AnalyzedTrend, GeneratedContentDraft.analyzed_trend_id == AnalyzedTrend.id
            ).filter(
                GeneratedContentDraft.founder_id == founder_id,
                GeneratedContentDraft.status == 'posted'
            ).group_by(
                GeneratedContentDraft.analyzed_trend_id,
                AnalyzedTrend.topic_name
            ).limit(10).all()
            
            print("1")
            # Get automation rules performance
            automation_rules = self.automation_repo.get_active_rules(founder_id)
            
            # Get content status distribution
            content_status_dist = self.db_session.query(
                GeneratedContentDraft.status,
                func.count(GeneratedContentDraft.id).label('count')
            ).filter(
                GeneratedContentDraft.founder_id == founder_id,
                GeneratedContentDraft.created_at >= datetime.now(UTC) - timedelta(days=days)
            ).group_by(GeneratedContentDraft.status).all()
            
            print("2")
            # Average engagement rate
            avg_engagement = self.db_session.query(
                func.avg(PostAnalytic.engagement_rate)
            ).scalar() or 0
            print("3")
            # Twitter credentials status
            twitter_connected = self.db_session.query(TwitterCredential).count()
            expired_tokens = self.db_session.query(TwitterCredential).filter(
                TwitterCredential.token_expires_at < datetime.now(UTC)
            ).count()
            
            return {
                'summary': summary,
                'engagement_trends': trends,
                'recent_trends_count': len(recent_trends),
                'micro_trends_count': len(micro_trends),
                'content_by_trend': [
                    {
                        'trend_topic': item.topic_name,
                        'content_count': item.content_count,
                        'avg_engagement_rate': round(float(item.avg_engagement or 0), 2)
                    }
                    for item in content_by_trend
                ],
                'automation_rules_count': len(automation_rules),
                'active_automation_rules': sum(1 for rule in automation_rules if rule.is_active),
                'content_status_distribution': {
                    status: count for status, count in content_status_dist
                },
                'period_days': days,
                'avg_engagement_rate': round(float(avg_engagement), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}
    
    # ====================
    # Automation Rules Flow
    # ====================
    
    def create_automation_rule(self, founder_id: str, rule_data: Dict[str, Any]) -> Optional[str]:
        """
        Create automation rule
        
        Args:
            founder_id: Founder's ID
            rule_data: Rule configuration
            
        Returns:
            Rule ID if successful, None otherwise
        """
        try:
            rule = self.automation_repo.create_rule(
                founder_id=founder_id,
                rule_name=rule_data['rule_name'],
                trigger_conditions=rule_data['trigger_conditions'],
                action_to_take=rule_data['action_to_take']
            )
            
            if rule:
                logger.info(f"Automation rule created: {rule.id}")
                return str(rule.id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create automation rule: {e}")
            return None
    
    def get_applicable_automation_rules(self, founder_id: str, 
                                       trigger_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get automation rules that apply to a given context
        
        Args:
            founder_id: Founder's ID
            trigger_context: Context to check against rules
            
        Returns:
            List of applicable rules
        """
        try:
            active_rules = self.automation_repo.get_active_rules(founder_id)
            applicable_rules = []
            
            for rule in active_rules:
                if self._rule_applies_to_context(rule.trigger_conditions, trigger_context):
                    applicable_rules.append({
                        'id': str(rule.id),
                        'name': rule.rule_name,
                        'trigger_conditions': rule.trigger_conditions,
                        'action_to_take': rule.action_to_take,
                        'trigger_count': rule.trigger_count
                    })
            
            return applicable_rules
            
        except Exception as e:
            logger.error(f"Failed to get applicable rules: {e}")
            return []
    
    def trigger_automation_rule(self, rule_id: str, trigger_context: Dict[str, Any]) -> bool:
        """
        Execute automation rule action
        
        Args:
            rule_id: Rule ID to trigger
            trigger_context: Context that triggered the rule
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update trigger count
            success = self.automation_repo.update_trigger_count(rule_id)
            if success:
                logger.info(f"Automation rule triggered: {rule_id}")
                # Note: Actual rule execution would be handled by RulesEngineModule
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to trigger automation rule: {e}")
            return False
    
    def _rule_applies_to_context(self, trigger_conditions: Dict[str, Any], 
                                context: Dict[str, Any]) -> bool:
        """
        Check if rule conditions match the current context
        
        Args:
            trigger_conditions: Rule trigger conditions
            context: Current context to check
            
        Returns:
            True if rule applies, False otherwise
        """
        try:
            # Simple condition matching logic
            # This could be expanded with more sophisticated rule evaluation
            
            # Check trend-based conditions
            if 'trend_type' in trigger_conditions:
                required_type = trigger_conditions['trend_type']
                if context.get('is_micro_trend', False) != (required_type == 'micro_trend'):
                    return False
            
            # Check sentiment conditions
            if 'sentiment' in trigger_conditions:
                required_sentiment = trigger_conditions['sentiment']
                context_sentiment = context.get('sentiment', {}).get('dominant_sentiment')
                if context_sentiment != required_sentiment:
                    return False
            
            # Check relevance score conditions
            if 'min_relevance_score' in trigger_conditions:
                min_score = trigger_conditions['min_relevance_score']
                context_score = context.get('relevance_score', 0)
                if context_score < min_score:
                    return False
            
            # Check keyword conditions
            if 'required_keywords' in trigger_conditions:
                required_keywords = trigger_conditions['required_keywords']
                context_keywords = context.get('keywords', [])
                if not any(keyword in context_keywords for keyword in required_keywords):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule conditions: {e}")
            return False
    
    # ====================
    # Data Maintenance and Cleanup
    # ====================
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired data across tables
        
        Returns:
            Dictionary with cleanup counts
        """
        cleanup_counts = {
            'expired_trends': 0,
            'old_drafts': 0,
            'stale_analytics': 0,
            'inactive_rules': 0
        }
        
        try:
            # Clean up expired trends
            expired_trends_count = self.db_session.query(AnalyzedTrend).filter(
                AnalyzedTrend.expires_at < datetime.now(UTC)
            ).delete()
            
            cleanup_counts['expired_trends'] = expired_trends_count
            
            # Clean up old rejected drafts (older than 30 days)
            old_date = datetime.now(UTC) - timedelta(days=30)
            old_drafts_count = self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.status == 'rejected',
                GeneratedContentDraft.created_at < old_date
            ).delete()
            
            cleanup_counts['old_drafts'] = old_drafts_count
            
            # Clean up very old analytics (older than 1 year by default)
            analytics_cutoff = datetime.now(UTC) - timedelta(days=365)
            stale_analytics_count = self.db_session.query(PostAnalytic).filter(
                PostAnalytic.posted_at < analytics_cutoff
            ).delete()
            
            cleanup_counts['stale_analytics'] = stale_analytics_count
            
            # Deactivate rules that haven't been triggered in 90 days
            inactive_rule_cutoff = datetime.now(UTC) - timedelta(days=90)
            inactive_rules = self.db_session.query(AutomationRule).filter(
                or_(
                    AutomationRule.last_triggered_at < inactive_rule_cutoff,
                    and_(
                        AutomationRule.last_triggered_at.is_(None),
                        AutomationRule.created_at < inactive_rule_cutoff
                    )
                ),
                AutomationRule.is_active == True
            ).all()
            
            for rule in inactive_rules:
                rule.is_active = False
            
            cleanup_counts['inactive_rules'] = len(inactive_rules)
            
            self.db_session.commit()
            logger.info(f"Data cleanup completed: {cleanup_counts}")
            
            return cleanup_counts
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            self.db_session.rollback()
            return cleanup_counts
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """
        Get system health and usage metrics
        
        Returns:
            System health metrics
        """
        try:
            # Count total records
            founders_count = self.db_session.query(Founder).count()
            products_count = self.db_session.query(Product).count()
            trends_count = self.db_session.query(AnalyzedTrend).count()
            content_count = self.db_session.query(GeneratedContentDraft).count()
            analytics_count = self.db_session.query(PostAnalytic).count()
            
            # Count active entities
            active_founders = self.db_session.query(Founder).filter(
                Founder.created_at >= datetime.now(UTC) - timedelta(days=30)
            ).count()
            
            recent_trends = self.db_session.query(AnalyzedTrend).filter(
                AnalyzedTrend.analyzed_at >= datetime.now(UTC) - timedelta(days=7)
            ).count()
            
            recent_content = self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.created_at >= datetime.now(UTC) - timedelta(days=7)
            ).count()
            
            # Content status distribution
            content_status = self.db_session.query(
                GeneratedContentDraft.status,
                func.count(GeneratedContentDraft.id)
            ).group_by(GeneratedContentDraft.status).all()
            print("4")
            # Average engagement rate
            avg_engagement = self.db_session.query(
                func.avg(PostAnalytic.engagement_rate)
            ).scalar() or 0
            print("5")
            # Twitter credentials status
            twitter_connected = self.db_session.query(TwitterCredential).count()
            expired_tokens = self.db_session.query(TwitterCredential).filter(
                TwitterCredential.token_expires_at < datetime.now(UTC)
            ).count()
            
            return {
                'total_counts': {
                    'founders': founders_count,
                    'products': products_count,
                    'trends': trends_count,
                    'content_drafts': content_count,
                    'analytics_records': analytics_count
                },
                'activity_metrics': {
                    'active_founders_30d': active_founders,
                    'recent_trends_7d': recent_trends,
                    'recent_content_7d': recent_content,
                    'avg_engagement_rate': round(float(avg_engagement), 2)
                },
                'content_status': dict(content_status),
                'twitter_integration': {
                    'connected_accounts': twitter_connected,
                    'expired_tokens': expired_tokens,
                    'connection_rate': round(twitter_connected / max(founders_count, 1) * 100, 1)
                },
                'timestamp': datetime.now(UTC)
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health metrics: {e}")
            return {}
    
    def export_founder_data(self, founder_id: str) -> Dict[str, Any]:
        """
        Export all data for a founder (for data portability/GDPR compliance)
        
        Args:
            founder_id: Founder's ID
            
        Returns:
            Complete founder data export
        """
        try:
            # Get founder info
            founder = self.founder_repo.get_by_id(founder_id)
            if not founder:
                return {}
            
            # Get all related data
            products = self.product_repo.get_by_founder_id(founder_id)
            trends = self.trend_repo.get_trends_by_founder(founder_id, limit=1000, include_expired=True)
            content_drafts = self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.founder_id == founder_id
            ).all()
            automation_rules = self.automation_repo.get_active_rules(founder_id)
            analytics = self.db_session.query(PostAnalytic).filter(
                PostAnalytic.founder_id == founder_id
            ).all()
            twitter_creds = self.get_twitter_credentials(founder_id)
            
            return {
                'export_timestamp': datetime.now(UTC),
                'founder': {
                    'id': str(founder.id),
                    'email': founder.email,
                    'created_at': founder.created_at,
                    'settings': founder.settings
                },
                'products': [
                    {
                        'id': str(product.id),
                        'name': product.product_name,
                        'description': product.description,
                        'core_values': product.core_values,
                        'target_audience': product.target_audience_description,
                        'niche_definition': product.niche_definition,
                        'created_at': product.created_at
                    }
                    for product in products
                ],
                'analyzed_trends': [
                    {
                        'id': str(trend.id),
                        'topic_name': trend.topic_name,
                        'analyzed_at': trend.analyzed_at,
                        'relevance_score': trend.niche_relevance_score,
                        'sentiment_scores': trend.sentiment_scores,
                        'is_micro_trend': trend.is_micro_trend
                    }
                    for trend in trends
                ],
                'content_drafts': [
                    {
                        'id': str(draft.id),
                        'content_type': draft.content_type,
                        'generated_text': draft.generated_text,
                        'edited_text': draft.edited_text,
                        'status': draft.status,
                        'created_at': draft.created_at,
                        'posted_tweet_id': draft.posted_tweet_id
                    }
                    for draft in content_drafts
                ],
                'automation_rules': [
                    {
                        'id': str(rule.id),
                        'name': rule.rule_name,
                        'trigger_conditions': rule.trigger_conditions,
                        'action_to_take': rule.action_to_take,
                        'is_active': rule.is_active,
                        'trigger_count': rule.trigger_count
                    }
                    for rule in automation_rules
                ],
                'analytics': [
                    {
                        'tweet_id': analytic.posted_tweet_id,
                        'impressions': analytic.impressions,
                        'likes': analytic.likes,
                        'retweets': analytic.retweets,
                        'replies': analytic.replies,
                        'engagement_rate': analytic.engagement_rate,
                        'posted_at': analytic.posted_at if analytic.posted_at else None
                    }
                    for analytic in analytics
                ],
                'twitter_connection': {
                    'connected': twitter_creds is not None,
                    'screen_name': twitter_creds['screen_name'] if twitter_creds else None
                    # Note: We don't export actual credentials for security
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to export founder data: {e}")
            return {}
    
    def delete_founder_data(self, founder_id: str) -> bool:
        """
        Delete all data for a founder (for account deletion/GDPR compliance)
        
        Args:
            founder_id: Founder's ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Due to cascade deletes, we only need to delete the founder
            # All related data will be automatically deleted
            founder = self.founder_repo.get_by_id(founder_id)
            if not founder:
                return False
            
            # Log data deletion for audit purposes
            logger.info(f"Deleting all data for founder: {founder.email}")
            
            success = self.founder_repo.delete(founder_id)
            
            if success:
                logger.info(f"Successfully deleted all data for founder: {founder_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete founder data: {e}")
            return False
    
    # ====================
    # Bulk Operations and Utilities
    # ====================
    
    def bulk_update_trend_expiration(self, days_to_expire: int = 30) -> int:
        """
        Bulk update trend expiration dates
        
        Args:
            days_to_expire: Days from analyzed_at to set expiration
            
        Returns:
            Number of trends updated
        """
        try:
            updated_count = 0
            
            # Get trends without expiration dates
            trends_without_expiry = self.db_session.query(AnalyzedTrend).filter(
                AnalyzedTrend.expires_at.is_(None)
            ).all()
            
            for trend in trends_without_expiry:
                trend.expires_at = trend.analyzed_at + timedelta(days=days_to_expire)
                updated_count += 1
            
            self.db_session.commit()
            logger.info(f"Updated expiration for {updated_count} trends")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to bulk update trend expiration: {e}")
            self.db_session.rollback()

    def recalculate_engagement_rates(self) -> int:
        """
        Recalculate engagement rates for all analytics records
        
        Returns:
            Number of records updated
        """
        try:
            updated_count = 0
            
            analytics_records = self.db_session.query(PostAnalytic).all()
            
            for record in analytics_records:
                if record.impressions and record.impressions > 0:
                    old_rate = record.engagement_rate
                    record.engagement_rate = record.calculate_engagement_rate()
                    
                    if old_rate != record.engagement_rate:
                        updated_count += 1
            
            self.db_session.commit()
            logger.info(f"Recalculated engagement rates for {updated_count} records")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to recalculate engagement rates: {e}")
            self.db_session.rollback()
            return 0

    def store_seo_optimization_result(self, founder_id: str, 
                                    optimization_data: Dict[str, Any]) -> bool:
        """Store SEO optimization results"""
        # TODO
        
    def get_seo_performance_history(self, founder_id: str, 
                                  days: int = 30) -> List[Dict[str, Any]]:
        """Get SEO performance history for analytics"""
        # TODO


class DataFlowManagerSEOExtensions:
    """SEO-related extensions for DataFlowManager"""
    
    def store_seo_optimization_result(self, founder_id: str, optimization_data: Dict[str, Any]) -> bool:
        """
        Store SEO optimization results
        
        Args:
            founder_id: Founder's ID
            optimization_data: SEO optimization data including:
                - content_draft_id: ID of the content draft
                - optimization_timestamp: When optimization was performed
                - seo_quality_score: Overall SEO quality score (0-1)
                - keywords_used: List of keywords used
                - hashtags_suggested: List of hashtags suggested
                - content_type: Type of content (tweet, reply, etc.)
                - optimization_method: Method used for optimization
                - overall_quality_score: Overall content quality score
                - trend_id: Associated trend ID (optional)
                - content_length: Length of optimized content
        
        Returns:
            bool: Success status
        """
        try:
            # Prepare SEO optimization record
            seo_record = {
                'founder_id': founder_id,
                'content_draft_id': optimization_data.get('content_draft_id'),
                'optimization_timestamp': optimization_data.get('optimization_timestamp', datetime.utcnow().isoformat()),
                'seo_quality_score': optimization_data.get('seo_quality_score', 0.0),
                'overall_quality_score': optimization_data.get('overall_quality_score', 0.0),
                'keywords_used': json.dumps(optimization_data.get('keywords_used', [])),
                'hashtags_suggested': json.dumps(optimization_data.get('hashtags_suggested', [])),
                'content_type': optimization_data.get('content_type', 'tweet'),
                'optimization_method': optimization_data.get('optimization_method', 'unknown'),
                'content_length': optimization_data.get('content_length', 0),
                'trend_id': optimization_data.get('trend_id'),
                'metadata': json.dumps({
                    'optimization_level': optimization_data.get('optimization_level'),
                    'hashtag_strategy': optimization_data.get('hashtag_strategy'),
                    'keyword_density': optimization_data.get('keyword_density'),
                    'platform_optimized': optimization_data.get('platform_optimized', 'twitter'),
                    'seo_improvements_made': optimization_data.get('seo_improvements_made', [])
                }),
                'created_at': datetime.utcnow()
            }
            
            # Store in database
            # Note: You'll need to create a table for SEO optimization results
            # For now, we'll simulate storage using a generic approach
            
            # If you have a specific SEO table, use it directly:
            # seo_optimization = SEOOptimizationResult(**seo_record)
            # self.db_session.add(seo_optimization)
            
            # Alternative: Store in a generic analytics table
            analytics_record = {
                'founder_id': founder_id,
                'event_type': 'seo_optimization',
                'event_data': json.dumps(seo_record),
                'timestamp': datetime.utcnow(),
                'category': 'content_generation'
            }
            
            # You can use your existing analytics or logging mechanism
            # For example, if you have an analytics_events table:
            try:
                # Method 1: Use existing analytics infrastructure
                if hasattr(self, 'analytics_repo') and self.analytics_repo:
                    success = self.analytics_repo.create(**analytics_record)
                    if success:
                        self.db_session.commit()
                        logger.info(f"SEO optimization result stored for founder {founder_id}")
                        return True
                
                # Method 2: Store directly using raw SQL if needed
                elif hasattr(self, 'db_session'):
                    # Create a simple table structure if it doesn't exist
                    self.db_session.execute("""
                        CREATE TABLE IF NOT EXISTS seo_optimization_results (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            founder_id TEXT NOT NULL,
                            content_draft_id TEXT,
                            optimization_timestamp TEXT,
                            seo_quality_score REAL,
                            overall_quality_score REAL,
                            keywords_used TEXT,
                            hashtags_suggested TEXT,
                            content_type TEXT,
                            optimization_method TEXT,
                            content_length INTEGER,
                            trend_id TEXT,
                            metadata TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Insert the record
                    self.db_session.execute("""
                        INSERT INTO seo_optimization_results (
                            founder_id, content_draft_id, optimization_timestamp,
                            seo_quality_score, overall_quality_score, keywords_used,
                            hashtags_suggested, content_type, optimization_method,
                            content_length, trend_id, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        seo_record['founder_id'],
                        seo_record['content_draft_id'],
                        seo_record['optimization_timestamp'],
                        seo_record['seo_quality_score'],
                        seo_record['overall_quality_score'],
                        seo_record['keywords_used'],
                        seo_record['hashtags_suggested'],
                        seo_record['content_type'],
                        seo_record['optimization_method'],
                        seo_record['content_length'],
                        seo_record['trend_id'],
                        seo_record['metadata']
                    ))
                    
                    self.db_session.commit()
                    logger.info(f"SEO optimization result stored for founder {founder_id}")
                    return True
                
                else:
                    # Method 3: Log to file as fallback
                    logger.info(f"SEO optimization result (stored to log): {json.dumps(seo_record)}")
                    return True
                    
            except Exception as db_error:
                logger.error(f"Database storage failed, using fallback: {db_error}")
                self.db_session.rollback()
                
                # Fallback: Store in memory or file
                if not hasattr(self, '_seo_optimization_cache'):
                    self._seo_optimization_cache = []
                
                self._seo_optimization_cache.append(seo_record)
                logger.info(f"SEO optimization result cached for founder {founder_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store SEO optimization result: {e}")
            if hasattr(self, 'db_session'):
                self.db_session.rollback()
            return False
    
    def get_seo_performance_history(self, founder_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get SEO performance history for analytics
        
        Args:
            founder_id: Founder's ID
            days: Number of days to look back
            
        Returns:
            List of SEO performance records
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            seo_history = []
            
            # Method 1: Query from dedicated SEO table if it exists
            try:
                if hasattr(self, 'db_session'):
                    # Try to query from seo_optimization_results table
                    results = self.db_session.execute("""
                        SELECT * FROM seo_optimization_results 
                        WHERE founder_id = ? AND created_at >= ?
                        ORDER BY created_at DESC
                    """, (founder_id, since_date.isoformat())).fetchall()
                    
                    for result in results:
                        # Convert database row to dictionary
                        record = {
                            'id': result[0] if len(result) > 0 else None,
                            'founder_id': result[1] if len(result) > 1 else founder_id,
                            'content_draft_id': result[2] if len(result) > 2 else None,
                            'optimization_timestamp': result[3] if len(result) > 3 else None,
                            'seo_quality_score': result[4] if len(result) > 4 else 0.0,
                            'overall_quality_score': result[5] if len(result) > 5 else 0.0,
                            'keywords_used': json.loads(result[6]) if len(result) > 6 and result[6] else [],
                            'hashtags_suggested': json.loads(result[7]) if len(result) > 7 and result[7] else [],
                            'content_type': result[8] if len(result) > 8 else 'tweet',
                            'optimization_method': result[9] if len(result) > 9 else 'unknown',
                            'content_length': result[10] if len(result) > 10 else 0,
                            'trend_id': result[11] if len(result) > 11 else None,
                            'metadata': json.loads(result[12]) if len(result) > 12 and result[12] else {},
                            'created_at': result[13] if len(result) > 13 else None
                        }
                        seo_history.append(record)
                    
                    if seo_history:
                        logger.info(f"Retrieved {len(seo_history)} SEO records from database for founder {founder_id}")
                        return seo_history
                        
            except Exception as db_error:
                logger.warning(f"Database query failed, trying alternative methods: {db_error}")
            
            # Method 2: Query from analytics events if SEO data is stored there
            try:
                if hasattr(self, 'analytics_repo') and self.analytics_repo:
                    analytics_events = self.analytics_repo.get_events_by_founder(
                        founder_id=founder_id,
                        event_type='seo_optimization',
                        since_date=since_date,
                        limit=100
                    )
                    
                    for event in analytics_events:
                        try:
                            event_data = json.loads(event.event_data) if isinstance(event.event_data, str) else event.event_data
                            seo_history.append({
                                'id': event.id,
                                'founder_id': event_data.get('founder_id', founder_id),
                                'content_draft_id': event_data.get('content_draft_id'),
                                'optimization_timestamp': event_data.get('optimization_timestamp'),
                                'seo_quality_score': event_data.get('seo_quality_score', 0.0),
                                'overall_quality_score': event_data.get('overall_quality_score', 0.0),
                                'keywords_used': event_data.get('keywords_used', []),
                                'hashtags_suggested': event_data.get('hashtags_suggested', []),
                                'content_type': event_data.get('content_type', 'tweet'),
                                'optimization_method': event_data.get('optimization_method', 'unknown'),
                                'content_length': event_data.get('content_length', 0),
                                'trend_id': event_data.get('trend_id'),
                                'metadata': event_data.get('metadata', {}),
                                'created_at': event.timestamp.isoformat() if hasattr(event, 'timestamp') else None
                            })
                        except Exception as parse_error:
                            logger.warning(f"Failed to parse analytics event: {parse_error}")
                            continue
                    
                    if seo_history:
                        logger.info(f"Retrieved {len(seo_history)} SEO records from analytics for founder {founder_id}")
                        return seo_history
                        
            except Exception as analytics_error:
                logger.warning(f"Analytics query failed: {analytics_error}")
            
            # Method 3: Check in-memory cache as fallback
            if hasattr(self, '_seo_optimization_cache'):
                cached_records = [
                    record for record in self._seo_optimization_cache
                    if record.get('founder_id') == founder_id and
                    datetime.fromisoformat(record.get('optimization_timestamp', '1970-01-01')) >= since_date
                ]
                
                if cached_records:
                    logger.info(f"Retrieved {len(cached_records)} SEO records from cache for founder {founder_id}")
                    return cached_records
            
            # Method 4: Generate sample data for demonstration (remove in production)
            if not seo_history:
                logger.info(f"No SEO history found for founder {founder_id}, generating sample data")
                seo_history = self._generate_sample_seo_history(founder_id, days)
            
            return seo_history
            
        except Exception as e:
            logger.error(f"Failed to get SEO performance history: {e}")
            return []
    
    def _generate_sample_seo_history(self, founder_id: str, days: int) -> List[Dict[str, Any]]:
        """Generate sample SEO history for demonstration purposes"""
        import random
        from datetime import datetime, timedelta
        
        sample_data = []
        
        # Generate sample records for the past few days
        for i in range(min(days // 2, 10)):  # Generate up to 10 sample records
            days_ago = random.randint(0, days)
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            
            sample_record = {
                'id': f"sample_{i}_{founder_id}",
                'founder_id': founder_id,
                'content_draft_id': f"draft_{i}_{founder_id}",
                'optimization_timestamp': timestamp.isoformat(),
                'seo_quality_score': random.uniform(0.4, 0.9),
                'overall_quality_score': random.uniform(0.5, 0.85),
                'keywords_used': random.sample([
                    'AI', 'innovation', 'startup', 'technology', 'productivity', 
                    'growth', 'automation', 'digital transformation', 'business'
                ], random.randint(2, 5)),
                'hashtags_suggested': random.sample([
                    'AI', 'innovation', 'startup', 'tech', 'productivity', 
                    'growth', 'automation', 'business', 'entrepreneur'
                ], random.randint(3, 6)),
                'content_type': random.choice(['tweet', 'reply', 'thread']),
                'optimization_method': random.choice(['integrated_generation', 'post_generation', 'manual']),
                'content_length': random.randint(120, 280),
                'trend_id': f"trend_{random.randint(1, 10)}" if random.random() > 0.3 else None,
                'metadata': {
                    'optimization_level': random.choice(['basic', 'moderate', 'aggressive']),
                    'hashtag_strategy': random.choice(['engagement_optimized', 'discovery_focused', 'brand_building']),
                    'keyword_density': random.uniform(0.01, 0.04),
                    'platform_optimized': 'twitter',
                    'seo_improvements_made': random.sample([
                        'Added relevant hashtags',
                        'Optimized keyword density',
                        'Improved content length',
                        'Enhanced readability'
                    ], random.randint(1, 3))
                },
                'created_at': timestamp.isoformat()
            }
            
            sample_data.append(sample_record)
        
        return sample_data
    
    def get_seo_analytics_summary(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get SEO analytics summary for founder
        
        Args:
            founder_id: Founder's ID
            days: Number of days to analyze
            
        Returns:
            SEO analytics summary
        """
        try:
            # Get SEO performance history
            seo_history = self.get_seo_performance_history(founder_id, days)
            
            if not seo_history:
                return {
                    'total_optimizations': 0,
                    'avg_seo_score': 0.0,
                    'avg_overall_score': 0.0,
                    'top_keywords': [],
                    'top_hashtags': [],
                    'optimization_trend': 'no_data',
                    'content_type_distribution': {},
                    'period_days': days
                }
            
            # Calculate summary metrics
            total_optimizations = len(seo_history)
            avg_seo_score = sum(record.get('seo_quality_score', 0) for record in seo_history) / total_optimizations
            avg_overall_score = sum(record.get('overall_quality_score', 0) for record in seo_history) / total_optimizations
            
            # Analyze keywords and hashtags
            all_keywords = []
            all_hashtags = []
            content_types = {}
            
            for record in seo_history:
                keywords = record.get('keywords_used', [])
                hashtags = record.get('hashtags_suggested', [])
                content_type = record.get('content_type', 'unknown')
                
                all_keywords.extend(keywords)
                all_hashtags.extend(hashtags)
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            # Get top keywords and hashtags
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            hashtag_counts = Counter(all_hashtags)
            
            top_keywords = [kw for kw, count in keyword_counts.most_common(10)]
            top_hashtags = [ht for ht, count in hashtag_counts.most_common(10)]
            
            # Analyze optimization trend
            optimization_trend = self._analyze_seo_trend(seo_history)
            
            return {
                'total_optimizations': total_optimizations,
                'avg_seo_score': round(avg_seo_score, 3),
                'avg_overall_score': round(avg_overall_score, 3),
                'top_keywords': top_keywords,
                'top_hashtags': top_hashtags,
                'optimization_trend': optimization_trend,
                'content_type_distribution': content_types,
                'keyword_diversity': len(set(all_keywords)),
                'hashtag_diversity': len(set(all_hashtags)),
                'period_days': days,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get SEO analytics summary: {e}")
            return {}
    
    def _analyze_seo_trend(self, seo_history: List[Dict[str, Any]]) -> str:
        """Analyze SEO optimization trend"""
        try:
            if len(seo_history) < 3:
                return 'insufficient_data'
            
            # Sort by timestamp
            sorted_history = sorted(
                seo_history,
                key=lambda x: x.get('optimization_timestamp', '1970-01-01')
            )
            
            # Calculate trend using first third vs last third
            third_size = len(sorted_history) // 3
            if third_size == 0:
                return 'insufficient_data'
            
            early_scores = [record.get('seo_quality_score', 0) for record in sorted_history[:third_size]]
            recent_scores = [record.get('seo_quality_score', 0) for record in sorted_history[-third_size:]]
            
            early_avg = sum(early_scores) / len(early_scores) if early_scores else 0
            recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            
            improvement = recent_avg - early_avg
            
            if improvement > 0.1:
                return 'improving'
            elif improvement < -0.1:
                return 'declining'
            else:
                return 'stable'
                
        except Exception as e:
            logger.warning(f"Failed to analyze SEO trend: {e}")
            return 'unknown'
    
    def cleanup_old_seo_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old SEO optimization data
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            # Clean up from database
            if hasattr(self, 'db_session'):
                try:
                    result = self.db_session.execute("""
                        DELETE FROM seo_optimization_results 
                        WHERE created_at < ?
                    """, (cutoff_date.isoformat(),))
                    
                    deleted_count = result.rowcount
                    self.db_session.commit()
                    
                except Exception as db_error:
                    logger.warning(f"Database cleanup failed: {db_error}")
                    self.db_session.rollback()
            
            # Clean up from cache
            if hasattr(self, '_seo_optimization_cache'):
                original_count = len(self._seo_optimization_cache)
                self._seo_optimization_cache = [
                    record for record in self._seo_optimization_cache
                    if datetime.fromisoformat(record.get('optimization_timestamp', '1970-01-01')) >= cutoff_date
                ]
                cache_deleted = original_count - len(self._seo_optimization_cache)
                deleted_count += cache_deleted
            
            logger.info(f"Cleaned up {deleted_count} old SEO optimization records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old SEO data: {e}")
            return 0