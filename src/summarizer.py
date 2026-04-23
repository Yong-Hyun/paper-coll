"""
요약 모듈
=========
Google Gemini AI를 사용하여 영문 논문 초록을 한글로 요약합니다.
최신 google-genai SDK를 사용합니다.
"""

from google import genai

from src.config import GEMINI_API_KEY
from src.logger import get_logger

log = get_logger("summarizer")

# Gemini 클라이언트 초기화
_client = None
_model_name = "gemini-2.5-flash"

if GEMINI_API_KEY:
    try:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        log.info(f"Gemini AI 클라이언트가 성공적으로 초기화되었습니다. (모델: {_model_name})")
    except Exception as e:
        log.warning(f"Gemini 초기화 실패: {e}")
else:
    log.warning("GEMINI_API_KEY가 설정되지 않았습니다. 한글 요약 기능이 비활성화됩니다.")


def summarize_korean(text: str) -> str:
    """
    영문 초록을 한글 3줄 요약으로 변환합니다.

    Args:
        text: 영문 초록 텍스트

    Returns:
        한글 요약 텍스트 (실패 시 안내 메시지)
    """
    if not _client:
        return "한글 요약 불가 (GEMINI_API_KEY 미설정)"

    prompt = (
        "다음은 인공지능 관련 논문의 초록입니다. "
        "핵심 내용을 3줄 이내의 한글로 친절하게 요약해 주세요:\n\n"
        f"{text}"
    )

    try:
        response = _client.models.generate_content(
            model=_model_name,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        log.error(f"Gemini 요약 중 오류: {e}")
        return f"요약 중 오류 발생: {e}"
