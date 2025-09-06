"""
Morgan - Core Data Models

Pydantic-based data models for Slack messages, AI analysis, and todo items.
"""

from datetime import datetime
from enum import StrEnum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class Priority(StrEnum):
    """Priority levels for todo items"""
    URGENT = "urgent"      # 즉시 처리 (30분 내)
    HIGH = "high"          # 오늘 중 처리
    MEDIUM = "medium"      # 이번 주 처리
    LOW = "low"           # 여유 있게 처리


class ActivityType(StrEnum):
    """Types of Slack activities"""
    MENTION = "mention"              # @멘션
    DM = "dm"                       # 개인 메시지
    THREAD_REPLY = "thread_reply"   # 스레드 댓글
    CHANNEL_MESSAGE = "channel"     # 채널 메시지


class WorkType(StrEnum):
    """Types of work identified in messages"""
    MEETING = "meeting"      # 회의 관련
    REVIEW = "review"        # 검토/리뷰
    INFO = "info"           # 정보 공유
    DECISION = "decision"    # 의사결정 필요
    SUPPORT = "support"      # 지원/도움
    OTHER = "other"         # 기타


class SlackMessage(BaseModel):
    """Slack message data model"""
    message_id: str
    channel_id: str
    channel_name: str
    user_id: str
    username: str
    text: str
    timestamp: datetime
    permalink: str
    
    # Message context
    activity_type: ActivityType
    thread_ts: Optional[str] = None
    is_bot: bool = False
    mentions_me: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIAnalysis(BaseModel):
    """AI analysis results for a message"""
    # Analysis results
    action_required: bool
    urgency_score: float = Field(ge=0, le=1, description="Urgency from 0-1")
    complexity: str = Field(description="simple|medium|complex")
    work_type: WorkType
    emotional_tone: str = Field(description="neutral|urgent|frustrated|encouraging")
    
    # Time estimation
    estimated_time_minutes: int = Field(ge=0, description="Expected time to handle")
    
    # AI metadata
    confidence: float = Field(ge=0, le=1, description="AI confidence in analysis")
    reasoning: str = Field(description="Brief explanation of the analysis")
    detected_keywords: List[str] = Field(default_factory=list)
    
    # Model info
    model_used: str = Field(description="AI model that performed analysis")
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PriorityScore(BaseModel):
    """Priority scoring with detailed breakdown"""
    final_score: float = Field(ge=0, le=1, description="Final priority score")
    priority_level: Priority
    
    # Score breakdown
    sender_authority_score: float = Field(ge=0, le=1)
    time_urgency_score: float = Field(ge=0, le=1)
    content_importance_score: float = Field(ge=0, le=1)
    personal_weight_score: float = Field(ge=0, le=1)
    
    # Recommendations
    recommended_action_time: str = Field(description="When to handle this")
    reasoning: str = Field(description="Why this priority was assigned")
    
    # Context
    calculated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TodoItem(BaseModel):
    """A todo item generated from Slack activity"""
    id: str = Field(description="Unique identifier")
    
    # Source
    source_message: SlackMessage
    ai_analysis: AIAnalysis
    priority_score: PriorityScore
    
    # Todo details
    title: str = Field(description="Brief todo title")
    description: str = Field(description="Detailed description")
    tags: List[str] = Field(default_factory=list)
    
    # Status
    completed: bool = False
    completed_at: Optional[datetime] = None
    
    # User interaction
    user_feedback: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def priority(self) -> Priority:
        """Get priority level from score"""
        return self.priority_score.priority_level

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPattern(BaseModel):
    """Learned user behavior patterns"""
    pattern_type: str = Field(description="Type of pattern (sender, keyword, time, etc)")
    pattern_value: str = Field(description="The actual pattern")
    weight_adjustment: float = Field(description="How much to adjust priority")
    confidence: float = Field(ge=0, le=1, description="Confidence in this pattern")
    usage_count: int = Field(ge=0, description="How many times this pattern was used")
    
    last_updated: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LearningFeedback(BaseModel):
    """User feedback for learning system"""
    todo_id: str
    predicted_priority: Priority
    actual_priority: Optional[Priority] = None
    user_satisfaction: int = Field(ge=1, le=5, description="1=very poor, 5=excellent")
    feedback_text: Optional[str] = None
    
    # Context for learning
    context_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TodoList(BaseModel):
    """A collection of todo items with metadata"""
    id: str = Field(description="List identifier")
    title: str = Field(description="List title")
    description: Optional[str] = None
    
    # Todos
    items: List[TodoItem] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_items: int = Field(default=0)
    completed_items: int = Field(default=0)
    
    # Generation info
    source_hours_scanned: int = Field(default=24)
    ai_models_used: List[str] = Field(default_factory=list)

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate"""
        if self.total_items == 0:
            return 0.0
        return self.completed_items / self.total_items

    def add_item(self, item: TodoItem) -> None:
        """Add a todo item to the list"""
        self.items.append(item)
        self.total_items = len(self.items)
        self.completed_items = sum(1 for item in self.items if item.completed)
        self.updated_at = datetime.now()

    def get_by_priority(self, priority: Priority) -> List[TodoItem]:
        """Get items by priority level"""
        return [item for item in self.items if item.priority == priority]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Example usage and validation
if __name__ == "__main__":
    # Test models
    sample_message = SlackMessage(
        message_id="123",
        channel_id="C123",
        channel_name="general",
        user_id="U123",
        username="john",
        text="Can you review this when you have time?",
        timestamp=datetime.now(),
        permalink="https://slack.com/message/123",
        activity_type=ActivityType.MENTION,
        mentions_me=True
    )
    
    print("✅ Models loaded successfully!")
    print(f"Sample message: {sample_message.text}")