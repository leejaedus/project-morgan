# 🤖 Morgan - AI-Powered Smart Slack Activity Manager

Morgan은 AI를 활용해 슬랙 활동을 분석하고 똑똑한 할일 목록을 생성하는 개인용 도구입니다.

## ✨ 주요 기능

- **🧠 스마트 AI 분석**: OpenAI GPT-4o-mini와 Claude 3.5 Sonnet을 활용한 컨텍스트 이해
- **🎯 지능적 우선순위**: 발신자, 시간, 내용, 개인 패턴을 종합한 우선순위 계산
- **📋 자동 할일 생성**: 액션이 필요한 메시지를 자동으로 할일로 변환
- **📊 학습 시스템**: 사용자 피드백을 통한 지속적인 개선
- **💰 비용 최적화**: 메시지 복잡도에 따른 AI 모델 자동 선택

## 🚀 빠른 시작

### 1. 설치

```bash
# uv 설치 (없다면)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

### 2. 환경 설정

`.env.example`을 복사해서 `.env` 파일을 만들고 API 키를 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
# Slack Configuration
SLACK_TOKEN=xoxp-your-slack-token

# AI API Keys  
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

### 3. Slack 토큰 발급

1. [Slack API](https://api.slack.com/apps)에서 새 앱 생성
2. OAuth & Permissions에서 다음 스코프 추가:
   - `channels:history`
   - `channels:read` 
   - `groups:history`
   - `groups:read`
   - `im:history`
   - `im:read`
   - `search:read`
   - `users:read`
3. 워크스페이스에 앱 설치 후 토큰 복사

### 4. AI API 키 발급

- **OpenAI**: [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키 생성
- **Anthropic**: [Anthropic Console](https://console.anthropic.com/)에서 API 키 생성

## 📖 사용법

### 기본 분석

```bash
# 최근 24시간 활동 분석
uv run python main.py analyze

# 최근 12시간, 최대 50개 메시지 분석
uv run python main.py analyze --hours 12 --max 50

# 결과를 파일로 저장
uv run python main.py analyze --save
```

### 상세 정보 보기

```bash
# 특정 할일의 상세 정보
uv run python main.py details 1
```

### 피드백 제공 (학습용)

```bash
# 할일 1번에 대해 만족도 4점
uv run python main.py feedback 1 4

# 의견과 함께 피드백
uv run python main.py feedback 1 5 --comment "우선순위가 정확했습니다"
```

### 설정 및 통계

```bash
# 환경 설정 확인
uv run python main.py config

# 사용 통계 보기  
uv run python main.py stats
```

## 🏗️ 아키텍처

```
📦 Morgan
├── 🧠 AI Engine
│   ├── OpenAI Client (GPT-4o-mini) - 빠른 분류
│   └── Claude Client (Claude 3.5) - 깊은 분석
├── 📱 Slack Client  
│   ├── 멘션 메시지 수집
│   ├── DM 수집
│   ├── 스레드 댓글 추적
│   └── 채널 활동 모니터링
├── 🎯 Priority Engine
│   ├── 발신자 권위도 분석
│   ├── 시간 긴급도 계산
│   ├── 내용 중요도 평가
│   └── 개인 패턴 적용
└── 📋 Todo Generator
    ├── 스마트 제목 생성
    ├── 상세 설명 작성
    └── 태그 자동 분류
```

## 🤖 AI 모델 전략

Morgan은 비용 최적화를 위해 메시지 복잡도에 따라 AI 모델을 선택합니다:

### GPT-4o-mini (~$0.15/1M 토큰)
- 간단한 메시지 분류
- 짧은 텍스트 처리
- 일상적인 대화 분석

### Claude 3.5 Sonnet (~$3/1M 토큰)  
- 복잡한 컨텍스트 이해
- 긴 메시지 분석
- 중요한 의사결정 관련 메시지

**예상 월 비용**: 일 100개 메시지 기준 $15-25

## 📊 출력 예시

```
📋 스마트 할일 목록 - 2025-09-05 14:30

┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ 우선순위 ┃ 할일                                   ┃ 발신자        ┃ 채널          ┃ 권장 처리시간        ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 🔥 URGENT│ 검토: 김팀장 요청                      │ 김팀장        │ #marketing    │ 즉시 처리 (30분 내) │
│ ⚡ HIGH  │ 답변: 고객사 미팅 관련 질문           │ 박대리        │ DM            │ 오늘 중 처리        │
│ 📌 MEDIUM│ 처리: 프로젝트 진행상황 확인          │ 이과장        │ #dev-team     │ 이번 주 처리        │
┗━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━┛

📊 총 3개 할일 | 🔥 긴급 1개 | ⚡ 높음 1개 | 📌 보통 1개 | 📝 낮음 0개
```

## ⚙️ 설정 옵션

### 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `HOURS_TO_SCAN` | 분석할 시간 범위 | 24 |
| `MAX_MESSAGES` | 최대 처리 메시지 수 | 100 |
| `DEFAULT_AI_MODEL` | 기본 AI 모델 | gpt-4o-mini |
| `COMPLEX_AI_MODEL` | 복잡한 분석용 모델 | claude-3-5-sonnet-20241022 |
| `LOG_LEVEL` | 로그 레벨 | INFO |

## 🔧 개발자 가이드

### 프로젝트 구조

```
project-morgan/
├── main.py                 # CLI 인터페이스
├── morgan.py              # 메인 오케스트레이터 & Todo 생성기
├── models.py              # Pydantic 데이터 모델
├── slack_client.py        # Slack API 클라이언트
├── ai_engine.py           # AI 분석 엔진
├── priority_engine.py     # 우선순위 계산 엔진
├── pyproject.toml        # Python 3.13 & uv 설정
└── README.md             # 이 파일
```

### 테스트 실행

```bash
# 모델 검증
python models.py

# Slack 클라이언트 테스트 (API 키 필요)
python slack_client.py

# AI 엔진 테스트 (API 키 필요)
python ai_engine.py

# 우선순위 엔진 테스트
python priority_engine.py

# 전체 시스템 테스트 (API 키 필요)
python morgan.py
```

### 확장하기

새로운 우선순위 규칙 추가:
```python
# priority_engine.py의 PriorityCalculator 클래스에 추가
def _custom_priority_rule(self, message: SlackMessage) -> float:
    # 커스텀 로직 구현
    return score
```

## 🔒 보안 및 프라이버시

- **API 키 보안**: 환경변수로만 관리, 절대 코드에 하드코딩하지 않음
- **데이터 익명화**: AI 분석 시 개인정보 마스킹 처리
- **로컬 처리**: 모든 데이터는 로컬에서 처리, 외부 저장소 없음
- **최소 권한**: Slack API 최소 필요 권한만 요청

## 📈 로드맵

### v0.2.0
- [ ] SQLite 데이터베이스 통합
- [ ] 사용자 패턴 학습 시스템
- [ ] 웹 대시보드 (Streamlit)

### v0.3.0  
- [ ] 멀티 워크스페이스 지원
- [ ] 캘린더 연동
- [ ] 자동 실행 스케줄링

### v1.0.0
- [ ] 답변 초안 생성 기능
- [ ] 고급 학습 시스템
- [ ] 플러그인 아키텍처

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🙏 감사

- OpenAI GPT-4o-mini for cost-effective analysis
- Anthropic Claude 3.5 Sonnet for deep understanding  
- Slack API for comprehensive activity access
- Python ecosystem (Pydantic, Typer, Rich) for excellent developer experience
- uv for lightning-fast dependency management

---

**Morgan으로 슬랙의 정보 과부하를 해결하고 정말 중요한 일에 집중하세요! 🚀**