```YAML
date: 2026-04-23
by: Yong-Hyun Lim
```



# 📄 AI 논문 자동 수집 에이전트


**7개 학술 데이터베이스**에서 AI 관련 논문을 **매일 자동으로** 수집하고,  
Gemini AI로 한글 요약하여 보고서를 생성하는 에이전트입니다.

---

## 📡 수집 소스

| 소스 | 분야 | 설명 |
|------|------|------|
| 🔬 **arXiv** | CS/AI | 프리프린트 서버, 키워드 기반 검색 |
| 🤗 **Hugging Face** | AI/ML | Daily Papers 인기 논문 |
| 🧠 **Semantic Scholar** | 전 분야 | AI 기반 시맨틱 학술 검색 |
| 🏥 **PubMed** | 의학/생명과학 | NCBI E-utilities API, 초록 포함 |
| 📚 **OpenAlex** | 전 분야 | 2억+ 건 오픈 학술 메타데이터 |
| 🧬 **bioRxiv** | 생명과학 | 프리프린트, 키워드 필터링 |
| 💊 **medRxiv** | 의학 | 프리프린트, 키워드 필터링 |

---

## 📁 프로젝트 구조

```
paper-collection-agent/
├── src/
│   ├── agent.py        # 메인 에이전트 (1회 실행 / 데몬 모드)
│   ├── collector.py    # 7개 소스 논문 수집
│   ├── summarizer.py   # Gemini AI 한글 요약
│   ├── dedup.py        # 중복 논문 제거
│   ├── reporter.py     # 보고서 생성
│   ├── config.py       # 설정 관리
│   └── logger.py       # 로깅
├── scripts/
│   ├── setup_scheduler.ps1   # Windows 작업 스케줄러 등록
│   └── remove_scheduler.ps1  # 작업 스케줄러 제거
├── outputs/            # 생성된 보고서
├── data/               # 수집 히스토리 (중복 방지)
├── logs/               # 실행 로그
├── .env.example        # 환경변수 템플릿
├── .env                # 실제 설정 (직접 생성)
├── requirements.txt    # Python 의존성
├── run_agent.bat       # 1회 실행 스크립트
└── run_daemon.bat      # 상주 모드 실행 스크립트
```

---

## 🚀 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
copy .env.example .env
```

`.env` 파일을 열어 Gemini API 키와 설정을 입력하세요:

```env
GEMINI_API_KEY=your_actual_api_key
SCHEDULE_TIME=09:00
KEYWORDS=On-device AI,ADL,Dementia Care,Edge AI
ENABLED_SOURCES=arxiv,huggingface,semantic_scholar,pubmed,openalex,biorxiv,medrxiv
```

> 💡 API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급받으세요.

---

## ▶️ 실행 방법

### 방법 1: 1회 수동 실행

```bash
python -m src.agent
```

또는 `run_agent.bat` 더블클릭

### 방법 2: 데몬(상주) 모드

프로세스가 계속 실행되면서 매일 지정된 시간에 자동 수집합니다:

```bash
python -m src.agent --daemon
```

또는 `run_daemon.bat` 더블클릭

### 방법 3: Windows 작업 스케줄러 (⭐ 권장)

PC를 켜놓지 않아도, 로그인만 하면 자동으로 실행됩니다:

```powershell
# 관리자 권한 PowerShell에서 실행
.\scripts\setup_scheduler.ps1

# 실행 시간 변경 시
.\scripts\setup_scheduler.ps1 -TriggerTime "08:30"

# 즉시 테스트 실행
Start-ScheduledTask -TaskName "PaperCollectionAgent"

# 스케줄러 제거
.\scripts\remove_scheduler.ps1
```

---

## 📋 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 다중 소스 수집 | 7개 학술 DB에서 동시 수집 |
| 🇰🇷 한글 요약 | Gemini AI 기반 3줄 요약 |
| 🔄 중복 제거 | 이전에 수집한 논문 자동 스킵 |
| ⏰ 자동 스케줄링 | 데몬 모드 / 작업 스케줄러 |
| 📝 로깅 | 실행 기록을 `logs/`에 저장 |
| ⚙️ 소스 선택 | `.env`에서 원하는 소스만 활성화 |

---

## ⚙️ 설정 옵션 (.env)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `GEMINI_API_KEY` | (필수) | Google AI Studio API 키 |
| `SCHEDULE_TIME` | `09:00` | 매일 자동 수집 시간 |
| `KEYWORDS` | `On-device AI,...` | 검색 키워드 (쉼표 구분) |
| `ENABLED_SOURCES` | 모든 소스 | 활성 수집 소스 (쉼표 구분) |
| `ARXIV_MAX_RESULTS` | `5` | arXiv 최대 수집 수 |
| `HF_MAX_RESULTS` | `5` | HuggingFace 최대 수집 수 |
| `SEMANTIC_SCHOLAR_MAX_RESULTS` | `5` | Semantic Scholar 최대 수집 수 |
| `PUBMED_MAX_RESULTS` | `5` | PubMed 최대 수집 수 |
| `OPENALEX_MAX_RESULTS` | `5` | OpenAlex 최대 수집 수 |
| `BIORXIV_MAX_RESULTS` | `3` | bioRxiv 최대 수집 수 |
| `MEDRXIV_MAX_RESULTS` | `3` | medRxiv 최대 수집 수 |
| `LOG_LEVEL` | `INFO` | 로그 상세 수준 |
