"""
중복 검사 모듈
==============
이미 수집한 논문을 다시 수집하지 않도록
data/history.json에 기록을 유지합니다.
"""

import json
from typing import List, Dict, Set

from src.config import DATA_DIR
from src.logger import get_logger

log = get_logger("dedup")

HISTORY_FILE = DATA_DIR / "history.json"


def load_history() -> Set[str]:
    """이전에 수집한 논문 링크 목록을 불러옵니다."""
    if not HISTORY_FILE.exists():
        return set()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("collected_links", []))
    except (json.JSONDecodeError, IOError) as e:
        log.warning(f"히스토리 파일 읽기 실패, 새로 시작합니다: {e}")
        return set()


def save_history(links: Set[str]) -> None:
    """수집한 논문 링크 목록을 저장합니다."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"collected_links": sorted(links)}, f, ensure_ascii=False, indent=2)
    except IOError as e:
        log.error(f"히스토리 파일 저장 실패: {e}")


def deduplicate(papers: List[Dict]) -> List[Dict]:
    """
    이미 수집한 논문을 제외하고 새로운 논문만 반환합니다.
    새로운 논문의 링크는 히스토리에 추가 저장됩니다.

    Args:
        papers: 수집된 논문 리스트

    Returns:
        중복이 제거된 새로운 논문 리스트
    """
    history = load_history()
    new_papers = [p for p in papers if p["link"] not in history]

    if len(papers) != len(new_papers):
        log.info(f"중복 제거: {len(papers)}개 중 {len(papers) - len(new_papers)}개 이미 수집됨")

    # 새 논문 링크를 히스토리에 추가
    new_links = {p["link"] for p in new_papers}
    history.update(new_links)
    save_history(history)

    log.info(f"새로운 논문: {len(new_papers)}개")
    return new_papers
