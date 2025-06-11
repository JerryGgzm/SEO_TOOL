"""Review Optimization Module - Demo

This demo showcases the key features of the review optimization module,
including content review workflows, batch operations, and analytics.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Mock imports for demo purposes
class MockDataFlowManager:
    """Mock DataFlowManager for demo"""
    
    def __init__(self):
        self.drafts = {}
        self.next_id = 1
    
    def create_mock_draft(self, founder_id: str, content: str, content_type: str = "trend_analysis"):
        """Create a mock draft for demo"""
        draft_id = f"draft_{self.next_id}"
        self.next_id += 1
        
        draft_data = {
            'id': draft_id,
            'founder_id': founder_id,
            'content_type': content_type,
            'generated_text': content,
            'current_content': content,
            'status': 'pending_review',
            'priority': 'medium',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'tags': [],
            'analyzed_trend_id': f"trend_{self.next_id}",
            'ai_generation_metadata': {'quality_score': 0.75 + (self.next_id % 3) * 0.1},
            'seo_suggestions': {'keywords': ['AI', 'startup'], 'hashtags': ['#AI', '#startup']},
            'quality_score': 0.75 + (self.next_id % 3) * 0.1,
            'edit_history': [],
            'review_feedback': None,
            'reviewed_at': None,
            'reviewer_id': None,
            'review_decision': None
        }
        
        self.drafts[draft_id] = draft_data
        return draft_id
    
    def get_pending_content_drafts(self, founder_id: str, limit: int, offset: int):
        """Get pending drafts"""
        pending = [d for d in self.drafts.values() 
                  if d['founder_id'] == founder_id and d['status'] == 'pending_review']
        return pending[offset:offset + limit]
    
    def get_content_draft_by_id(self, draft_id: str):
        """Get draft by ID"""
        return self.drafts.get(draft_id)
    
    def update_content_draft(self, draft_id: str, update_data: Dict[str, Any]):
        """Update draft"""
        if draft_id in self.drafts:
            self.drafts[draft_id].update(update_data)
            return True
        return False


class MockContentGenerationService:
    """Mock content generation service"""
    
    async def regenerate_content_with_seo_feedback(self, draft_id: str, founder_id: str, 
                                                  feedback: str, preferences: Dict[str, Any]):
        """Mock content regeneration"""
        return [f"regenerated_{draft_id}"]


class MockAnalyticsCollector:
    """Mock analytics collector"""
    
    async def record_event(self, event_data: Dict[str, Any]):
        """Mock event recording"""
        print(f"📊 Analytics Event: {event_data['event_type']}")


# Import the actual review optimization modules
try:
    from modules.review_optimization.service import ReviewOptimizationService
    from modules.review_optimization.models import (
        ReviewDecision, DraftStatus, ContentPriority,
        ReviewDecisionRequest, BatchReviewRequest, BatchReviewDecision,
        ContentRegenerationRequest, StatusUpdateRequest
    )
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    print("⚠️  Review optimization modules not available. Running demo with mock data only.")


class ReviewOptimizationDemo:
    """Demo class for review optimization features"""
    
    def __init__(self):
        self.mock_data_manager = MockDataFlowManager()
        self.mock_content_service = MockContentGenerationService()
        self.mock_analytics = MockAnalyticsCollector()
        
        if MODULES_AVAILABLE:
            self.service = ReviewOptimizationService(
                data_flow_manager=self.mock_data_manager,
                content_generation_service=self.mock_content_service,
                analytics_collector=self.mock_analytics
            )
        
        self.founder_id = "demo_founder_123"
        self.demo_content = [
            {
                "content": "🚀 5 Key Insights for AI Startups\n\nAfter conducting in-depth market research, I've discovered several important AI startup opportunities:\n\n1. Vertical AI applications still have enormous potential\n2. Data quality is more important than algorithm complexity\n3. User experience is the key to AI product success\n\nWhich field do you think has the most potential?\n\n#AI #Startup #TechTrends",
                "type": "trend_analysis"
            },
            {
                "content": "💡 Sharing a Practical Product Growth Tip\n\nYesterday I chatted with a successful entrepreneur and learned a great growth strategy...\n\nThe key is to focus on user value, not the number of features.\n\n#Product #Growth #StartupExperience",
                "type": "experience_sharing"
            },
            {
                "content": "📈 Latest Market Report Shows: AI Investment Up 150% YoY in Q1 2024\n\nWhat trends does this number reflect? As entrepreneurs, how should we seize this opportunity?\n\n#MarketAnalysis #AIInvestment #StartupOpportunity",
                "type": "news_commentary"
            }
        ]
    
    def print_header(self, title: str):
        """Print demo section header"""
        print(f"\n{'='*60}")
        print(f"🎯 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str):
        """Print demo step"""
        print(f"\n📋 {step}")
        print("-" * 40)
    
    async def setup_demo_data(self):
        """Setup demo data"""
        self.print_header("Setting Up Demo Data")
        
        # Create demo drafts
        self.draft_ids = []
        for i, content_data in enumerate(self.demo_content):
            draft_id = self.mock_data_manager.create_mock_draft(
                self.founder_id, 
                content_data["content"], 
                content_data["type"]
            )
            self.draft_ids.append(draft_id)
            print(f"✅ Created draft {draft_id}: {content_data['type']}")
        
        print(f"\n🎉 Successfully created {len(self.draft_ids)} demo drafts")
    
    async def demo_get_pending_drafts(self):
        """Demo getting pending drafts"""
        self.print_header("Getting Pending Drafts")
        
        if not MODULES_AVAILABLE:
            print("⚠️  Modules not available, showing mock data")
            pending_drafts = self.mock_data_manager.get_pending_content_drafts(self.founder_id, 10, 0)
            for draft in pending_drafts:
                print(f"📄 Draft {draft['id']}: {draft['content_type']}")
                print(f"   Content preview: {draft['current_content'][:50]}...")
                print(f"   Quality score: {draft['quality_score']}")
            return
        
        self.print_step("Calling get_pending_drafts API")
        
        try:
            pending_drafts = await self.service.get_pending_drafts(self.founder_id, limit=5)
            
            print(f"📊 Found {len(pending_drafts)} pending drafts:")
            
            for draft in pending_drafts:
                print(f"\n📄 Draft ID: {draft.id}")
                print(f"   Type: {draft.content_type}")
                print(f"   Status: {draft.status.value}")
                print(f"   Priority: {draft.priority.value}")
                print(f"   Content preview: {draft.current_content[:50]}...")
                print(f"   Quality score: {draft.quality_score}")
                print(f"   Created: {draft.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_review_decisions(self):
        """Demo review decisions"""
        self.print_header("Review Decision Demo")
        
        if not MODULES_AVAILABLE or len(self.draft_ids) < 3:
            print("⚠️  Modules not available or insufficient data, showing simulated review process")
            self._simulate_review_decisions()
            return
        
        # Demo different types of decisions
        decisions = [
            {
                "draft_id": self.draft_ids[0],
                "decision": ReviewDecision.APPROVE,
                "feedback": "High quality content, ready for publication",
                "tags": ["AI", "startup", "insights"]
            },
            {
                "draft_id": self.draft_ids[1],
                "decision": ReviewDecision.EDIT_AND_APPROVE,
                "edited_content": "💡 Sharing a Practical Product Growth Tip\n\nYesterday I had an in-depth conversation with a successful entrepreneur and learned a very effective growth strategy:\n\n🎯 The key is to focus on core user value, not blindly stacking features.\n\nWhat challenges have you encountered in product growth? Feel free to share!\n\n#Product #Growth #StartupExperience #UserValue",
                "feedback": "Added more details and interactive elements, optimized formatting"
            },
            {
                "draft_id": self.draft_ids[2],
                "decision": ReviewDecision.REJECT,
                "feedback": "Content is too simple, needs more in-depth analysis and data support"
            }
        ]
        
        for i, decision_data in enumerate(decisions):
            self.print_step(f"Processing Review Decision {i+1}")
            
            try:
                request = ReviewDecisionRequest(**decision_data)
                
                print(f"📝 Draft: {decision_data['draft_id']}")
                print(f"🎯 Decision: {decision_data['decision'].value}")
                print(f"💬 Feedback: {decision_data['feedback']}")
                
                if decision_data['decision'] == ReviewDecision.EDIT_AND_APPROVE:
                    print(f"✏️  Edited content preview: {decision_data['edited_content'][:100]}...")
                
                success = await self.service.submit_review_decision(
                    decision_data['draft_id'], 
                    self.founder_id, 
                    request
                )
                
                if success:
                    print("✅ Review decision processed successfully")
                else:
                    print("❌ Review decision processing failed")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _simulate_review_decisions(self):
        """Simulate review decisions for demo"""
        decisions = [
            {"type": "APPROVE", "reason": "High quality content, ready for publication"},
            {"type": "EDIT_AND_APPROVE", "reason": "Ready for publication after minor edits"},
            {"type": "REJECT", "reason": "Needs more in-depth analysis"}
        ]
        
        for i, decision in enumerate(decisions):
            print(f"\n📝 Draft {i+1}:")
            print(f"   Decision: {decision['type']}")
            print(f"   Reason: {decision['reason']}")
            print("   ✅ Processing complete")
    
    async def demo_batch_review(self):
        """Demo batch review operations"""
        self.print_header("Batch Review Demo")
        
        if not MODULES_AVAILABLE:
            print("⚠️  Modules not available, showing simulated batch review")
            print("📦 Simulating batch review of 5 drafts:")
            for i in range(5):
                print(f"   📄 Draft {i+1}: Approved")
            return
        
        self.print_step("Creating Batch Review Request")
        
        # Create more demo drafts for batch review
        batch_draft_ids = []
        for i in range(3):
            content = f"Batch review demo content {i+1} - This is an in-depth analysis of AI technology development..."
            draft_id = self.mock_data_manager.create_mock_draft(
                self.founder_id, content, "batch_demo"
            )
            batch_draft_ids.append(draft_id)
        
        batch_decisions = [
            BatchReviewDecision(
                draft_id=batch_draft_ids[0],
                decision=ReviewDecision.APPROVE,
                feedback="Good content quality"
            ),
            BatchReviewDecision(
                draft_id=batch_draft_ids[1],
                decision=ReviewDecision.APPROVE,
                feedback="Suitable for publication"
            ),
            BatchReviewDecision(
                draft_id=batch_draft_ids[2],
                decision=ReviewDecision.REJECT,
                feedback="Needs more data support"
            )
        ]
        
        batch_request = BatchReviewRequest(decisions=batch_decisions)
        
        print(f"📦 Batch processing {len(batch_decisions)} review decisions:")
        for decision in batch_decisions:
            print(f"   📄 {decision.draft_id}: {decision.decision.value}")
        
        try:
            results = await self.service.submit_batch_review_decisions(
                self.founder_id, batch_request
            )
            
            print(f"\n📊 Batch review results:")
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            print(f"   ✅ Success: {success_count}/{total_count}")
            print(f"   ❌ Failed: {total_count - success_count}/{total_count}")
            
            for draft_id, success in results.items():
                status = "✅" if success else "❌"
                print(f"   {status} {draft_id}")
                
        except Exception as e:
            print(f"❌ Batch review error: {e}")
    
    async def demo_content_regeneration(self):
        """Demo content regeneration"""
        self.print_header("Content Regeneration Demo")
        
        if not MODULES_AVAILABLE or not self.draft_ids:
            print("⚠️  Modules not available, showing simulated regeneration")
            print("🔄 Simulating content regeneration:")
            print("   Original: 5 Key Insights for AI Startups...")
            print("   Regenerated: In-Depth AI Startup Analysis: 5 Core Insights and Practical Recommendations...")
            print("   ✅ Regeneration complete")
            return
        
        self.print_step("Requesting Content Regeneration")
        
        regeneration_request = ContentRegenerationRequest(
            feedback="Good direction, but needs more specific cases and data support, tone should be more professional",
            style_preferences={
                "tone": "professional",
                "length": "detailed",
                "include_examples": True
            },
            target_improvements=[
                "Add specific success cases",
                "Quote latest market data",
                "Include actionable recommendations"
            ],
            keep_elements=[
                "Core viewpoint structure",
                "Question-guided ending"
            ],
            avoid_elements=[
                "Overly colloquial expressions",
                "Unsupported claims"
            ]
        )
        
        draft_id = self.draft_ids[0]
        print(f"🎯 Regenerating draft: {draft_id}")
        print(f"💬 Feedback requirements: {regeneration_request.feedback}")
        print(f"🎨 Style preferences: {regeneration_request.style_preferences}")
        print(f"📈 Improvement targets: {regeneration_request.target_improvements}")
        
        try:
            result = await self.service.regenerate_content(
                draft_id, self.founder_id, regeneration_request
            )
            
            if result:
                print(f"\n✅ Regeneration successful!")
                print(f"📄 New content preview: {result.new_content[:150]}...")
                print(f"🔧 Improvements made: {result.improvements_made}")
                print(f"⭐ Quality score: {result.quality_score}")
            else:
                print("❌ Regeneration failed")
                
        except Exception as e:
            print(f"❌ Regeneration error: {e}")
    
    async def demo_analytics_and_insights(self):
        """Demo analytics and insights"""
        self.print_header("Analytics Reports and Insights")
        
        if not MODULES_AVAILABLE:
            self._simulate_analytics()
            return
        
        self.print_step("Getting Review Summary")
        
        try:
            summary = await self.service.get_review_summary(self.founder_id, days=30)
            
            print(f"📊 Review summary for past 30 days:")
            print(f"   📝 Pending: {summary.total_pending}")
            print(f"   ✅ Approved: {summary.total_approved}")
            print(f"   ❌ Rejected: {summary.total_rejected}")
            print(f"   ✏️  Edited: {summary.total_edited}")
            print(f"   ⭐ Average quality score: {summary.avg_quality_score:.2f}")
            print(f"   📈 Approval rate: {summary.approval_rate:.1f}%")
            print(f"   🏷️  Common tags: {summary.most_common_tags}")
            print(f"   ⚡ Review velocity: {summary.review_velocity:.1f} posts/day")
            
        except Exception as e:
            print(f"❌ Summary retrieval error: {e}")
        
        self.print_step("Getting Detailed Analytics Data")
        
        try:
            analytics = await self.service.get_review_analytics(self.founder_id, days=30)
            
            print(f"📈 Detailed analytics data (past {analytics.period_days} days):")
            print(f"   📊 Total reviews: {analytics.total_reviews}")
            print(f"   🎯 Decision breakdown: {analytics.decision_breakdown}")
            print(f"   📝 Content type breakdown: {analytics.content_type_breakdown}")
            print(f"   ⏱️  Average review time: {analytics.average_review_time_minutes:.1f} minutes")
            print(f"   📉 Top rejection reasons: {analytics.top_rejection_reasons}")
            print(f"   🚀 Productivity metrics: {analytics.productivity_metrics}")
            
        except Exception as e:
            print(f"❌ Analytics data retrieval error: {e}")
    
    def _simulate_analytics(self):
        """Simulate analytics for demo"""
        print("📊 Simulated analytics report:")
        print("   📝 Pending: 5")
        print("   ✅ Approved: 23")
        print("   ❌ Rejected: 2")
        print("   ✏️  Edited: 8")
        print("   ⭐ Average quality score: 0.84")
        print("   📈 Approval rate: 91.2%")
        print("   🏷️  Common tags: ['AI', 'startup', 'technology', 'product', 'growth']")
        print("   ⚡ Review velocity: 2.3 posts/day")
        
        print("\n📈 Productivity metrics:")
        print("   🎯 Review efficiency: Very high")
        print("   ✅ Quality trend: Improving")
        print("   📊 Edit rate: 21%")
        print("   🔄 Regeneration rate: 5%")
    
    async def demo_workflow_scenarios(self):
        """Demo real-world workflow scenarios"""
        self.print_header("Real-World Workflow Scenario Demo")
        
        scenarios = [
            {
                "name": "Morning Review Routine",
                "description": "Daily morning review and processing of pending content",
                "steps": [
                    "Check pending review queue",
                    "Sort by priority",
                    "Quick review of high-quality content",
                    "Detailed editing of content needing improvement",
                    "Reject content that doesn't meet standards"
                ]
            },
            {
                "name": "Batch Content Preparation",
                "description": "Prepare a batch of content for next week",
                "steps": [
                    "Generate multiple content drafts",
                    "Batch review and edit",
                    "Schedule publication times",
                    "Set priorities",
                    "Prepare backup content"
                ]
            },
            {
                "name": "Quality Optimization Process",
                "description": "Optimize content quality based on data feedback",
                "steps": [
                    "Analyze historical performance data",
                    "Identify high-performing content patterns",
                    "Regenerate low-quality content",
                    "Update content strategy",
                    "Set new quality standards"
                ]
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎬 Scenario {i}: {scenario['name']}")
            print(f"📝 Description: {scenario['description']}")
            print("🔄 Execution steps:")
            
            for j, step in enumerate(scenario['steps'], 1):
                print(f"   {j}. {step}")
                await asyncio.sleep(0.5)  # Simulate processing time
                print(f"      ✅ Complete")
            
            print(f"🎉 Scenario {i} execution complete!")
    
    async def demo_best_practices(self):
        """Demo best practices and tips"""
        self.print_header("Best Practices and Recommendations")
        
        best_practices = [
            {
                "category": "📝 Content Review",
                "tips": [
                    "Set clear quality standards and checklists",
                    "Prioritize time-sensitive content",
                    "Maintain consistency in review standards",
                    "Record common issues to improve generation quality"
                ]
            },
            {
                "category": "⚡ Efficiency Optimization",
                "tips": [
                    "Use batch operations for similar content",
                    "Establish templates and standard formats",
                    "Set reasonable review time windows",
                    "Leverage data insights to optimize workflows"
                ]
            },
            {
                "category": "📊 Quality Control",
                "tips": [
                    "Regularly analyze content performance data",
                    "Adjust generation parameters based on feedback",
                    "Maintain a high-standard content library",
                    "Continuously optimize SEO and user experience"
                ]
            },
            {
                "category": "🔄 Continuous Improvement",
                "tips": [
                    "Collect and analyze user feedback",
                    "Test different content styles",
                    "Follow industry trends and best practices",
                    "Regularly review and update strategies"
                ]
            }
        ]
        
        for practice in best_practices:
            print(f"\n{practice['category']}")
            for tip in practice['tips']:
                print(f"   💡 {tip}")
    
    async def run_full_demo(self):
        """Run the complete demo"""
        print("🎉 Welcome to the Review Optimization Module Demo!")
        print("This demo will showcase the complete workflow for content review and optimization.")
        
        await self.setup_demo_data()
        await self.demo_get_pending_drafts()
        await self.demo_review_decisions()
        await self.demo_batch_review()
        await self.demo_content_regeneration()
        await self.demo_analytics_and_insights()
        await self.demo_workflow_scenarios()
        await self.demo_best_practices()
        
        self.print_header("Demo Complete")
        print("🎊 Congratulations! You've learned about the main features of the Review Optimization Module:")
        print("   ✅ Content review and decisions")
        print("   ✅ Batch operations")
        print("   ✅ Content regeneration")
        print("   ✅ Analytics and insights")
        print("   ✅ Workflow optimization")
        print("\n📚 Recommended next steps:")
        print("   1. Check the API documentation for detailed interfaces")
        print("   2. Run test cases to verify functionality")
        print("   3. Integrate into your application")
        print("   4. Customize workflows according to your needs")


async def main():
    """Main demo function"""
    demo = ReviewOptimizationDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    print("🚀 Starting Review Optimization Module Demo...")
    asyncio.run(main()) 