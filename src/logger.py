"""
로깅 설정 모듈
==============
파일과 콘솔에 동시에 로그를 기록합니다.
logs/ 디렉토리에 날짜별 로그 파일이 생성됩니다.
"""

import logging
import sys
from datetime import datetime
from src.config import LOGS_DIR, LOG_LEVEL


def get_logger(name: str = "paper-agent") -> logging.Logger:
    """프로젝트 전체에서 사용할 로거를 생성합니다."""
    logger = logging.getLogger(name)

    # 이미 핸들러가 등록되어 있으면 중복 추가 방지
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # 포맷 설정
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔 핸들러
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # 파일 핸들러 (날짜별)
    log_file = LOGS_DIR / f"agent_{datetime.now():%Y-%m-%d}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
