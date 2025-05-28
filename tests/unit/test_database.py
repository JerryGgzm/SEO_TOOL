import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

from database import init_database, get_db_session, DataFlowManager
from database.models import Founder, Product, AnalyzedTrend
from database.repositories import FounderRepository, ProductRepository

class TestFounderRepository:
    @pytest.fixture
    def db_session(self):
        # Use in-memory SQLite for testing
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base
        
        engine = create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()
    
    @pytest.fixture
    def founder_repo(self, db_session):
        return FounderRepository(db_session)
    
    def test_create_founder(self, founder_repo):
        """Test founder creation"""
        founder = founder_repo.create_founder(
            email='test@example.com',
            hashed_password='hash123',
            settings={'theme': 'dark'}
        )
        
        assert founder is not None
        assert founder.email == 'test@example.com'
        assert founder.settings == {'theme': 'dark'}
    
    def test_get_founder_by_email(self, founder_repo):
        """Test founder retrieval by email"""
        # Create founder
        founder_repo.create_founder(
            email='test@example.com',
            hashed_password='hash123'
        )
        
        # Retrieve founder
        found_founder = founder_repo.get_by_email('test@example.com')
        assert found_founder is not None
        assert found_founder.email == 'test@example.com'
    
    def test_duplicate_email_fails(self, founder_repo):
        """Test that duplicate emails are rejected"""
        founder_repo.create_founder(
            email='test@example.com',
            hashed_password='hash123'
        )
        
        duplicate = founder_repo.create_founder(
            email='test@example.com',
            hashed_password='hash456'
        )
        
        assert duplicate is None

class TestDataFlowManager:
    @pytest.fixture
    def db_session(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base
        
        engine = create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()
    
    @pytest.fixture
    def data_flow(self, db_session):
        return DataFlowManager(db_session)
    
    def test_founder_registration_flow(self, data_flow):
        """Test complete founder registration flow"""
        registration_data = {
            'email': 'founder@startup.com',
            'hashed_password': 'secure_hash_123',
            'settings': {'notifications': True}
        }
        
        founder_id = data_flow.process_founder_registration(registration_data)
        
        assert founder_id is not None
        assert len(founder_id) > 0
    
    def test_product_information_entry(self, data_flow):
        """Test product information entry flow"""
        # First create founder
        founder_id = data_flow.process_founder_registration({
            'email': 'founder@startup.com',
            'hashed_password': 'hash123'
        })
        
        # Then add product
        product_data = {
            'product_name': 'AI Assistant',
            'description': 'An AI-powered productivity tool',
            'target_audience_description': 'Remote workers and freelancers',
            'niche_definition': {
                'keywords': ['AI', 'productivity', 'automation'],
                'tags': ['#AI', '#productivity']
            },
            'core_values': ['innovation', 'user-friendly']
        }
        
        product_id = data_flow.process_product_information_entry(founder_id, product_data)
        
        assert product_id is not None
        
        # Verify context retrieval
        context = data_flow.get_founder_context_for_trend_analysis(founder_id)
        assert context is not None
        assert len(context['products']) == 1
        assert 'AI' in context['all_keywords']