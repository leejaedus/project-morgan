"""
Morgan - Priority Calculation Engine

Smart priority scoring system that learns from user behavior patterns.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from models import SlackMessage, AIAnalysis, PriorityScore, Priority, UserPattern


class PriorityCalculator:
    """Calculates smart priorities for messages based on multiple factors"""
    
    def __init__(self):
        # Default weights - can be adjusted by learning
        self.default_weights = {
            "sender_authority": 0.3,
            "time_urgency": 0.2, 
            "content_importance": 0.3,
            "personal_patterns": 0.2
        }
        
        # Sender role mappings
        self.role_authority_scores = {
            "ceo": 0.95,
            "manager": 0.8,
            "team_lead": 0.7,
            "colleague": 0.5,
            "junior": 0.3,
            "bot": 0.1,
            "external": 0.6,
            "unknown": 0.4
        }
        
        # User patterns (loaded from database/learning system)
        self.user_patterns: List[UserPattern] = []
        
        # Working hours (can be customized)
        self.working_hours = {
            "start": 9,  # 9 AM
            "end": 18,   # 6 PM
            "timezone": "local"
        }
    
    def calculate_priority(self, message: SlackMessage, ai_analysis: AIAnalysis, 
                          user_patterns: Optional[List[UserPattern]] = None) -> PriorityScore:
        """Calculate comprehensive priority score"""
        
        if user_patterns:
            self.user_patterns = user_patterns
        
        # Calculate individual scores
        sender_score = self._calculate_sender_authority_score(message)
        time_score = self._calculate_time_urgency_score(message, ai_analysis)
        content_score = self._calculate_content_importance_score(message, ai_analysis)
        personal_score = self._apply_personal_patterns(message, ai_analysis)
        
        # Weighted final score
        weights = self._get_adjusted_weights(message)
        final_score = (
            sender_score * weights["sender_authority"] +
            time_score * weights["time_urgency"] +
            content_score * weights["content_importance"] +
            personal_score * weights["personal_patterns"]
        )
        
        # Clamp to 0-1 range
        final_score = max(0.0, min(1.0, final_score))
        
        # Determine priority level
        priority_level = self._score_to_priority(final_score)
        
        # Generate recommendation
        action_time = self._suggest_action_time(final_score, message, ai_analysis)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            sender_score, time_score, content_score, personal_score, weights
        )
        
        return PriorityScore(
            final_score=final_score,
            priority_level=priority_level,
            sender_authority_score=sender_score,
            time_urgency_score=time_score,
            content_importance_score=content_score,
            personal_weight_score=personal_score,
            recommended_action_time=action_time,
            reasoning=reasoning
        )
    
    def _calculate_sender_authority_score(self, message: SlackMessage) -> float:
        """Calculate score based on sender's authority/relationship"""
        base_score = 0.5
        
        # Activity type influence
        if message.activity_type.value == "dm":
            base_score += 0.2  # Personal messages are more important
        elif message.activity_type.value == "mention":
            base_score += 0.3  # Direct mentions are very important
        elif message.activity_type.value == "thread_reply":
            base_score += 0.1  # Thread replies have some importance
        
        # Channel-based authority (rough heuristics)
        channel_name = message.channel_name.lower()
        if any(keyword in channel_name for keyword in ["exec", "leadership", "board"]):
            base_score += 0.3
        elif any(keyword in channel_name for keyword in ["urgent", "critical", "alert"]):
            base_score += 0.25
        elif any(keyword in channel_name for keyword in ["general", "random", "off-topic"]):
            base_score -= 0.1
        
        # Time of day factor (messages outside working hours might be more urgent)
        hour = message.timestamp.hour
        if hour < self.working_hours["start"] or hour > self.working_hours["end"]:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_time_urgency_score(self, message: SlackMessage, ai_analysis: AIAnalysis) -> float:
        """Calculate urgency based on timing factors"""
        base_score = ai_analysis.urgency_score
        
        # Message age factor
        age_hours = (datetime.now() - message.timestamp).total_seconds() / 3600
        if age_hours < 1:
            base_score += 0.2  # Very recent messages are more urgent
        elif age_hours > 24:
            base_score -= 0.2  # Older messages are less urgent
        
        # Day of week factor
        weekday = message.timestamp.weekday()
        if weekday >= 5:  # Weekend
            base_score -= 0.1  # Weekend messages can usually wait
        elif weekday == 0:  # Monday
            base_score += 0.1  # Monday messages often need quick attention
        
        # Time of day factor
        hour = message.timestamp.hour
        if 9 <= hour <= 17:  # Business hours
            base_score += 0.1
        elif hour >= 22 or hour <= 6:  # Late night/early morning
            base_score += 0.2  # Unusual timing suggests urgency
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_content_importance_score(self, message: SlackMessage, ai_analysis: AIAnalysis) -> float:
        """Calculate importance based on message content"""
        base_score = 0.5
        
        # AI analysis factors
        if ai_analysis.action_required:
            base_score += 0.3
        
        if ai_analysis.work_type.value in ["decision", "meeting", "review"]:
            base_score += 0.2
        elif ai_analysis.work_type.value in ["info", "support"]:
            base_score += 0.1
        
        # Complexity factor
        if ai_analysis.complexity == "complex":
            base_score += 0.15
        elif ai_analysis.complexity == "simple":
            base_score -= 0.05
        
        # Emotional tone factor
        if ai_analysis.emotional_tone == "urgent":
            base_score += 0.2
        elif ai_analysis.emotional_tone == "frustrated":
            base_score += 0.15
        elif ai_analysis.emotional_tone == "encouraging":
            base_score += 0.05
        
        # Message length factor (very short or very long messages might be more important)
        text_length = len(message.text)
        if text_length > 500:  # Long messages
            base_score += 0.1
        elif text_length < 20:  # Very short messages
            base_score += 0.05
        
        # Keyword boost
        high_priority_keywords = [
            "urgent", "asap", "immediately", "critical", "emergency",
            "deadline", "board", "client", "customer", "revenue", "budget"
        ]
        text_lower = message.text.lower()
        keyword_count = sum(1 for keyword in high_priority_keywords if keyword in text_lower)
        base_score += min(0.2, keyword_count * 0.05)
        
        return max(0.0, min(1.0, base_score))
    
    def _apply_personal_patterns(self, message: SlackMessage, ai_analysis: AIAnalysis) -> float:
        """Apply learned personal patterns"""
        base_score = 0.5
        
        # Apply user patterns
        for pattern in self.user_patterns:
            if self._pattern_matches(pattern, message, ai_analysis):
                # Apply weight adjustment with confidence weighting
                adjustment = pattern.weight_adjustment * pattern.confidence
                base_score += adjustment
        
        return max(0.0, min(1.0, base_score))
    
    def _pattern_matches(self, pattern: UserPattern, message: SlackMessage, ai_analysis: AIAnalysis) -> bool:
        """Check if a pattern matches the current message"""
        pattern_type = pattern.pattern_type
        pattern_value = pattern.pattern_value.lower()
        
        if pattern_type == "sender":
            return pattern_value in message.username.lower()
        elif pattern_type == "channel":
            return pattern_value in message.channel_name.lower()
        elif pattern_type == "keyword":
            return pattern_value in message.text.lower()
        elif pattern_type == "work_type":
            return pattern_value == ai_analysis.work_type.value
        elif pattern_type == "time":
            # Pattern value could be "morning", "afternoon", "evening"
            hour = message.timestamp.hour
            if pattern_value == "morning" and 6 <= hour < 12:
                return True
            elif pattern_value == "afternoon" and 12 <= hour < 18:
                return True
            elif pattern_value == "evening" and 18 <= hour < 22:
                return True
        
        return False
    
    def _get_adjusted_weights(self, message: SlackMessage) -> Dict[str, float]:
        """Get weights adjusted for specific message context"""
        weights = self.default_weights.copy()
        
        # Adjust weights based on message type
        if message.activity_type.value == "dm":
            weights["sender_authority"] += 0.1
            weights["time_urgency"] += 0.05
        elif message.activity_type.value == "mention":
            weights["content_importance"] += 0.1
        elif message.activity_type.value == "channel":
            weights["personal_patterns"] += 0.1
        
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        for key in weights:
            weights[key] /= total
        
        return weights
    
    def _score_to_priority(self, score: float) -> Priority:
        """Convert numeric score to priority enum"""
        if score >= 0.8:
            return Priority.URGENT
        elif score >= 0.6:
            return Priority.HIGH
        elif score >= 0.4:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _suggest_action_time(self, score: float, message: SlackMessage, ai_analysis: AIAnalysis) -> str:
        """Suggest when to handle this item"""
        if score >= 0.8:
            return "즉시 처리 (30분 내)"
        elif score >= 0.6:
            if ai_analysis.estimated_time_minutes > 30:
                return "오늘 중 처리 (집중 시간 확보)"
            else:
                return "오늘 중 처리 (1-2시간 내)"
        elif score >= 0.4:
            return "이번 주 처리"
        else:
            return "여유 있을 때 처리"
    
    def _generate_reasoning(self, sender_score: float, time_score: float, 
                          content_score: float, personal_score: float,
                          weights: Dict[str, float]) -> str:
        """Generate human-readable reasoning for the priority"""
        reasons = []
        
        # Identify the strongest factors
        scores = {
            "발신자 중요도": sender_score,
            "시간 긴급도": time_score, 
            "내용 중요도": content_score,
            "개인 패턴": personal_score
        }
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Generate reasoning based on top factors
        top_factor, top_score = sorted_scores[0]
        if top_score > 0.7:
            reasons.append(f"{top_factor}가 높음 ({top_score:.2f})")
        
        second_factor, second_score = sorted_scores[1]
        if second_score > 0.6:
            reasons.append(f"{second_factor}도 고려됨 ({second_score:.2f})")
        
        if not reasons:
            reasons.append("일반적인 우선순위")
        
        return " | ".join(reasons)
    
    def batch_calculate_priorities(self, messages_with_analysis: List[Tuple[SlackMessage, AIAnalysis]],
                                  user_patterns: Optional[List[UserPattern]] = None) -> List[PriorityScore]:
        """Calculate priorities for multiple messages efficiently"""
        priorities = []
        
        if user_patterns:
            self.user_patterns = user_patterns
        
        for message, analysis in messages_with_analysis:
            priority = self.calculate_priority(message, analysis, user_patterns)
            priorities.append(priority)
        
        return priorities


