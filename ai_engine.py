"""
Morgan - AI Analysis Engine

Handles AI-powered analysis of Slack messages using OpenAI and Anthropic APIs.
"""

import json
import os
from typing import Dict, Any, Optional, List
import asyncio

import openai
import anthropic
from anthropic import Anthropic

from models import SlackMessage, AIAnalysis, WorkType


class AIModelRouter:
    """Routes messages to appropriate AI models based on complexity"""
    
    def __init__(self):
        self.simple_threshold = 50  # Characters
        self.complex_indicators = [
            "project", "budget", "deadline", "meeting", "review",
            "approval", "decision", "strategy", "planning"
        ]
    
    def should_use_complex_model(self, message: SlackMessage) -> bool:
        """Determine if message needs complex AI model"""
        text = message.text.lower()
        
        # Use complex model if:
        # 1. Message is long
        if len(message.text) > 200:
            return True
        
        # 2. Contains complex indicators
        if any(indicator in text for indicator in self.complex_indicators):
            return True
        
        # 3. Is from a mention (likely important)
        if message.mentions_me:
            return True
        
        # 4. Is a DM (personal attention needed)
        if message.activity_type.value == "dm":
            return True
        
        return False


class OpenAIClient:
    """OpenAI API client for fast, cost-effective analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = os.getenv("DEFAULT_AI_MODEL", "gpt-4o-mini")
        
    async def quick_classify(self, message: SlackMessage) -> AIAnalysis:
        """Quick classification using GPT-4o-mini"""
        prompt = self._create_classification_prompt(message)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing work communications for priority and action requirements."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            analysis_data = json.loads(content)
            
            return AIAnalysis(
                action_required=analysis_data.get("action_required", False),
                urgency_score=analysis_data.get("urgency_score", 0.5),
                complexity=analysis_data.get("complexity", "simple"),
                work_type=WorkType(analysis_data.get("work_type", "other")),
                emotional_tone=analysis_data.get("emotional_tone", "neutral"),
                estimated_time_minutes=analysis_data.get("estimated_time_minutes", 10),
                confidence=analysis_data.get("confidence", 0.7),
                reasoning=analysis_data.get("reasoning", "Quick AI classification"),
                detected_keywords=analysis_data.get("detected_keywords", []),
                model_used=self.model
            )
            
        except Exception as e:
            # Fallback analysis
            print(f"⚠️ OpenAI analysis failed: {e}")
            return self._create_fallback_analysis(message, "openai-error")
    
    def _create_classification_prompt(self, message: SlackMessage) -> str:
        """Create prompt for quick classification"""
        return f"""
Analyze this Slack message for work priority and action requirements:

Message: "{message.text}"
From: {message.username}
Channel: {message.channel_name}
Type: {message.activity_type}
Mentions me: {message.mentions_me}

Provide analysis as JSON:
{{
    "action_required": boolean,
    "urgency_score": 0.0-1.0,
    "complexity": "simple|medium|complex", 
    "work_type": "meeting|review|info|decision|support|other",
    "emotional_tone": "neutral|urgent|frustrated|encouraging",
    "estimated_time_minutes": integer,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "detected_keywords": ["key", "words"]
}}
"""
    
    def _create_fallback_analysis(self, message: SlackMessage, error_type: str) -> AIAnalysis:
        """Create fallback analysis when AI fails"""
        # Basic heuristic analysis
        text_lower = message.text.lower()
        
        action_required = any(word in text_lower for word in [
            "?", "please", "can you", "could you", "review", "check", "confirm"
        ])
        
        urgency_score = 0.7 if message.mentions_me else 0.3
        if any(word in text_lower for word in ["urgent", "asap", "급함"]):
            urgency_score = 0.9
        
        return AIAnalysis(
            action_required=action_required,
            urgency_score=urgency_score,
            complexity="simple",
            work_type=WorkType.OTHER,
            emotional_tone="neutral",
            estimated_time_minutes=15,
            confidence=0.3,
            reasoning=f"Fallback analysis due to {error_type}",
            detected_keywords=[],
            model_used="fallback-heuristic"
        )


class ClaudeClient:
    """Anthropic Claude client for deep contextual analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = os.getenv("COMPLEX_AI_MODEL", "claude-3-5-sonnet-20241022")
    
    async def deep_analyze(self, message: SlackMessage) -> AIAnalysis:
        """Deep contextual analysis using Claude"""
        prompt = self._create_deep_analysis_prompt(message)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            analysis_data = json.loads(content)
            
            return AIAnalysis(
                action_required=analysis_data.get("action_required", False),
                urgency_score=analysis_data.get("urgency_score", 0.5),
                complexity=analysis_data.get("complexity", "medium"),
                work_type=WorkType(analysis_data.get("work_type", "other")),
                emotional_tone=analysis_data.get("emotional_tone", "neutral"),
                estimated_time_minutes=analysis_data.get("estimated_time_minutes", 20),
                confidence=analysis_data.get("confidence", 0.8),
                reasoning=analysis_data.get("reasoning", "Deep Claude analysis"),
                detected_keywords=analysis_data.get("detected_keywords", []),
                model_used=self.model
            )
            
        except Exception as e:
            print(f"⚠️ Claude analysis failed: {e}")
            # Use OpenAI as fallback
            openai_client = OpenAIClient()
            return await openai_client.quick_classify(message)
    
    def _create_deep_analysis_prompt(self, message: SlackMessage) -> str:
        """Create prompt for deep contextual analysis"""
        return f"""
You are an expert work communication analyst. Perform deep contextual analysis of this Slack message:

Message: "{message.text}"
From: {message.username}
Channel: {message.channel_name} ({message.activity_type})
Timestamp: {message.timestamp}
Mentions me directly: {message.mentions_me}
Message URL: {message.permalink}

Context Analysis Required:
1. What is the real intent behind this message?
2. What level of urgency does this actually represent?
3. How much cognitive effort will responding require?
4. What type of work/collaboration is this?
5. What emotions or tone are conveyed?

Consider:
- Implicit vs explicit requests
- Cultural communication patterns
- Relationship dynamics (based on communication style)
- Time sensitivity indicators
- Complexity of required response

Provide detailed analysis as JSON:
{{
    "action_required": boolean,
    "urgency_score": 0.0-1.0,
    "complexity": "simple|medium|complex",
    "work_type": "meeting|review|info|decision|support|other",
    "emotional_tone": "neutral|urgent|frustrated|encouraging|casual",
    "estimated_time_minutes": integer,
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation of analysis",
    "detected_keywords": ["important", "contextual", "keywords"]
}}

Focus on practical prioritization for a busy professional.
"""


