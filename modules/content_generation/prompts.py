"""Prompt engineering and templates for content generation"""
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from .models import ContentType, ContentGenerationContext, BrandVoice, PromptTemplate, ContentGenerationRequest, GenerationMode

class ContentPromptTemplates:
    """Collection of prompt templates for different content types"""
    
    # Base system prompts
    SYSTEM_PROMPTS = {
        ContentType.TWEET: """You are an expert social media content creator specializing in Twitter. 
Your goal is to create engaging, authentic tweets that drive meaningful engagement while staying true to the brand voice.
Always consider the target audience and current trends when crafting content.""",
        
        ContentType.REPLY: """You are an expert at crafting thoughtful, engaging replies on Twitter.
Your replies should add value to the conversation, show genuine interest, and maintain a conversational tone.
Focus on building relationships and encouraging further discussion.""",
        
        ContentType.THREAD: """You are an expert at creating compelling Twitter threads that tell a story or explain complex topics.
Each tweet in the thread should flow naturally to the next while being self-contained enough to stand alone.
Use clear, concise language and maintain reader interest throughout.""",
        
        ContentType.QUOTE_TWEET: """You are an expert at creating insightful quote tweets that add meaningful commentary.
Your quote should provide a fresh perspective, ask a thought-provoking question, or add valuable context to the original tweet."""
    }
    
    # Content generation templates
    CONTENT_TEMPLATES = {
        ContentType.TWEET: {
            "trend_based": """Create an engaging tweet about the trending topic: {trend_name}

Context:
- Product: {product_name} - {product_description}
- Target Audience: {target_audience}
- Brand Voice: {brand_tone} and {brand_style}
- Key Pain Points from Trend: {pain_points}
- Common Questions: {questions}

Brand Guidelines:
- Tone: {brand_tone}
- Personality: {personality_traits}
- Avoid: {avoid_words}

Requirements:
- Maximum 280 characters
- Address at least one pain point
- Include a call-to-action or thought-provoking question
- Match the brand voice
- Make it shareable and engaging
- Focus on authentic value delivery

Generate a tweet that connects the trend to your product's value proposition while maintaining authenticity.""",

            "product_focused": """Create a compelling tweet highlighting {product_name}'s key benefits.

Product Details:
- Name: {product_name}
- Description: {product_description}
- Core Values: {core_values}
- Key Features: {key_features}
- Target Audience: {target_audience}

Brand Voice:
- Tone: {brand_tone}
- Style: {brand_style}
- Personality: {personality_traits}

Recent Successful Content Patterns:
{successful_patterns}

Requirements:
- Maximum 280 characters
- Highlight unique value proposition
- Include emotional appeal
- End with clear call-to-action
- Avoid sounding too promotional
- Focus on user benefits over features

Generate a tweet that naturally showcases your product's benefits.""",

            "educational": """Create an educational tweet that provides value to {target_audience}.

Topic Context:
- Main Topic: {trend_name}
- Key Insights: {key_insights}
- Common Questions: {questions}
- Pain Points: {pain_points}

Brand Context:
- Product: {product_name}
- Expertise Area: {expertise_area}
- Brand Voice: {brand_tone}

Requirements:
- Maximum 280 characters
- Share actionable insight or tip
- Position brand as helpful expert
- Include relevant emoji for engagement
- End with question to encourage replies
- Make content easily shareable

Generate an educational tweet that establishes thought leadership.""",

            "viral_focused": """Create a viral-focused tweet designed for maximum engagement about {trend_name}.

Viral Elements to Include:
- Controversial but respectful take
- Universal truth or insight
- Emotional hook (surprise, humor, inspiration)
- Conversational tone
- Question or discussion starter

Context:
- Product: {product_name}
- Target Audience: {target_audience}
- Brand Voice: {brand_tone}
- Trending Topic: {trend_name}

Requirements:
- Maximum 280 characters
- Strong emotional hook in first line
- Include relatable experience
- End with engaging question
- Avoid being overly promotional
- Focus on shareability and discussion

Generate a tweet optimized for viral engagement while maintaining brand authenticity.""",

            "engagement_optimized": """Create an engagement-optimized tweet about {trend_name}.

Engagement Drivers:
- Ask compelling questions
- Share personal insights
- Create discussion starters
- Use conversational language
- Include call-to-action for responses

Brand Context:
- Product: {product_name}
- Voice: {brand_tone}
- Audience: {target_audience}
- Expertise: {expertise_area}

Requirements:
- Maximum 280 characters
- Start with hook or question
- Share genuine insight
- Encourage replies and discussion
- Use authentic, conversational tone
- Make audience feel heard

Generate a tweet designed to maximize meaningful engagement."""
        },
        
        ContentType.REPLY: {
            "supportive": """Craft a supportive reply to this tweet: "{original_tweet}"

Your Brand Context:
- Product: {product_name}
- Expertise: {expertise_area}
- Brand Voice: {brand_tone}

Guidelines:
- Be genuinely helpful and supportive
- Add value to the conversation
- Share relevant experience or insight
- Keep it conversational and authentic
- Don't be promotional unless highly relevant
- Maximum 280 characters

Generate a reply that builds relationships and shows genuine interest.""",

            "expert_insight": """Create an expert reply adding valuable insight to: "{original_tweet}"

Your Expertise Context:
- Product/Service: {product_name}
- Industry Knowledge: {expertise_area}
- Relevant Experience: {relevant_experience}
- Brand Voice: {brand_tone}

Requirements:
- Share specific, actionable insight
- Reference relevant experience or data
- Maintain conversational tone
- Add unique perspective
- Include question to continue conversation
- Maximum 280 characters

Generate a reply that positions you as a knowledgeable industry expert."""
        },
        
        ContentType.THREAD: {
            "story_telling": """Create a compelling Twitter thread telling a story about {story_topic}.

Story Elements:
- Main Topic: {story_topic}
- Key Message: {key_message}
- Target Audience: {target_audience}
- Supporting Details: {supporting_details}

Brand Context:
- Product: {product_name}
- Brand Voice: {brand_tone}
- Core Values: {core_values}

Thread Structure:
1. Hook tweet (grab attention)
2. Problem/situation setup
3. Development/journey (2-3 tweets)
4. Resolution/lesson learned
5. Call-to-action or question

Requirements:
- Each tweet maximum 280 characters
- Strong opening hook
- Natural flow between tweets
- Include personal or customer story
- End with clear takeaway
- Maximum 7 tweets total

Generate a thread that engages readers and builds connection with your brand.""",

            "educational_breakdown": """Create an educational Twitter thread breaking down {complex_topic}.

Topic Details:
- Main Topic: {complex_topic}
- Key Points to Cover: {key_points}
- Target Audience: {target_audience}
- Complexity Level: {complexity_level}

Brand Authority:
- Product: {product_name}
- Expertise Area: {expertise_area}
- Brand Voice: {brand_tone}

Thread Structure:
1. Introduction tweet (why this matters)
2. Break down into 3-5 digestible points
3. Practical examples or applications
4. Common mistakes to avoid
5. Summary and call-to-action

Requirements:
- Each tweet maximum 280 characters
- Use numbered format (1/7, 2/7, etc.)
- Include relevant emojis for readability
- Make complex concepts simple
- End with question for engagement
- Maximum 8 tweets total

Generate an educational thread that establishes thought leadership."""
        }
    }

