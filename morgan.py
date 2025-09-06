"""
Morgan - Main Orchestrator & Todo Generator

Central coordination of all components for smart Slack todo management.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from models import (
    SlackMessage, AIAnalysis, PriorityScore, TodoItem, TodoList, 
    Priority, UserPattern, LearningFeedback
)
from slack_client import SlackClient
from ai_engine import AIEngine
from priority_engine import PriorityCalculator


class TodoGenerator:
    """Generates smart todo items from analyzed Slack activities"""
    
    def __init__(self):
        pass
    
    def generate_todo_item(self, message: SlackMessage, analysis: AIAnalysis, 
                          priority_score: PriorityScore) -> TodoItem:
        """Generate a single todo item"""
        
        # Generate title
        title = self._generate_title(message, analysis)
        
        # Generate description
        description = self._generate_description(message, analysis, priority_score)
        
        # Generate tags
        tags = self._generate_tags(message, analysis)
        
        return TodoItem(
            id=str(uuid.uuid4()),
            source_message=message,
            ai_analysis=analysis,
            priority_score=priority_score,
            title=title,
            description=description,
            tags=tags
        )
    
    def _generate_title(self, message: SlackMessage, analysis: AIAnalysis) -> str:
        """Generate concise todo title"""
        sender = message.username
        
        # Extract action from message
        text = message.text.strip()
        
        # Common patterns for todo titles
        if "?" in text:
            # Question -> "답변: ..."
            return f"답변: {sender}의 질문"
        elif any(word in text.lower() for word in ["review", "검토"]):
            return f"검토: {sender} 요청"
        elif any(word in text.lower() for word in ["meeting", "회의"]):
            return f"회의: {sender}와 논의"
        elif any(word in text.lower() for word in ["approve", "승인"]):
            return f"승인: {sender} 요청 건"
        elif analysis.work_type.value == "decision":
            return f"결정: {sender} 의사결정 필요"
        elif analysis.work_type.value == "support":
            return f"지원: {sender} 도움 요청"
        else:
            # Generic title
            return f"처리: {sender}의 메시지"
    
    def _generate_description(self, message: SlackMessage, analysis: AIAnalysis, 
                            priority_score: PriorityScore) -> str:
        """Generate detailed todo description"""
        lines = []
        
        # Message preview
        preview = message.text[:100] + "..." if len(message.text) > 100 else message.text
        lines.append(f"💬 \"{preview}\"")
        lines.append("")
        
        # Context info
        lines.append(f"👤 발신자: {message.username}")
        lines.append(f"📍 채널: #{message.channel_name} ({message.activity_type})")
        lines.append(f"⏰ 시간: {message.timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        # AI Analysis
        lines.append(f"🤖 AI 분석:")
        lines.append(f"  - 작업 유형: {analysis.work_type}")
        lines.append(f"  - 복잡도: {analysis.complexity}")
        lines.append(f"  - 예상 소요시간: {analysis.estimated_time_minutes}분")
        lines.append(f"  - 감정적 톤: {analysis.emotional_tone}")
        if analysis.detected_keywords:
            lines.append(f"  - 핵심 키워드: {', '.join(analysis.detected_keywords)}")
        lines.append("")
        
        # Priority reasoning
        lines.append(f"🎯 우선순위 근거: {priority_score.reasoning}")
        lines.append(f"📅 권장 처리시간: {priority_score.recommended_action_time}")
        
        return "\n".join(lines)
    
    def _generate_tags(self, message: SlackMessage, analysis: AIAnalysis) -> List[str]:
        """Generate relevant tags"""
        tags = []
        
        # Activity type tag
        tags.append(f"type:{message.activity_type}")
        
        # Work type tag
        tags.append(f"work:{analysis.work_type}")
        
        # Channel tag
        tags.append(f"channel:{message.channel_name}")
        
        # Urgency tag
        if analysis.urgency_score > 0.8:
            tags.append("urgent")
        elif analysis.urgency_score > 0.6:
            tags.append("important")
        
        # Complexity tag
        tags.append(f"complexity:{analysis.complexity}")
        
        # Time estimate tag
        if analysis.estimated_time_minutes <= 15:
            tags.append("quick")
        elif analysis.estimated_time_minutes >= 60:
            tags.append("deep-work")
        
        return tags
    
    def generate_todo_list(self, analyzed_messages: List[tuple[SlackMessage, AIAnalysis, PriorityScore]],
                          title: str = None) -> TodoList:
        """Generate complete todo list from analyzed messages"""
        
        # Generate todos
        todos = []
        models_used = set()
        
        for message, analysis, priority in analyzed_messages:
            if analysis.action_required:  # Only create todos for actionable items
                todo = self.generate_todo_item(message, analysis, priority)
                todos.append(todo)
                models_used.add(analysis.model_used)
        
        # Sort by priority score (highest first)
        todos.sort(key=lambda t: t.priority_score.final_score, reverse=True)
        
        # Generate list metadata
        if not title:
            title = f"스마트 할일 목록 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        todo_list = TodoList(
            id=str(uuid.uuid4()),
            title=title,
            description=f"{len(analyzed_messages)}개 메시지 분석 결과",
            items=todos,
            total_items=len(todos),
            completed_items=0,
            ai_models_used=list(models_used)
        )
        
        return todo_list


class MorganOrchestrator:
    """Main orchestrator that coordinates all components"""
    
    def __init__(self):
        self.slack_client = SlackClient()
        self.ai_engine = AIEngine()
        self.priority_calculator = PriorityCalculator()
        self.todo_generator = TodoGenerator()
        
        # User patterns for learning (would be loaded from database)
        self.user_patterns: List[UserPattern] = []
    
    async def process_slack_activities(self, hours: int = 24, 
                                      max_messages: int = 100) -> TodoList:
        """Main processing pipeline"""
        print("🚀 Morgan이 슬랙 활동을 분석하고 있습니다...")
        
        try:
            # Step 1: Collect Slack activities
            print("\n📱 1단계: Slack 활동 수집")
            activities = await self.slack_client.collect_all_activities(hours)
            
            if not activities:
                print("❌ 슬랙 활동을 찾을 수 없습니다.")
                return TodoList(
                    id=str(uuid.uuid4()),
                    title="빈 할일 목록",
                    description="분석할 활동이 없습니다."
                )
            
            # Limit number of messages to process
            if len(activities) > max_messages:
                print(f"⚠️ 메시지가 많아 최근 {max_messages}개만 처리합니다.")
                activities = activities[:max_messages]
            
            # Step 2: AI Analysis
            print(f"\n🤖 2단계: AI 분석 ({len(activities)}개 메시지)")
            analyzed_activities = await self.ai_engine.analyze_batch(activities)
            
            # Step 3: Priority Calculation
            print(f"\n🎯 3단계: 우선순위 계산")
            prioritized_activities = []
            for message, analysis in analyzed_activities:
                priority = self.priority_calculator.calculate_priority(
                    message, analysis, self.user_patterns
                )
                prioritized_activities.append((message, analysis, priority))
            
            # Step 4: Todo Generation
            print(f"\n📋 4단계: 할일 목록 생성")
            todo_list = self.todo_generator.generate_todo_list(prioritized_activities)
            
            # Step 5: Summary
            print(f"\n✅ 완료!")
            print(f"  - 분석된 메시지: {len(activities)}개")
            print(f"  - 생성된 할일: {len(todo_list.items)}개")
            print(f"  - 사용된 AI 모델: {', '.join(todo_list.ai_models_used)}")
            
            # Usage stats
            stats = self.ai_engine.get_usage_stats()
            print(f"  - AI 호출: OpenAI {stats['openai_calls']}회, Claude {stats['claude_calls']}회")
            print(f"  - 예상 비용: ${stats['estimated_cost_usd']}")
            
            return todo_list
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # Return empty todo list
            return TodoList(
                id=str(uuid.uuid4()),
                title="오류 - 빈 할일 목록",
                description=f"처리 중 오류 발생: {str(e)}"
            )
    
    def collect_feedback(self, todo_id: str, satisfaction: int, 
                        feedback_text: str = None, actual_priority: Priority = None) -> LearningFeedback:
        """Collect user feedback for learning"""
        # Find the todo item (in real implementation, this would query database)
        # For now, create feedback object
        
        feedback = LearningFeedback(
            todo_id=todo_id,
            predicted_priority=Priority.MEDIUM,  # Would get from actual todo
            actual_priority=actual_priority,
            user_satisfaction=satisfaction,
            feedback_text=feedback_text
        )
        
        print(f"📝 피드백 수집됨: 만족도 {satisfaction}/5")
        if feedback_text:
            print(f"   의견: {feedback_text}")
        
        # TODO: Store in database and update learning patterns
        
        return feedback
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        ai_stats = self.ai_engine.get_usage_stats()
        
        return {
            "ai_usage": ai_stats,
            "user_patterns_count": len(self.user_patterns),
            "last_processed": datetime.now().isoformat()
        }


# Test Morgan orchestrator
if __name__ == "__main__":
    async def test_morgan():
        morgan = MorganOrchestrator()
        
        print("🧪 Testing Morgan orchestrator...")
        print("Note: This requires valid Slack and AI API tokens in environment variables.")
        
        # Test with limited scope
        todo_list = await morgan.process_slack_activities(hours=1, max_messages=5)
        
        if todo_list.items:
            print(f"\n📋 Generated {len(todo_list.items)} todos:")
            for i, todo in enumerate(todo_list.items[:3]):
                print(f"{i+1}. [{todo.priority}] {todo.title}")
                print(f"   {todo.source_message.username}: {todo.source_message.text[:50]}...")
                print()
        else:
            print("No todos generated (no actionable messages found)")
        
        # Test feedback collection
        if todo_list.items:
            feedback = morgan.collect_feedback(
                todo_id=todo_list.items[0].id,
                satisfaction=4,
                feedback_text="우선순위가 적절했습니다"
            )
            print(f"Feedback collected: {feedback.user_satisfaction}/5")
    
    # Uncomment to test (requires API keys)
    # asyncio.run(test_morgan())