# Test the priority calculator
if __name__ == "__main__":
    from datetime import datetime
    
    # Create test data
    test_message = SlackMessage(
        message_id="test123",
        channel_id="C123",
        channel_name="urgent-requests",
        user_id="U123",
        username="sarah_manager",
        text="Can you please review the Q4 budget proposal? The board meeting is tomorrow and we need your input ASAP.",
        timestamp=datetime.now(),
        permalink="https://slack.com/test",
        activity_type="mention",
        mentions_me=True
    )
    
    test_analysis = AIAnalysis(
        action_required=True,
        urgency_score=0.85,
        complexity="complex",
        work_type="decision",
        emotional_tone="urgent",
        estimated_time_minutes=45,
        confidence=0.9,
        reasoning="Board meeting urgency with direct request",
        detected_keywords=["review", "budget", "ASAP", "tomorrow"],
        model_used="test"
    )
    
    calculator = PriorityCalculator()
    priority = calculator.calculate_priority(test_message, test_analysis)
    
    print("🧪 Test Priority Calculation:")
    print(f"Final score: {priority.final_score:.3f}")
    print(f"Priority level: {priority.priority_level}")
    print(f"Recommended action: {priority.recommended_action_time}")
    print(f"Reasoning: {priority.reasoning}")
    print("\n📊 Score breakdown:")
    print(f"  Sender authority: {priority.sender_authority_score:.3f}")
    print(f"  Time urgency: {priority.time_urgency_score:.3f}")
    print(f"  Content importance: {priority.content_importance_score:.3f}")
    print(f"  Personal patterns: {priority.personal_weight_score:.3f}")