class PromptEngine:
    """Engine for generating and managing content prompts"""
    
    def __init__(self):
        self.templates = ContentPromptTemplates()
    
    def generate_prompt(self, request: ContentGenerationRequest, 
                       context: ContentGenerationContext, 
                       prompt_type: str = "default") -> str:
        """Generate a complete prompt for content generation"""
        
        # Extract content type from request
        content_type = request.content_type
        
        # Get system prompt
        system_prompt = self.templates.SYSTEM_PROMPTS.get(content_type, "")
        
        # Get content template
        content_templates = self.templates.CONTENT_TEMPLATES.get(content_type, {})
        
        # Determine best template based on context and request
        if prompt_type == "default":
            prompt_type = self._determine_optimal_template(content_type, context, request)
        
        template = content_templates.get(prompt_type)
        if not template:
            template = self._get_fallback_template(content_type)
        
        # Fill template with context data
        filled_template = self._fill_template(template, context, request)
        
        # Combine system prompt and content prompt
        full_prompt = f"{system_prompt}\n\n{filled_template}"
        
        return full_prompt
    
    def _determine_optimal_template(self, content_type: ContentType, 
                                  context: ContentGenerationContext,
                                  request: ContentGenerationRequest) -> str:
        """Determine the best template based on context and request"""
        
        # Check generation mode first
        if request.generation_mode == GenerationMode.VIRAL_FOCUSED:
            if content_type == ContentType.TWEET:
                return "viral_focused"
            else:
                return "supportive"
        elif request.generation_mode == GenerationMode.ENGAGEMENT_OPTIMIZED:
            if content_type == ContentType.TWEET:
                return "engagement_optimized"
            else:
                return "expert_insight"
        elif request.generation_mode == GenerationMode.BRAND_FOCUSED:
            return "product_focused" if content_type == ContentType.TWEET else "supportive"
        elif request.generation_mode == GenerationMode.TREND_BASED:
            return "trend_based" if context.trend_info else "educational"
        
        # Default template selection
        if content_type == ContentType.TWEET:
            # If we have trend info, use trend-based template
            if context.trend_info:
                return "trend_based"
            # If we have successful patterns, use product-focused
            elif context.successful_patterns:
                return "product_focused"
            # Default to educational
            else:
                return "educational"
                
        elif content_type == ContentType.REPLY:
            # Determine if this should be supportive or expert insight
            if context.content_preferences.get("expert_positioning", False):
                return "expert_insight"
            else:
                return "supportive"
                
        elif content_type == ContentType.THREAD:
            # Check if we have story elements
            if context.content_preferences.get("storytelling", True):
                return "story_telling"
            else:
                return "educational_breakdown"
        
        return "default"
    
    def _fill_template(self, template: str, context: ContentGenerationContext, 
                      request: ContentGenerationRequest) -> str:
        """Fill template placeholders with context data"""
        
        # Extract product info
        product_info = context.product_info
        trend_info = context.trend_info or {}
        brand_voice = context.brand_voice
        
        # Prepare replacement dictionary
        replacements = {
            # Product information
            "product_name": product_info.get("name", "Our Product"),
            "product_description": product_info.get("description", ""),
            "core_values": ", ".join(product_info.get("core_values", [])),
            "key_features": ", ".join(product_info.get("key_features", [])),
            "target_audience": context.target_audience or "professionals",
            
            # Trend information
            "trend_name": trend_info.get("topic_name", "current trends"),
            "pain_points": ", ".join(trend_info.get("pain_points", [])),
            "questions": ", ".join(trend_info.get("questions", [])),
            "key_insights": ", ".join(trend_info.get("focus_points", [])),
            
            # Brand voice
            "brand_tone": brand_voice.tone,
            "brand_style": brand_voice.style,
            "personality_traits": ", ".join(brand_voice.personality_traits),
            "avoid_words": ", ".join(brand_voice.avoid_words),
            
            # Additional context
            "expertise_area": product_info.get("industry_category", "technology"),
            "successful_patterns": self._format_successful_patterns(context.successful_patterns),
            "relevant_experience": product_info.get("brand_story", ""),
            
            # Dynamic content
            "story_topic": trend_info.get("topic_name", "industry insights"),
            "key_message": product_info.get("tagline", ""),
            "supporting_details": ", ".join(trend_info.get("focus_points", [])),
            "complex_topic": trend_info.get("topic_name", "industry best practices"),
            "key_points": ", ".join(trend_info.get("pain_points", [])),
            "complexity_level": "intermediate",
            
            # Handle original tweet for replies
            "original_tweet": context.content_preferences.get("original_tweet", "a recent industry discussion"),
            
            # Request-specific information
            "founder_id": request.founder_id,
            "generation_mode": request.generation_mode.value,
            "custom_instructions": request.custom_prompt or "No additional instructions"
        }
        
        # Fill template
        filled_template = template
        for key, value in replacements.items():
            placeholder = "{" + key + "}"
            filled_template = filled_template.replace(placeholder, str(value))
        
        return filled_template
    
    def _format_successful_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format successful content patterns for inclusion in prompts"""
        if not patterns:
            return "No specific patterns identified yet."
        
        formatted = []
        for pattern in patterns[:3]:  # Use top 3 patterns
            content_type = pattern.get("content_type", "tweet")
            engagement = pattern.get("engagement_rate", 0)
            topic = pattern.get("topic", "general")
            formatted.append(f"- {content_type.title()} about {topic} (engagement: {engagement:.1%})")
        
        return "\n".join(formatted)
    
    def _get_fallback_template(self, content_type: ContentType) -> str:
        """Get fallback template when specific template not found"""
        fallback_templates = {
            ContentType.TWEET: """Create an engaging tweet for {product_name}.