class AIEngine:
    """Main AI engine that coordinates different models"""
    
    def __init__(self):
        self.router = AIModelRouter()
        self.openai_client = OpenAIClient()
        self.claude_client = ClaudeClient()
        
        # Usage tracking for cost optimization
        self.usage_stats = {
            "openai_calls": 0,
            "claude_calls": 0,
            "total_tokens": 0
        }
    
    async def analyze_message(self, message: SlackMessage) -> AIAnalysis:
        """Analyze a single message using the appropriate AI model"""
        
        # Route to appropriate model
        if self.router.should_use_complex_model(message):
            self.usage_stats["claude_calls"] += 1
            print(f"🧠 Using Claude for complex analysis: {message.text[:50]}...")
            return await self.claude_client.deep_analyze(message)
        else:
            self.usage_stats["openai_calls"] += 1
            print(f"⚡ Using OpenAI for quick analysis: {message.text[:30]}...")
            return await self.openai_client.quick_classify(message)
    
    async def analyze_batch(self, messages: List[SlackMessage], 
                          max_concurrent: int = 5) -> List[tuple[SlackMessage, AIAnalysis]]:
        """Analyze multiple messages with concurrency control"""
        print(f"🤖 Starting AI analysis of {len(messages)} messages...")
        
        # Create semaphore to limit concurrent API calls
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(message: SlackMessage) -> tuple[SlackMessage, AIAnalysis]:
            async with semaphore:
                analysis = await self.analyze_message(message)
                return message, analysis
        
        # Run analysis with concurrency control
        tasks = [analyze_with_semaphore(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for result in results:
            if isinstance(result, tuple):
                successful_results.append(result)
            else:
                print(f"⚠️ Analysis failed: {result}")
        
        print(f"✅ AI analysis complete: {len(successful_results)} successful")
        return successful_results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total_calls = self.usage_stats["openai_calls"] + self.usage_stats["claude_calls"]
        
        # Rough cost estimation (approximate)
        openai_cost = self.usage_stats["openai_calls"] * 0.001  # $0.001 per call (rough)
        claude_cost = self.usage_stats["claude_calls"] * 0.01   # $0.01 per call (rough)
        
        return {
            **self.usage_stats,
            "total_calls": total_calls,
            "estimated_cost_usd": round(openai_cost + claude_cost, 3),
            "openai_percentage": round(self.usage_stats["openai_calls"] / max(total_calls, 1) * 100, 1),
            "claude_percentage": round(self.usage_stats["claude_calls"] / max(total_calls, 1) * 100, 1)
        }


# Test the AI engine
if __name__ == "__main__":
    async def test_ai_engine():
        from datetime import datetime
        
        # Create test message
        test_message = SlackMessage(
            message_id="test123",
            channel_id="C123",
            channel_name="general",
            user_id="U123", 
            username="john_doe",
            text="Can you review the quarterly budget proposal when you have time? It's needed for the board meeting next week.",
            timestamp=datetime.now(),
            permalink="https://slack.com/test",
            activity_type="mention",
            mentions_me=True
        )
        
        engine = AIEngine()
        analysis = await engine.analyze_message(test_message)
        
        print("🧪 Test Analysis Results:")
        print(f"Action required: {analysis.action_required}")
        print(f"Urgency score: {analysis.urgency_score}")
        print(f"Work type: {analysis.work_type}")
        print(f"Model used: {analysis.model_used}")
        print(f"Reasoning: {analysis.reasoning}")
        
        stats = engine.get_usage_stats()
        print(f"\n📊 Usage Stats: {stats}")
    
    # Uncomment to test
    # asyncio.run(test_ai_engine())