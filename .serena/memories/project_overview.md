# Morgan - Project Overview

## Purpose
Morgan은 AI를 활용해 슬랙 활동을 분석하고 똑똑한 할일 목록을 생성하는 개인용 도구입니다.

### 주요 기능
- **스마트 AI 분석**: OpenAI GPT-4o-mini와 Claude 3.5 Sonnet을 활용한 컨텍스트 이해
- **지능적 우선순위**: 발신자, 시간, 내용, 개인 패턴을 종합한 우선순위 계산
- **자동 할일 생성**: 액션이 필요한 메시지를 자동으로 할일로 변환
- **학습 시스템**: 사용자 피드백을 통한 지속적인 개선
- **비용 최적화**: 메시지 복잡도에 따른 AI 모델 자동 선택

### 비즈니스 가치
- 슬랙의 정보 과부하 문제 해결
- 중요한 메시지와 액션 아이템 자동 식별
- 개인 생산성 향상 및 업무 효율성 증대

## Architecture Overview

```
📦 Morgan
├── 🧠 AI Engine (ai_engine.py)
│   ├── AIModelRouter - 메시지 복잡도 기반 모델 선택
│   ├── OpenAIClient - GPT-4o-mini 클라이언트 (빠른 분류)
│   ├── ClaudeClient - Claude 3.5 클라이언트 (깊은 분석)
│   └── AIEngine - 통합 AI 분석 엔진
├── 📱 Slack Client (slack_client.py)
│   ├── 멘션 메시지 수집
│   ├── DM 수집
│   ├── 스레드 댓글 추적
│   └── 채널 활동 모니터링
├── 🎯 Priority Engine (priority_engine.py)
│   ├── 발신자 권위도 분석
│   ├── 시간 긴급도 계산
│   ├── 내용 중요도 평가
│   └── 개인 패턴 적용
├── 📋 Todo Generator (morgan.py)
│   ├── TodoGenerator - 스마트 제목 생성
│   ├── MorganOrchestrator - 메인 오케스트레이터
│   └── 태그 자동 분류
├── 📊 Data Models (models.py)
│   ├── SlackMessage, AIAnalysis, PriorityScore
│   ├── TodoItem, UserPattern, LearningFeedback
│   └── TodoList
└── 🖥️ CLI Interface (main.py)
    ├── Typer 기반 명령어 인터페이스
    ├── Rich 기반 아름다운 출력
    └── 사용자 피드백 및 학습 시스템
```

## Key Components
1. **AI Engine**: 이중 모델 전략으로 비용 최적화
2. **Priority Engine**: 다차원 우선순위 계산
3. **Todo Generator**: 컨텍스트 인식 할일 생성
4. **Learning System**: 사용자 피드백 기반 지속 개선