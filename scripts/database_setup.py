#!/usr/bin/env python3
"""
Ideation Database Setup and Management Script

This script provides comprehensive database management functionality including:
- Database creation and initialization
- Schema migrations and updates
- Data validation and testing
- Performance monitoring
- Backup and restore operations
- Development utilities

Usage:
    python scripts/database_setup.py --help
    python scripts/database_setup.py create
    python scripts/database_setup.py test
    python scripts/database_setup.py demo
    python scripts/database_setup.py migrate
    python scripts/database_setup.py backup
"""

import sys
import os
import argparse
import logging
import time
import json
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import database modules
try:
    from database import (
        init_database, get_db_manager, get_db_context, 
        DataFlowManager, health_check
    )
    from database.models import *
    from database.repositories import *
    from config.database_config import database_config
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_setup.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseSetupManager:
    """Manages all database setup and maintenance operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database setup manager"""
        self.database_url = database_url or database_config.DATABASE_URL
        logger.info("Database Setup Manager initialized")
        logger.info(f"Database URL: {self._mask_password(self.database_url)}")
        
        # Initialize database connection
        self._initialize_database_connection()
    
    def _initialize_database_connection(self):
        """Initialize database connection for all operations"""
        try:
            # Initialize database connection
            init_database(self.database_url, create_tables=False)
            logger.info("Database connection initialized")
        except Exception as e:
            logger.warning(f"Database connection initialization failed: {e}")
            # Don't raise an exception here, let the specific operations handle it
    
    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging"""
        if '@' in url and ':' in url:
            parts = url.split('@')
            if len(parts) == 2:
                user_pass = parts[0].split('//')[-1]
                if ':' in user_pass:
                    user, _ = user_pass.split(':', 1)
                    return url.replace(user_pass, f"{user}:****")
        return url
    
    def create_database(self) -> bool:
        """Create database and tables"""
        try:
            print("🔨 Creating database and tables...")
            
            # Initialize database and create tables
            init_database(self.database_url, create_tables=True)
            
            # Test connectivity
            if not health_check():
                raise Exception("Database health check failed after creation")
            
            print("✅ Database and tables created successfully")
            logger.info("Database creation completed successfully")
            
            # Show table information
            self._show_table_info()
            
            return True
            
        except Exception as e:
            print(f"❌ Database creation failed: {e}")
            logger.error(f"Database creation failed: {e}")
            return False
    
    def _show_table_info(self):
        """Show information about created tables"""
        try:
            with get_db_context() as session:
                # Count tables by checking if they exist
                tables = [
                    ('founders', Founder),
                    ('products', Product),
                    ('twitter_credentials', TwitterCredential),
                    ('analyzed_trends', AnalyzedTrend),
                    ('generated_content_drafts', GeneratedContentDraft),
                    ('automation_rules', AutomationRule),
                    ('post_analytics', PostAnalytic),
                    ('tracked_trends_raw', TrackedTrendRaw)
                ]
                
                print("\n📋 Database Tables Created:")
                print("-" * 50)
                
                for table_name, model_class in tables:
                    try:
                        count = session.query(model_class).count()
                        print(f"  {table_name:25} ✅ (0 records)")
                    except Exception as e:
                        print(f"  {table_name:25} ❌ Error: {e}")
                
                print()
                
        except Exception as e:
            logger.warning(f"Could not show table info: {e}")
    
    def test_database(self) -> bool:
        """Test database connectivity and basic operations"""
        try:
            print("🧪 Testing database connectivity and operations...")
            
            # 确保数据库已初始化
            if not self._ensure_database_initialized():
                return False
            
            # Test 1: Health check
            print("  📊 Running health check...")
            if health_check():
                print("  ✅ Health check passed")
            else:
                print("  ❌ Health check failed")
                return False
            
            # Test 2: Basic CRUD operations
            print("  🔄 Testing CRUD operations...")
            success = self._test_crud_operations()
            if not success:
                return False
            
            # Test 3: Data flow operations
            print("  🌊 Testing data flow operations...")
            success = self._test_data_flow_operations()
            if not success:
                return False
            
            # Test 4: Repository operations
            print("  📚 Testing repository operations...")
            success = self._test_repository_operations()
            if not success:
                return False
            
            print("✅ All database tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            logger.error(f"Database test failed: {e}")
            return False
    
    def _ensure_database_initialized(self) -> bool:
        """确保数据库已初始化"""
        try:
            # 尝试初始化数据库连接
            init_database(self.database_url, create_tables=False)
            return True
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def _test_crud_operations(self) -> bool:
        """Test basic CRUD operations"""
        try:
            with get_db_context() as session:
                # Create test founder
                test_founder = Founder(
                    email='test_crud@example.com',
                    hashed_password='test_hash_123',
                    settings={'test_mode': True}
                )
                session.add(test_founder)
                session.commit()
                
                # Read test founder
                found_founder = session.query(Founder).filter(
                    Founder.email == 'test_crud@example.com'
                ).first()
                
                if not found_founder:
                    raise Exception("Could not find created founder")
                
                # Update test founder
                found_founder.settings = {'test_mode': True, 'updated': True}
                session.commit()
                
                # Verify update
                updated_founder = session.query(Founder).filter(
                    Founder.id == found_founder.id
                ).first()
                
                if not updated_founder.settings.get('updated'):
                    raise Exception("Update operation failed")
                
                # Delete test founder
                session.delete(updated_founder)
                session.commit()
                
                # Verify deletion
                deleted_founder = session.query(Founder).filter(
                    Founder.id == found_founder.id
                ).first()
                
                if deleted_founder:
                    raise Exception("Delete operation failed")
                
                print("    ✅ CRUD operations working correctly")
                return True
                
        except Exception as e:
            print(f"    ❌ CRUD operations failed: {e}")
            logger.error(f"CRUD operations test failed: {e}")
            return False
    
    def _test_data_flow_operations(self) -> bool:
        """Test data flow operations"""
        try:
            print("  🌊 Testing data flow operations...")
            
            with get_db_context() as session:
                data_flow = DataFlowManager(session)
                
                # Test founder registration
                founder_data = {
                    'email': 'test_dataflow@example.com',
                    'hashed_password': 'test_hash_123',
                    'settings': {'theme': 'dark'}
                }
                
                founder_id = data_flow.process_founder_registration(founder_data)
                if not founder_id:
                    raise Exception("Founder registration failed")
                
                # Test product information entry
                product_data = {
                    'product_name': 'Test Product',
                    'description': 'A test product for validation',
                    'target_audience_description': 'Test audience',
                    'niche_definition': 'Test niche',
                    'core_values': ['innovation', 'quality']
                }
                
                product_id = data_flow.process_product_information_entry(founder_id, product_data)
                if not product_id:
                    raise Exception("Product creation failed")
                
                # Test trend analysis
                trends_data = [{
                    'topic_name': 'Test Trend',
                    'niche_relevance_score': 0.85,
                    'sentiment_scores': {'positive': 0.7, 'negative': 0.1, 'neutral': 0.2},
                    'is_micro_trend': True
                }]
                
                trend_ids = data_flow.store_analyzed_trends(founder_id, trends_data)
                if not trend_ids:
                    raise Exception("Trend storage failed")
                
                # Test content generation
                content_data = {
                    'founder_id': founder_id,
                    'analyzed_trend_id': trend_ids[0],
                    'content_type': 'tweet',
                    'generated_text': 'Test tweet content #TestTrend',
                    'seo_suggestions': {
                        'hashtags': ['#TestTrend'],
                        'keywords': ['test', 'trend']
                    }
                }
                
                content_id = data_flow.store_generated_content_draft(content_data)
                if not content_id:
                    raise Exception("Content generation failed")
                
                # Cleanup test data
                try:
                    # 1. Delete content draft
                    content_draft = session.query(GeneratedContentDraft).filter(
                        GeneratedContentDraft.id == content_id
                    ).first()
                    if content_draft:
                        session.delete(content_draft)
                    
                    # 2. Delete trend analysis
                    for trend_id in trend_ids:
                        trend = session.query(AnalyzedTrend).filter(
                            AnalyzedTrend.id == trend_id
                        ).first()
                        if trend:
                            session.delete(trend)
                    
                    # 3. Delete product
                    product = session.query(Product).filter(
                        Product.id == product_id
                    ).first()
                    if product:
                        session.delete(product)
                    
                    # 4. Delete founder
                    founder = session.query(Founder).filter(
                        Founder.id == founder_id
                    ).first()
                    if founder:
                        session.delete(founder)
                    
                    # Commit delete operations
                    session.commit()
                    
                except Exception as cleanup_error:
                    logger.warning(f"Test data cleanup failed: {cleanup_error}")
                    session.rollback()
                    # Don't let cleanup failure cause the entire test to fail
                
                return True
                
        except Exception as e:
            logger.error(f"Data flow operations test failed: {e}")
            return False
    
    def _test_repository_operations(self) -> bool:
        """Test repository pattern operations"""
        try:
            with get_db_context() as session:
                founder_repo = FounderRepository(session)
                
                # Test repository creation
                founder = founder_repo.create_founder(
                    email='test_repo@example.com',
                    hashed_password='repo_hash_789',
                    settings={'repo_test': True}
                )
                
                if not founder:
                    raise Exception("Repository creation failed")
                
                # Test repository retrieval
                found_founder = founder_repo.get_by_email('test_repo@example.com')
                if not found_founder or found_founder.id != founder.id:
                    raise Exception("Repository retrieval failed")
                
                # Test repository update
                updated_founder = founder_repo.update_settings(
                    str(founder.id), 
                    {'repo_test': True, 'updated_via_repo': True}
                )
                
                if not updated_founder or not updated_founder.settings.get('updated_via_repo'):
                    raise Exception("Repository update failed")
                
                # Test repository deletion
                deleted = founder_repo.delete(str(founder.id))
                if not deleted:
                    raise Exception("Repository deletion failed")
                
                print("    ✅ Repository operations working correctly")
                return True
                
        except Exception as e:
            print(f"    ❌ Repository operations failed: {e}")
            logger.error(f"Repository operations test failed: {e}")
            return False
    
    def run_demo(self) -> bool:
        """Run comprehensive demonstration of system capabilities"""
        try:
            print("🎭 Running comprehensive system demonstration...")
            print("=" * 60)
            
            with get_db_context() as session:
                data_flow = DataFlowManager(session)
                
                # Demo 1: Complete user onboarding
                print("\n1️⃣  User Onboarding Demo")
                print("-" * 30)
                
                demo_founder = {
                    'email': 'demo@ideation.com',
                    'hashed_password': 'demo_hash_secure',
                    'settings': {
                        'demo_mode': True,
                        'timezone': 'UTC',
                        'notifications': True
                    }
                }
                
                founder_id = data_flow.process_founder_registration(demo_founder)
                if founder_id:
                    print(f"   ✅ Demo founder registered: {founder_id[:8]}...")
                else:
                    raise Exception("Demo founder registration failed")
                
                # Add product information
                demo_product = {
                    'product_name': 'EcoTrack Pro',
                    'description': 'AI-powered sustainability tracking for businesses',
                    'target_audience_description': 'Small to medium businesses focused on sustainability',
                    'niche_definition': {
                        'keywords': ['sustainability', 'green', 'carbon', 'eco-friendly', 'environment'],
                        'tags': ['#sustainability', '#greentech', '#carbonneutral'],
                        'exclusions': ['greenwashing', 'fake-eco']
                    },
                    'core_values': ['environmental impact', 'transparency', 'data-driven decisions'],
                    'seo_keywords': 'carbon tracking, sustainability software, green business',
                    'website_url': 'https://ecotrack-pro.demo'
                }
                
                product_id = data_flow.process_product_information_entry(founder_id, demo_product)
                if product_id:
                    print(f"   ✅ Demo product created: EcoTrack Pro")
                else:
                    raise Exception("Demo product creation failed")
                
                # Demo 2: Trend analysis and storage
                print("\n2️⃣  Trend Analysis Demo")
                print("-" * 30)
                
                demo_trends = [
                    {
                        'topic_name': '#CarbonNeutral',
                        'niche_relevance_score': 0.92,
                        'sentiment_scores': {
                            'positive': 0.7,
                            'negative': 0.1,
                            'neutral': 0.2,
                            'dominant_sentiment': 'positive'
                        },
                        'extracted_pain_points': [
                            'difficulty tracking carbon footprint',
                            'lack of transparency in supply chain',
                            'complex sustainability reporting'
                        ],
                        'common_questions': [
                            'How to measure carbon footprint accurately?',
                            'What are the best sustainability practices?',
                            'How to report environmental impact?'
                        ],
                        'discussion_focus_points': [
                            'carbon tracking tools',
                            'sustainability metrics',
                            'green technology adoption'
                        ],
                        'is_micro_trend': True,
                        'trend_velocity_score': 8.5,
                        'trend_potential_score': 0.88
                    },
                    {
                        'topic_name': '#GreenTech',
                        'niche_relevance_score': 0.85,
                        'sentiment_scores': {
                            'positive': 0.6,
                            'negative': 0.2,
                            'neutral': 0.2,
                            'dominant_sentiment': 'positive'
                        },
                        'extracted_pain_points': [
                            'high cost of green technology',
                            'limited adoption in SMBs',
                            'ROI uncertainty'
                        ],
                        'is_micro_trend': False,
                        'trend_velocity_score': 6.2,
                        'trend_potential_score': 0.75
                    }
                ]
                
                trend_ids = data_flow.store_analyzed_trends(founder_id, demo_trends)
                print(f"   ✅ Stored {len(trend_ids)} analyzed trends")
                
                # Demo 3: Content generation workflow
                print("\n3️⃣  Content Generation Demo")
                print("-" * 30)
                
                demo_content_drafts = [
                    {
                        'founder_id': founder_id,
                        'analyzed_trend_id': trend_ids[0],
                        'content_type': 'tweet',
                        'generated_text': '🌱 Achieving #CarbonNeutral goals starts with accurate tracking. EcoTrack Pro helps businesses measure, monitor, and reduce their environmental impact with AI-powered insights. Ready to go green? 🌍 #GreenTech #Sustainability',
                        'seo_suggestions': {
                            'hashtags': ['#CarbonNeutral', '#GreenTech', '#Sustainability', '#EcoFriendly'],
                            'keywords': ['carbon tracking', 'environmental impact', 'sustainability software']
                        },
                        'ai_generation_metadata': {
                            'trend_used': '#CarbonNeutral',
                            'pain_point_addressed': 'difficulty tracking carbon footprint',
                            'product_value_highlighted': 'AI-powered insights',
                            'generation_strategy': 'pain-point-solution-approach'
                        }
                    },
                    {
                        'founder_id': founder_id,
                        'analyzed_trend_id': trend_ids[1],
                        'content_type': 'tweet',
                        'generated_text': 'The future of business is green 💚 While #GreenTech adoption faces cost challenges, the long-term ROI is undeniable. Start small, track progress, and watch your sustainability efforts pay off. What\'s your first green step? 🔋',
                        'seo_suggestions': {
                            'hashtags': ['#GreenTech', '#SustainableBusiness', '#ROI'],
                            'keywords': ['green technology', 'sustainable business', 'environmental ROI']
                        },
                        'ai_generation_metadata': {
                            'trend_used': '#GreenTech',
                            'pain_point_addressed': 'ROI uncertainty',
                            'content_strategy': 'educational-question-engagement'
                        }
                    }
                ]
                
                draft_ids = []
                for draft_data in demo_content_drafts:
                    draft_id = data_flow.store_generated_content_draft(draft_data)
                    if draft_id:
                        draft_ids.append(draft_id)
                
                print(f"   ✅ Generated {len(draft_ids)} content drafts")
                
                # Demo 4: Content review and approval
                print("\n4️⃣  Content Review Demo")
                print("-" * 30)
                
                # Approve first draft immediately
                approval_1 = data_flow.process_content_review_decision(
                    draft_ids[0], founder_id, 'approved'
                )
                
                # Edit and schedule second draft
                approval_2 = data_flow.process_content_review_decision(
                    draft_ids[1], founder_id, 'edited',
                    edited_text="The future of business is green 💚 #GreenTech adoption may face initial costs, but ROI grows over time. EcoTrack Pro helps you start small and track progress. What's your sustainability goal? 🌱",
                    scheduled_time=datetime.utcnow() + timedelta(hours=2)
                )
                
                if approval_1 and approval_2:
                    print("   ✅ Content review and approval completed")
                else:
                    raise Exception("Content review failed")
                
                # Demo 5: Publication simulation
                print("\n5️⃣  Publication Simulation")
                print("-" * 30)
                
                # Simulate successful publications
                pub_1 = data_flow.record_successful_publication(
                    draft_ids[0], 'demo_tweet_1234567890',
                    posted_at=datetime.utcnow()
                )
                
                pub_2 = data_flow.record_successful_publication(
                    draft_ids[1], 'demo_tweet_0987654321',
                    posted_at=datetime.utcnow() - timedelta(minutes=30)
                )
                
                if pub_1 and pub_2:
                    print("   ✅ Publications recorded successfully")
                else:
                    raise Exception("Publication recording failed")
                
                # Demo 6: Analytics simulation
                print("\n6️⃣  Analytics Demo")
                print("-" * 30)
                
                analytics_data = [
                    {
                        'posted_tweet_id': 'demo_tweet_1234567890',
                        'founder_id': founder_id,
                        'impressions': 2500,
                        'likes': 85,
                        'retweets': 23,
                        'replies': 12,
                        'quote_tweets': 5,
                        'link_clicks': 45,
                        'profile_visits_from_tweet': 15,
                        'posted_at': datetime.utcnow()
                    },
                    {
                        'posted_tweet_id': 'demo_tweet_0987654321',
                        'founder_id': founder_id,
                        'impressions': 1800,
                        'likes': 62,
                        'retweets': 18,
                        'replies': 8,
                        'quote_tweets': 3,
                        'link_clicks': 32,
                        'profile_visits_from_tweet': 11,
                        'posted_at': datetime.utcnow() - timedelta(minutes=30)
                    }
                ]
                
                for analytics in analytics_data:
                    success = data_flow.store_post_analytics(analytics)
                    if not success:
                        raise Exception("Analytics storage failed")
                
                print("   ✅ Analytics data stored successfully")
                
                # Demo 7: Dashboard and reporting
                print("\n7️⃣  Dashboard Demo")
                print("-" * 30)
                
                dashboard_data = data_flow.get_analytics_dashboard_data(founder_id, days=7)
                
                if dashboard_data:
                    summary = dashboard_data['summary']
                    print(f"   📊 Dashboard Summary:")
                    print(f"      Total Posts: {summary['total_posts']}")
                    print(f"      Total Impressions: {summary['total_impressions']:,}")
                    print(f"      Total Engagements: {summary['total_engagements']}")
                    print(f"      Avg Engagement Rate: {summary['avg_engagement_rate']:.1f}%")
                    print(f"      Best Tweet Engagement: {summary.get('best_performing_tweet', {}).get('engagement_rate', 0):.1f}%")
                else:
                    raise Exception("Dashboard data retrieval failed")
                
                # Demo 8: System health check
                print("\n8️⃣  System Health Check")
                print("-" * 30)
                
                health_metrics = data_flow.get_system_health_metrics()
                if health_metrics:
                    print(f"   🏥 System Health:")
                    print(f"      Total Founders: {health_metrics['total_counts']['founders']}")
                    print(f"      Total Products: {health_metrics['total_counts']['products']}")
                    print(f"      Total Trends: {health_metrics['total_counts']['trends']}")
                    print(f"      Total Content: {health_metrics['total_counts']['content_drafts']}")
                    print(f"      Avg Engagement: {health_metrics['activity_metrics']['avg_engagement_rate']:.1f}%")
                else:
                    raise Exception("Health metrics retrieval failed")
                
            print("\n🎉 Demo completed successfully!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n💥 Demo failed: {e}")
            logger.error(f"Demo execution failed: {e}")
            return False
        finally:
            # Cleanup demo data
            self._cleanup_demo_data()
    
    def _cleanup_demo_data(self):
        """Clean up demo data"""
        try:
            with get_db_context() as session:
                # Delete demo founder (cascades to all related data)
                demo_founder = session.query(Founder).filter(
                    Founder.email == 'demo@ideation.com'
                ).first()
                
                if demo_founder:
                    session.delete(demo_founder)
                    session.commit()
                    logger.info("Demo data cleaned up successfully")
                    
        except Exception as e:
            logger.warning(f"Demo data cleanup failed: {e}")
    
    def show_stats(self) -> bool:
        """Show comprehensive database statistics"""
        try:
            print("📊 Database Statistics")
            print("=" * 50)
            
            if not health_check():
                print("❌ Database is not accessible")
                return False
            
            with get_db_context() as session:
                data_flow = DataFlowManager(session)
                
                # Get system health metrics
                health_metrics = data_flow.get_system_health_metrics()
                
                if health_metrics:
                    print("\n🏥 System Overview:")
                    print("-" * 20)
                    total_counts = health_metrics['total_counts']
                    for entity, count in total_counts.items():
                        print(f"  {entity.replace('_', ' ').title():20}: {count:>8,}")
                    
                    print("\n📈 Activity Metrics (Recent):")
                    print("-" * 30)
                    activity = health_metrics['activity_metrics']
                    print(f"  Active Founders (30d):     {activity['active_founders_30d']:>8}")
                    print(f"  Recent Trends (7d):        {activity['recent_trends_7d']:>8}")
                    print(f"  Recent Content (7d):       {activity['recent_content_7d']:>8}")
                    print(f"  Avg Engagement Rate:       {activity['avg_engagement_rate']:>7.1f}%")
                    
                    print("\n🐦 Twitter Integration:")
                    print("-" * 25)
                    twitter = health_metrics['twitter_integration']
                    print(f"  Connected Accounts:        {twitter['connected_accounts']:>8}")
                    print(f"  Expired Tokens:            {twitter['expired_tokens']:>8}")
                    print(f"  Connection Rate:           {twitter['connection_rate']:>7.1f}%")
                    
                    # Content status distribution
                    if 'content_status' in health_metrics:
                        print("\n📝 Content Status Distribution:")
                        print("-" * 35)
                        for status, count in health_metrics['content_status'].items():
                            print(f"  {status.replace('_', ' ').title():20}: {count:>8}")
                
                # Database size and performance info
                self._show_performance_stats(session)
                
            print("\n✅ Statistics retrieved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to retrieve statistics: {e}")
            logger.error(f"Statistics retrieval failed: {e}")
            return False
    
    def _show_performance_stats(self, session):
        """Show database performance statistics"""
        try:
            print("\n⚡ Performance Metrics:")
            print("-" * 25)
            
            # Simple performance test
            start_time = time.time()
            founder_count = session.query(Founder).count()
            query_time = (time.time() - start_time) * 1000
            
            print(f"  Simple Query Time:         {query_time:>6.1f}ms")
            
            # Connection info
            db_manager = get_db_manager()
            conn_info = db_manager.get_connection_info()
            
            print(f"  Pool Size:                 {conn_info['pool_size']:>8}")
            print(f"  Max Overflow:              {conn_info['max_overflow']:>8}")
            print(f"  SQL Echo:                  {'Yes' if conn_info['echo'] else 'No':>8}")
            
        except Exception as e:
            logger.warning(f"Could not retrieve performance stats: {e}")
    
    def cleanup_old_data(self) -> bool:
        """Clean up old and expired data"""
        try:
            print("🧹 Cleaning up old and expired data...")
            
            with get_db_context() as session:
                data_flow = DataFlowManager(session)
                
                cleanup_result = data_flow.cleanup_expired_data()
                
                print(f"  ✅ Expired trends removed:     {cleanup_result['expired_trends']:>6}")
                print(f"  ✅ Old drafts removed:         {cleanup_result['old_drafts']:>6}")
                print(f"  ✅ Stale analytics removed:    {cleanup_result['stale_analytics']:>6}")
                print(f"  ✅ Inactive rules deactivated: {cleanup_result['inactive_rules']:>6}")
                
                total_cleaned = sum(cleanup_result.values())
                print(f"\n🎯 Total items cleaned: {total_cleaned}")
                
                if total_cleaned > 0:
                    print("✅ Cleanup completed successfully")
                else:
                    print("ℹ️  No cleanup needed - database is clean")
                
                return True
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            logger.error(f"Data cleanup failed: {e}")
            return False
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create database backup"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_ideation_{timestamp}.sql"
            
            print(f"💾 Creating database backup: {backup_path}")
            
            # Extract connection details
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            pg_dump_cmd = [
                'pg_dump',
                '-h', parsed.hostname or 'localhost',
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', backup_path,
                '--verbose',
                '--clean',  # Include DROP statements
                '--create', # Include CREATE DATABASE
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            # Run pg_dump
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
                print(f"✅ Backup created successfully: {backup_path} ({file_size:.1f} MB)")
                logger.info(f"Database backup created: {backup_path}")
                return True
            else:
                print(f"❌ Backup failed: {result.stderr}")
                logger.error(f"pg_dump failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ pg_dump command not found. Please install PostgreSQL client tools.")
            logger.error("pg_dump command not available")
            return False
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            logger.error(f"Database backup failed: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_path):
                print(f"❌ Backup file not found: {backup_path}")
                return False
            
            print(f"🔄 Restoring database from: {backup_path}")
            print("⚠️  This will OVERWRITE the current database!")
            
            # Confirm restoration
            if not self._confirm_destructive_operation("restore"):
                print("❌ Database restoration cancelled")
                return False
            
            # Extract connection details
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            psql_cmd = [
                'psql',
                '-h', parsed.hostname or 'localhost',
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', backup_path,
                '--quiet'
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            # Run psql
            result = subprocess.run(
                psql_cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Database restored successfully")
                logger.info(f"Database restored from: {backup_path}")
                
                # Verify restoration with health check
                if health_check():
                    print("✅ Database health check passed after restoration")
                    return True
                else:
                    print("⚠️  Database restored but health check failed")
                    return False
            else:
                print(f"❌ Restoration failed: {result.stderr}")
                logger.error(f"psql restore failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ psql command not found. Please install PostgreSQL client tools.")
            logger.error("psql command not available")
            return False
        except Exception as e:
            print(f"❌ Restoration failed: {e}")
            logger.error(f"Database restoration failed: {e}")
            return False
    
    def migrate_database(self) -> bool:
        """Run database migrations"""
        try:
            print("🔄 Running database migrations...")
            
            # Check current database state
            if not health_check():
                print("❌ Database is not accessible for migration")
                return False
            
            with get_db_context() as session:
                # Get current schema version (if migration tracking exists)
                migration_version = self._get_migration_version(session)
                print(f"Current migration version: {migration_version}")
                
                migrations_applied = 0
                
                # Apply any pending migrations
                migrations = self._get_pending_migrations(migration_version)
                
                if not migrations:
                    print("✅ No pending migrations")
                    return True
                
                print(f"Found {len(migrations)} pending migrations")
                
                for migration in migrations:
                    try:
                        print(f"  Applying migration: {migration['name']}")
                        self._apply_migration(session, migration)
                        migrations_applied += 1
                        print(f"  ✅ Migration applied: {migration['name']}")
                    except Exception as e:
                        print(f"  ❌ Migration failed: {migration['name']} - {e}")
                        logger.error(f"Migration failed: {migration['name']} - {e}")
                        return False
                
                print(f"✅ {migrations_applied} migrations applied successfully")
                return True
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            logger.error(f"Database migration failed: {e}")
            return False
    
    def _get_migration_version(self, session) -> str:
        """Get current migration version"""
        try:
            # Check if migrations table exists
            result = session.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schema_migrations'
                );
            """)
            
            if not result.scalar():
                # Create migrations table
                session.execute("""
                    CREATE TABLE schema_migrations (
                        version VARCHAR(50) PRIMARY KEY,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                session.commit()
                return "0000_initial"
            
            # Get latest migration version
            result = session.execute("""
                SELECT version FROM schema_migrations 
                ORDER BY version DESC LIMIT 1
            """)
            
            latest = result.scalar()
            return latest or "0000_initial"
            
        except Exception as e:
            logger.warning(f"Could not determine migration version: {e}")
            return "0000_initial"
    
    def _get_pending_migrations(self, current_version: str) -> List[Dict[str, Any]]:
        """Get list of pending migrations"""
        # Define migrations here
        # In a real application, these would be loaded from migration files
        migrations = [
            {
                'name': '0001_add_indexes',
                'version': '0001_add_indexes',
                'sql': """
                    -- Add additional indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_founders_created_at ON founders(created_at);
                    CREATE INDEX IF NOT EXISTS idx_products_updated_at ON products(updated_at);
                    CREATE INDEX IF NOT EXISTS idx_trends_expires_at ON analyzed_trends(expires_at);
                """
            },
            {
                'name': '0002_add_constraints',
                'version': '0002_add_constraints',
                'sql': """
                    -- Add check constraints
                    ALTER TABLE analyzed_trends 
                    ADD CONSTRAINT check_relevance_score 
                    CHECK (niche_relevance_score >= 0.0 AND niche_relevance_score <= 1.0);
                    
                    ALTER TABLE post_analytics 
                    ADD CONSTRAINT check_engagement_rate 
                    CHECK (engagement_rate >= 0.0);
                """
            }
        ]
        
        # Filter migrations that haven't been applied
        pending = []
        for migration in migrations:
            if migration['version'] > current_version:
                pending.append(migration)
        
        return pending
    
    def _apply_migration(self, session, migration: Dict[str, Any]):
        """Apply a single migration"""
        try:
            # Execute migration SQL
            session.execute(migration['sql'])
            
            # Record migration as applied
            session.execute("""
                INSERT INTO schema_migrations (version) 
                VALUES (:version)
            """, {'version': migration['version']})
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
    
    def reset_database(self) -> bool:
        """Reset database (drop and recreate all tables)"""
        try:
            print("🔄 Resetting database...")
            print("⚠️  This will DELETE ALL DATA!")
            
            # Confirm reset
            if not self._confirm_destructive_operation("reset"):
                print("❌ Database reset cancelled")
                return False
            
            # Drop and recreate tables
            db_manager = get_db_manager()
            db_manager.drop_tables()
            db_manager.create_tables()
            
            print("✅ Database reset completed")
            logger.info("Database reset completed")
            
            # Verify reset
            if health_check():
                print("✅ Database health check passed after reset")
                return True
            else:
                print("❌ Database health check failed after reset")
                return False
                
        except Exception as e:
            print(f"❌ Database reset failed: {e}")
            logger.error(f"Database reset failed: {e}")
            return False
    
    def _confirm_destructive_operation(self, operation: str) -> bool:
        """Confirm destructive database operation"""
        try:
            confirmation = input(f"Type 'YES' to confirm {operation}: ")
            return confirmation.strip() == 'YES'
        except KeyboardInterrupt:
            return False
    
    def export_data(self, founder_email: str, output_path: Optional[str] = None) -> bool:
        """Export founder data to JSON file"""
        try:
            print(f"📤 Exporting data for founder: {founder_email}")
            
            with get_db_context() as session:
                # Find founder
                founder_repo = FounderRepository(session)
                founder = founder_repo.get_by_email(founder_email)
                
                if not founder:
                    print(f"❌ Founder not found: {founder_email}")
                    return False
                
                # Export data
                data_flow = DataFlowManager(session)
                export_data = data_flow.export_founder_data(str(founder.id))
                
                if not export_data:
                    print("❌ Failed to export founder data")
                    return False
                
                # Save to file
                if not output_path:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_email = founder_email.replace('@', '_').replace('.', '_')
                    output_path = f"export_{safe_email}_{timestamp}.json"
                
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                file_size = os.path.getsize(output_path) / 1024  # KB
                print(f"✅ Data exported successfully: {output_path} ({file_size:.1f} KB)")
                logger.info(f"Founder data exported: {founder_email} -> {output_path}")
                
                return True
                
        except Exception as e:
            print(f"❌ Data export failed: {e}")
            logger.error(f"Data export failed: {e}")
            return False
    
    def import_data(self, import_path: str) -> bool:
        """Import founder data from JSON file"""
        try:
            print(f"📥 Importing data from: {import_path}")
            
            if not os.path.exists(import_path):
                print(f"❌ Import file not found: {import_path}")
                return False
            
            # Load data
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate data structure
            if 'founder' not in import_data:
                print("❌ Invalid import file: missing founder data")
                return False
            
            with get_db_context() as session:
                data_flow = DataFlowManager(session)
                
                # Check if founder already exists
                founder_email = import_data['founder']['email']
                founder_repo = FounderRepository(session)
                existing_founder = founder_repo.get_by_email(founder_email)
                
                if existing_founder:
                    print(f"❌ Founder already exists: {founder_email}")
                    return False
                
                # Import founder
                founder_data = import_data['founder']
                founder_id = data_flow.process_founder_registration({
                    'email': founder_data['email'],
                    'hashed_password': founder_data.get('hashed_password', 'imported_password'),
                    'settings': founder_data.get('settings', {})
                })
                
                if not founder_id:
                    print("❌ Failed to import founder")
                    return False
                
                print(f"✅ Founder imported: {founder_email}")
                
                # Import products
                if 'products' in import_data:
                    for product_data in import_data['products']:
                        product_id = data_flow.process_product_information_entry(
                            founder_id, product_data
                        )
                        if product_id:
                            print(f"  ✅ Product imported: {product_data['name']}")
                
                # Import trends
                if 'analyzed_trends' in import_data:
                    trends_to_import = []
                    for trend_data in import_data['analyzed_trends']:
                        trends_to_import.append({
                            'topic_name': trend_data['topic_name'],
                            'niche_relevance_score': trend_data['relevance_score'],
                            'sentiment_scores': trend_data['sentiment_scores'],
                            'is_micro_trend': trend_data['is_micro_trend']
                        })
                    
                    if trends_to_import:
                        trend_ids = data_flow.store_analyzed_trends(founder_id, trends_to_import)
                        print(f"  ✅ {len(trend_ids)} trends imported")
                
                print("✅ Data import completed successfully")
                return True
                
        except Exception as e:
            print(f"❌ Data import failed: {e}")
            logger.error(f"Data import failed: {e}")
            return False
    
    def validate_database(self) -> bool:
        """Validate database integrity and consistency"""
        try:
            print("🔍 Validating database integrity...")
            
            if not health_check():
                print("❌ Database health check failed")
                return False
            
            validation_errors = []
            
            with get_db_context() as session:
                # Check for orphaned records
                print("  Checking for orphaned records...")
                
                # Check for products without founders
                orphaned_products = session.query(Product).filter(
                    ~Product.founder_id.in_(session.query(Founder.id))
                ).count()
                
                if orphaned_products > 0:
                    validation_errors.append(f"Found {orphaned_products} orphaned products")
                
                # Check for content drafts without founders
                orphaned_content = session.query(GeneratedContentDraft).filter(
                    ~GeneratedContentDraft.founder_id.in_(session.query(Founder.id))
                ).count()
                
                if orphaned_content > 0:
                    validation_errors.append(f"Found {orphaned_content} orphaned content drafts")
                
                # Check for analytics without founders
                orphaned_analytics = session.query(PostAnalytic).filter(
                    ~PostAnalytic.founder_id.in_(session.query(Founder.id))
                ).count()
                
                if orphaned_analytics > 0:
                    validation_errors.append(f"Found {orphaned_analytics} orphaned analytics records")
                
                # Check data consistency
                print("  Checking data consistency...")
                
                # Check for invalid engagement rates
                invalid_engagement = session.query(PostAnalytic).filter(
                    PostAnalytic.engagement_rate < 0
                ).count()
                
                if invalid_engagement > 0:
                    validation_errors.append(f"Found {invalid_engagement} invalid engagement rates")
                
                # Check for invalid relevance scores
                invalid_relevance = session.query(AnalyzedTrend).filter(
                    (AnalyzedTrend.niche_relevance_score < 0) | 
                    (AnalyzedTrend.niche_relevance_score > 1)
                ).count()
                
                if invalid_relevance > 0:
                    validation_errors.append(f"Found {invalid_relevance} invalid relevance scores")
                
                # Check for missing required fields
                print("  Checking required fields...")
                
                founders_no_email = session.query(Founder).filter(
                    (Founder.email.is_(None)) | (Founder.email == '')
                ).count()
                
                if founders_no_email > 0:
                    validation_errors.append(f"Found {founders_no_email} founders without email")
            
            # Report validation results
            if validation_errors:
                print("\n❌ Database validation failed:")
                for error in validation_errors:
                    print(f"  • {error}")
                logger.warning(f"Database validation failed: {validation_errors}")
                return False
            else:
                print("✅ Database validation passed - no issues found")
                logger.info("Database validation completed successfully")
                return True
                
        except Exception as e:
            print(f"❌ Database validation failed: {e}")
            logger.error(f"Database validation failed: {e}")
            return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Ideation Database Setup and Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python database_setup.py create                 # Create database and tables
  python database_setup.py test                   # Run connectivity tests
  python database_setup.py demo                   # Run comprehensive demo
  python database_setup.py stats                  # Show database statistics
  python database_setup.py cleanup                # Clean up old data
  python database_setup.py backup                 # Create database backup
  python database_setup.py restore backup.sql     # Restore from backup
  python database_setup.py migrate                # Run database migrations
  python database_setup.py reset                  # Reset database (DANGEROUS!)
  python database_setup.py export user@email.com  # Export user data
  python database_setup.py import data.json       # Import user data
  python database_setup.py validate               # Validate database integrity
        """
    )
    
    parser.add_argument(
        'command',
        choices=[
            'create', 'test', 'demo', 'stats', 'cleanup', 'backup', 
            'restore', 'migrate', 'reset', 'export', 'import', 'validate'
        ],
        help='Command to execute'
    )
    
    parser.add_argument(
        'target',
        nargs='?',
        help='Target for command (backup file, email, etc.)'
    )
    
    parser.add_argument(
        '--database-url',
        help='Database connection URL (overrides config)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path for export operations'
    )
    
    args = parser.parse_args()
    
    # Initialize setup manager
    setup_manager = DatabaseSetupManager(
        database_url=args.database_url
    )
    
    # Execute command
    success = False
    
    try:
        if args.command == 'create':
            success = setup_manager.create_database()
            
        elif args.command == 'test':
            success = setup_manager.test_database()
            
        elif args.command == 'demo':
            success = setup_manager.run_demo()
            
        elif args.command == 'stats':
            success = setup_manager.show_stats()
            
        elif args.command == 'cleanup':
            success = setup_manager.cleanup_old_data()
            
        elif args.command == 'backup':
            success = setup_manager.backup_database(args.target)
            
        elif args.command == 'restore':
            if not args.target:
                print("❌ Restore command requires backup file path")
                sys.exit(1)
            success = setup_manager.restore_database(args.target)
            
        elif args.command == 'migrate':
            success = setup_manager.migrate_database()
            
        elif args.command == 'reset':
            success = setup_manager.reset_database()
            
        elif args.command == 'export':
            if not args.target:
                print("❌ Export command requires founder email")
                sys.exit(1)
            success = setup_manager.export_data(args.target, args.output)
            
        elif args.command == 'import':
            if not args.target:
                print("❌ Import command requires data file path")
                sys.exit(1)
            success = setup_manager.import_data(args.target)
            
        elif args.command == 'validate':
            success = setup_manager.validate_database()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        sys.exit(1)


if __name__ == '__main__':
    main()
