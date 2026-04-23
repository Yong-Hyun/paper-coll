"""
Paper Collection Agent - 메인 에이전트
======================================
arXiv, Hugging Face, Semantic Scholar, PubMed, OpenAlex,
bioRxiv/medRxiv 등 다양한 소스에서 AI 관련 논문을 수집하고,
Gemini AI로 한글 요약하여 보고서를 생성합니다.

사용법:
  1회 실행:        python -m src.agent
  스케줄러 모드:    python -m src.agent --daemon
"""

import argparse
import time
import signal
import sys
import schedule

from src.config import (
    KEYWORDS, SCHEDULE_TIME, ENABLED_SOURCES,
    ARXIV_MAX_RESULTS, HF_MAX_RESULTS,
    SEMANTIC_SCHOLAR_MAX_RESULTS, PUBMED_MAX_RESULTS,
    OPENALEX_MAX_RESULTS, BIORXIV_MAX_RESULTS, MEDRXIV_MAX_RESULTS,
)
from src.collector import (
    fetch_arxiv, fetch_huggingface_daily,
    fetch_semantic_scholar, fetch_pubmed,
    fetch_openalex, fetch_biorxiv,
)
from src.dedup import deduplicate
from src.reporter import generate_report
from src.logger import get_logger

log = get_logger("agent")

# ─── 소스별 수집 함수 매핑 ─────────────────────────
_SOURCE_MAP = {
    "arxiv":            lambda: fetch_arxiv(KEYWORDS, max_results=ARXIV_MAX_RESULTS),
    "huggingface":      lambda: fetch_huggingface_daily(max_results=HF_MAX_RESULTS),
    "semantic_scholar": lambda: fetch_semantic_scholar(KEYWORDS, max_results=SEMANTIC_SCHOLAR_MAX_RESULTS),
    "pubmed":           lambda: fetch_pubmed(KEYWORDS, max_results=PUBMED_MAX_RESULTS),
    "openalex":         lambda: fetch_openalex(KEYWORDS, max_results=OPENALEX_MAX_RESULTS),
    "biorxiv":          lambda: fetch_biorxiv(KEYWORDS, max_results=BIORXIV_MAX_RESULTS, server="biorxiv"),
    "medrxiv":          lambda: fetch_biorxiv(KEYWORDS, max_results=MEDRXIV_MAX_RESULTS, server="medrxiv"),
}

# ─── 종료 시그널 처리 ──────────────────────────────
_running = True


def _handle_signal(signum, frame):
    global _running
    log.info("종료 신호를 수신했습니다. 안전하게 종료합니다...")
    _running = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ─── 핵심 수집 작업 ────────────────────────────────
def run_collection():
    """논문 수집 → 중복 제거 → 보고서 생성 파이프라인을 실행합니다."""
    log.info("=" * 60)
    log.info("📡 논문 수집 작업을 시작합니다")
    log.info(f"   키워드: {', '.join(KEYWORDS)}")
    log.info(f"   활성 소스: {', '.join(ENABLED_SOURCES)}")
    log.info("=" * 60)

    # 1단계: 활성화된 소스에서 논문 수집
    papers = []
    for source_name in ENABLED_SOURCES:
        fetcher = _SOURCE_MAP.get(source_name)
        if fetcher:
            try:
                papers.extend(fetcher())
            except Exception as e:
                log.error(f"'{source_name}' 수집 중 예외 발생: {e}")
        else:
            log.warning(f"알 수 없는 소스: '{source_name}' (무시됨)")

    if not papers:
        log.warning("수집된 논문이 없습니다.")
        return

    log.info(f"총 {len(papers)}개의 논문이 수집되었습니다.")

    # 2단계: 중복 제거
    new_papers = deduplicate(papers)

    if not new_papers:
        log.info("모든 논문이 이전에 수집된 것입니다. 보고서를 생성하지 않습니다.")
        return

    # 3단계: 보고서 생성
    report_path = generate_report(new_papers, KEYWORDS)
    log.info(f"🎉 작업 완료! 보고서: {report_path}")


# ─── 데몬(스케줄러) 모드 ───────────────────────────
def run_daemon():
    """
    지정된 시간에 매일 자동으로 논문을 수집하는 상주 모드입니다.
    .env의 SCHEDULE_TIME (기본값: 09:00)에 맞춰 작동합니다.
    """
    log.info("🔄 스케줄러 모드로 시작합니다")
    log.info(f"   매일 {SCHEDULE_TIME}에 논문 수집이 실행됩니다")
    log.info(f"   종료: Ctrl+C")

    # 스케줄 등록
    schedule.every().day.at(SCHEDULE_TIME).do(run_collection)

    # 시작 직후 1회 즉시 실행
    log.info("시작 시 1회 즉시 수집을 실행합니다...")
    run_collection()

    # 스케줄 루프
    while _running:
        schedule.run_pending()
        time.sleep(30)  # 30초마다 스케줄 확인

    log.info("스케줄러가 종료되었습니다.")


# ─── CLI 진입점 ────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="AI 논문 자동 수집 에이전트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python -m src.agent              1회 수집 실행
  python -m src.agent --daemon     상주 모드 (매일 자동 실행)
        """,
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="상주(데몬) 모드: 매일 지정된 시간에 자동 수집",
    )
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    else:
        run_collection()


if __name__ == "__main__":
    main()
