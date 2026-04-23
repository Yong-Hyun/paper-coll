"""
설정 관리 모듈
=============
.env 파일과 환경변수에서 설정값을 읽어오는 모듈입니다.
프로젝트 루트 경로를 기준으로 모든 경로가 결정됩니다.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리 (src/ 의 상위 디렉토리)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# .env 파일 로드
load_dotenv(PROJECT_ROOT / ".env")


# ─── API 키 ────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ─── 스케줄 설정 ───────────────────────────────────
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")

# ─── 수집 키워드 ───────────────────────────────────
_raw_keywords = os.getenv("KEYWORDS", "On-device AI,ADL,Dementia Care,Edge AI")
KEYWORDS = [k.strip() for k in _raw_keywords.split(",") if k.strip()]

# ─── 수집 개수 (소스별) ────────────────────────────
ARXIV_MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "5"))
HF_MAX_RESULTS = int(os.getenv("HF_MAX_RESULTS", "5"))
SEMANTIC_SCHOLAR_MAX_RESULTS = int(os.getenv("SEMANTIC_SCHOLAR_MAX_RESULTS", "5"))
PUBMED_MAX_RESULTS = int(os.getenv("PUBMED_MAX_RESULTS", "5"))
OPENALEX_MAX_RESULTS = int(os.getenv("OPENALEX_MAX_RESULTS", "5"))
BIORXIV_MAX_RESULTS = int(os.getenv("BIORXIV_MAX_RESULTS", "3"))
MEDRXIV_MAX_RESULTS = int(os.getenv("MEDRXIV_MAX_RESULTS", "3"))

# ─── 활성화할 수집 소스 ────────────────────────────
# 쉼표로 구분. 사용 가능한 값:
#   arxiv, huggingface, semantic_scholar, pubmed, openalex, biorxiv, medrxiv
_raw_sources = os.getenv(
    "ENABLED_SOURCES",
    "arxiv,huggingface,semantic_scholar,pubmed,openalex,biorxiv,medrxiv"
)
ENABLED_SOURCES = [s.strip().lower() for s in _raw_sources.split(",") if s.strip()]

# ─── 경로 설정 ─────────────────────────────────────
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# ─── 로그 레벨 ─────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 필요한 디렉토리 자동 생성
for d in [OUTPUTS_DIR, DATA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
