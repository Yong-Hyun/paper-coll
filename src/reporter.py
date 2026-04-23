"""
보고서 생성 모듈
================
수집된 논문을 한글 요약과 함께 파일로 저장합니다.
"""

import datetime
from typing import List, Dict

from src.config import OUTPUTS_DIR
from src.summarizer import summarize_korean
from src.logger import get_logger

log = get_logger("reporter")


def generate_report(papers: List[Dict], keywords: List[str]) -> str:
    """
    수집된 논문을 보고서 파일로 저장합니다.

    Args:
        papers: 수집된 논문 리스트
        keywords: 사용된 검색 키워드

    Returns:
        생성된 보고서 파일 경로
    """
    today = datetime.date.today()
    filename = OUTPUTS_DIR / f"report_{today}.txt"

    # 같은 날 이미 보고서가 있으면 번호를 붙임
    counter = 1
    while filename.exists():
        filename = OUTPUTS_DIR / f"report_{today}_{counter}.txt"
        counter += 1

    log.info(f"보고서 생성 시작: {filename.name} ({len(papers)}개 논문)")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{'=' * 70}\n")
        f.write(f"  📄 AI 논문 자동 수집 보고서 — {today}\n")
        f.write(f"  키워드: {', '.join(keywords)}\n")
        f.write(f"  수집 시각: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"{'=' * 70}\n\n")

        for i, paper in enumerate(papers, 1):
            log.info(f"  [{i}/{len(papers)}] 요약 중: {paper['title'][:50]}...")
            ko_summary = summarize_korean(paper["summary"])

            f.write(f"[{i}] {paper['title']}\n")
            f.write(f"    출처: {paper['source']} | 날짜: {paper['published']}\n")
            f.write(f"    링크: {paper['link']}\n")
            f.write(f"    ▶ AI 한글 요약:\n")
            for line in ko_summary.split("\n"):
                f.write(f"      {line}\n")
            f.write(f"\n{'-' * 70}\n\n")

    log.info(f"✅ 보고서 생성 완료: {filename}")
    return str(filename)