Target Audience: {target_audience}
Brand Voice: {brand_tone}
Core Message: Share value and engage your audience

Requirements:
- Maximum 280 characters
- Include call-to-action
- Match brand voice
- Be authentic and engaging
- Focus on user value""",

            ContentType.REPLY: """Create a helpful reply that adds value to the conversation.

Brand Context: {product_name}
Brand Voice: {brand_tone}

Requirements:
- Be conversational and authentic
- Add genuine value
- Maximum 280 characters
- Encourage further discussion""",

            ContentType.THREAD: """Create a Twitter thread about {trend_name}.

Brand: {product_name}
Voice: {brand_tone}
Audience: {target_audience}

Structure:
1. Hook tweet
2. Main content (3-5 tweets)
3. Call-to-action

Requirements:
- Each tweet max 280 characters
- Number tweets (1/6, 2/6, etc.)
- Maintain consistent voice"""
        }
        
        return fallback_templates.get(content_type, "Create engaging content for your audience.")
    
    def create_custom_prompt(self, instruction: str, context: ContentGenerationContext) -> str:
        """Create a custom prompt from user instruction"""
        
        base_context = f"""
Product: {context.product_info.get('name', 'Our Product')}
Target Audience: {context.target_audience}
Brand Voice: {context.brand_voice.tone} and {context.brand_voice.style}
"""
        
        if context.trend_info:
            base_context += f"\nTrending Topic: {context.trend_info.get('topic_name', '')}"
            base_context += f"\nKey Insights: {', '.join(context.trend_info.get('pain_points', []))}"
        
        return f"{base_context}\n\nCustom Instruction: {instruction}\n\nCreate content that follows the instruction while maintaining brand voice and engaging the target audience."
    
    def optimize_prompt_for_llm(self, prompt: str, llm_provider: str) -> str:
        """Optimize prompt for specific LLM provider"""
        
        if llm_provider.lower() == "openai":
            # OpenAI likes clear structure and explicit instructions
            return f"Please follow these instructions carefully:\n\n{prompt}\n\nProvide only the requested content without additional commentary."
        
        elif llm_provider.lower() == "claude":
            # Claude prefers conversational, detailed prompts
            return f"I need your help creating social media content. Here's the context:\n\n{prompt}\n\nPlease create engaging content that meets all the requirements."
        
        elif llm_provider.lower() == "local":
            # Local models often work better with simpler, more direct prompts
            simplified = re.sub(r'\n\s*\n', '\n', prompt)  # Remove extra newlines
            return f"Task: {simplified}\n\nGenerate the requested content:"
        
        return prompt