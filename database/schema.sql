-- Ideation Database Schema
-- PostgreSQL DDL for initial database setup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Founders table
CREATE TABLE founders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_founders_email ON founders(email);

-- Products table  
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    founder_id UUID NOT NULL REFERENCES founders(id) ON DELETE CASCADE,
    product_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    core_values TEXT,
    target_audience_description TEXT NOT NULL,
    niche_definition JSONB NOT NULL,
    seo_keywords TEXT,
    website_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_products_founder_id ON products(founder_id);

-- Twitter credentials table
CREATE TABLE twitter_credentials (
    founder_id UUID PRIMARY KEY REFERENCES founders(id) ON DELETE CASCADE,
    twitter_user_id VARCHAR(50) NOT NULL,
    screen_name VARCHAR(50) NOT NULL,
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    last_validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_twitter_credentials_user_id ON twitter_credentials(twitter_user_id);

-- Raw trends tracking table
CREATE TABLE tracked_trends_raw (
    id BIGSERIAL PRIMARY KEY,
    trend_source_id VARCHAR(100),
    name VARCHAR(200) NOT NULL,
    location_woeid VARCHAR(20),
    volume INTEGER,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tracked_trends_source_id ON tracked_trends_raw(trend_source_id);
CREATE INDEX idx_tracked_trends_location ON tracked_trends_raw(location_woeid);

-- Analyzed trends table
CREATE TABLE analyzed_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    founder_id UUID NOT NULL REFERENCES founders(id) ON DELETE CASCADE,
    trend_source_id VARCHAR(100),
    topic_name VARCHAR(200) NOT NULL,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    niche_relevance_score NUMERIC(3,2) NOT NULL,
    sentiment_scores JSONB NOT NULL,
    extracted_pain_points TEXT,
    common_questions TEXT,
    discussion_focus_points TEXT,
    is_micro_trend BOOLEAN DEFAULT FALSE,
    trend_velocity_score NUMERIC,
    trend_potential_score NUMERIC,
    example_tweets_json JSONB,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_analyzed_trends_founder_id ON analyzed_trends(founder_id);
CREATE INDEX idx_analyzed_trends_topic_name ON analyzed_trends(topic_name);
CREATE INDEX idx_analyzed_trends_founder_micro ON analyzed_trends(founder_id, is_micro_trend);
CREATE INDEX idx_analyzed_trends_analyzed_at ON analyzed_trends(analyzed_at);
CREATE INDEX idx_analyzed_trends_potential_score ON analyzed_trends(trend_potential_score);

-- Generated content drafts table (includes scheduling functionality)
CREATE TABLE generated_content_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    founder_id UUID NOT NULL REFERENCES founders(id) ON DELETE CASCADE,
    analyzed_trend_id UUID REFERENCES analyzed_trends(id) ON DELETE SET NULL,
    source_tweet_id_for_reply VARCHAR(50),
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('tweet', 'reply', 'quote_tweet')),
    generated_text TEXT NOT NULL,
    seo_suggestions JSONB,
    edited_text TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending_review' 
        CHECK (status IN ('pending_review', 'approved', 'rejected', 'scheduled', 'posted', 'error')),
    ai_generation_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Scheduling fields (merged from scheduled_content)
    scheduled_post_time TIMESTAMP WITH TIME ZONE,
    posted_tweet_id VARCHAR(50),
    platform VARCHAR(20) DEFAULT 'twitter',
    priority INTEGER DEFAULT 5,
    
    -- Error handling fields
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Publishing details
    posted_at TIMESTAMP WITH TIME ZONE,
    tags JSONB DEFAULT '[]'::jsonb,
    created_by UUID REFERENCES founders(id)
);

CREATE INDEX idx_content_drafts_founder_id ON generated_content_drafts(founder_id);
CREATE INDEX idx_content_drafts_status ON generated_content_drafts(status);
CREATE INDEX idx_content_drafts_status_created ON generated_content_drafts(status, created_at);
CREATE INDEX idx_content_drafts_scheduled_time ON generated_content_drafts(scheduled_post_time);
CREATE INDEX idx_content_drafts_posted_tweet_id ON generated_content_drafts(posted_tweet_id);
CREATE INDEX idx_content_drafts_founder_status ON generated_content_drafts(founder_id, status);

-- Automation rules table
CREATE TABLE automation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    founder_id UUID NOT NULL REFERENCES founders(id) ON DELETE CASCADE,
    rule_name VARCHAR(100) NOT NULL,
    trigger_conditions JSONB NOT NULL,
    action_to_take JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0
);

CREATE INDEX idx_automation_rules_founder_id ON automation_rules(founder_id);
CREATE INDEX idx_automation_rules_is_active ON automation_rules(is_active);

-- Post analytics table
CREATE TABLE post_analytics (
    posted_tweet_id VARCHAR(50) PRIMARY KEY,
    founder_id UUID NOT NULL REFERENCES founders(id) ON DELETE CASCADE,
    content_draft_id UUID REFERENCES generated_content_drafts(id) ON DELETE SET NULL,
    impressions INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    quote_tweets INTEGER DEFAULT 0,
    link_clicks INTEGER DEFAULT 0,
    profile_visits_from_tweet INTEGER DEFAULT 0,
    engagement_rate NUMERIC,
    posted_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_post_analytics_founder_id ON post_analytics(founder_id);
CREATE INDEX idx_post_analytics_founder_posted ON post_analytics(founder_id, posted_at);
CREATE INDEX idx_post_analytics_engagement_rate ON post_analytics(engagement_rate);

-- Update triggers for timestamp fields
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ language 'plpgsql';

CREATE TRIGGER update_founders_updated_at BEFORE UPDATE ON founders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_twitter_credentials_updated_at BEFORE UPDATE ON twitter_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_generated_content_drafts_updated_at BEFORE UPDATE ON generated_content_drafts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_post_analytics_updated_at BEFORE UPDATE ON post_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();