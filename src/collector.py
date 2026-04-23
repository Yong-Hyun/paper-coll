"""
논문 수집 모듈
==============
다양한 학술 데이터베이스에서 논문을 수집하는 핵심 로직입니다.

지원 소스 (search-lit SKILL 참조):
  1. arXiv          — AI/CS 분야 프리프린트 (기존)
  2. Hugging Face   — Daily Papers 인기 논문 (기존)
  3. Semantic Scholar — AI 기반 시맨틱 학술 검색 (신규)
  4. PubMed/NCBI    — 의학·생명과학 논문 (신규)
  5. OpenAlex       — 전 분야 오픈 학술 메타데이터 (신규)
  6. bioRxiv/medRxiv — 생명과학·의학 프리프린트 (신규)
"""

import time
import requests
import xml.etree.ElementTree as ET
import urllib.parse
from typing import List, Dict

from src.logger import get_logger

log = get_logger("collector")

# 공통 HTTP 세션 (connection pooling + 기본 헤더)
_session = requests.Session()
_session.headers.update({
    "User-Agent": "PaperCollectionAgent/2.0 (mailto:paper-agent@example.com)"
})


# ─────────────────────────────────────────────────────
# 1. arXiv (기존)
# ─────────────────────────────────────────────────────
def fetch_arxiv(keywords: List[str], max_results: int = 5) -> List[Dict]:
    """
    arXiv API에서 키워드로 최신 논문을 검색합니다.

    Args:
        keywords: 검색 키워드 목록
        max_results: 최대 수집 개수

    Returns:
        논문 정보 딕셔너리 리스트
    """
    log.info(f"[arXiv] 수집 시작 (키워드: {', '.join(keywords)}, 최대: {max_results}개)")

    query = " OR ".join([f'all:"{k}"' for k in keywords])
    encoded_query = urllib.parse.quote(query)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={encoded_query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )

    papers = []
    try:
        response = _session.get(url, timeout=30)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)

        for entry in entries:
            title = " ".join(entry.find("atom:title", ns).text.split())
            summary = " ".join(entry.find("atom:summary", ns).text.split())
            link = entry.find('atom:link[@rel="alternate"]', ns).attrib["href"]
            published = entry.find("atom:published", ns).text

            papers.append({
                "source": "arXiv",
                "title": title,
                "summary": summary,
                "link": link,
                "published": published,
            })

        log.info(f"[arXiv] {len(papers)}개 수집 완료")

    except requests.exceptions.RequestException as e:
        log.error(f"[arXiv] 네트워크 오류: {e}")
    except ET.ParseError as e:
        log.error(f"[arXiv] 응답 파싱 오류: {e}")

    return papers


# ─────────────────────────────────────────────────────
# 2. Hugging Face Daily Papers (기존)
# ─────────────────────────────────────────────────────
def fetch_huggingface_daily(max_results: int = 5) -> List[Dict]:
    """
    Hugging Face Daily Papers API에서 오늘의 인기 논문을 수집합니다.

    Args:
        max_results: 최대 수집 개수

    Returns:
        논문 정보 딕셔너리 리스트
    """
    log.info(f"[HuggingFace] Daily Papers 수집 시작 (최대: {max_results}개)")
    url = "https://huggingface.co/api/daily_papers"

    papers = []
    try:
        response = _session.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        for p in data[:max_results]:
            papers.append({
                "source": "Hugging Face",
                "title": p["paper"]["title"],
                "summary": p["paper"]["summary"],
                "link": f"https://huggingface.co/papers/{p['paper']['id']}",
                "published": p["publishedAt"],
            })

        log.info(f"[HuggingFace] {len(papers)}개 수집 완료")

    except requests.exceptions.RequestException as e:
        log.error(f"[HuggingFace] 네트워크 오류: {e}")
    except (KeyError, ValueError) as e:
        log.error(f"[HuggingFace] 응답 파싱 오류: {e}")

    return papers


# ─────────────────────────────────────────────────────
# 3. Semantic Scholar (신규)
#    - search-lit SKILL의 semanticSearch 참조
#    - 무료 API, 키 없이도 사용 가능 (100 req/5min)
# ─────────────────────────────────────────────────────
def fetch_semantic_scholar(keywords: List[str], max_results: int = 5) -> List[Dict]:
    """
    Semantic Scholar Academic Graph API에서 논문을 검색합니다.
    AI 기반 시맨틱 검색으로 키워드 매칭보다 관련성이 높은 결과를 반환합니다.

    API 문서: https://api.semanticscholar.org/api-docs/graph

    Args:
        keywords: 검색 키워드 목록
        max_results: 최대 수집 개수

    Returns:
        논문 정보 딕셔너리 리스트
    """
    log.info(f"[SemanticScholar] 수집 시작 (키워드: {', '.join(keywords)}, 최대: {max_results}개)")

    # 키워드를 자연어 쿼리로 조합
    query = " ".join(keywords)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,url,publicationDate,externalIds",
        "sort": "publicationDate:desc",
    }

    papers = []
    try:
        response = _session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        for item in data.get("data", []):
            abstract = item.get("abstract") or ""
            pub_date = item.get("publicationDate") or "날짜 미상"

            # DOI 기반 링크 우선, 없으면 S2 링크 사용
            external_ids = item.get("externalIds") or {}
            doi = external_ids.get("DOI")
            link = f"https://doi.org/{doi}" if doi else item.get("url", "")

            if item.get("title"):
                papers.append({
                    "source": "Semantic Scholar",
                    "title": item["title"],
                    "summary": abstract,
                    "link": link,
                    "published": pub_date,
                })

        log.info(f"[SemanticScholar] {len(papers)}개 수집 완료")

    except requests.exceptions.RequestException as e:
        log.error(f"[SemanticScholar] 네트워크 오류: {e}")
    except (KeyError, ValueError) as e:
        log.error(f"[SemanticScholar] 응답 파싱 오류: {e}")

    return papers


# ─────────────────────────────────────────────────────
# 4. PubMed / NCBI E-utilities (신규)
#    - search-lit SKILL의 NCBI E-utilities 참조
#    - Rate limit: 3 req/sec (API key 없이)
# ─────────────────────────────────────────────────────
def fetch_pubmed(keywords: List[str], max_results: int = 5) -> List[Dict]:
    """
    PubMed(NCBI E-utilities)에서 최신 논문을 검색합니다.
    의학·생명과학 분야에 특화되어 있습니다.

    API 문서: https://www.ncbi.nlm.nih.gov/books/NBK25500/

    Args:
        keywords: 검색 키워드 목록
        max_results: 최대 수집 개수

    Returns:
        논문 정보 딕셔너리 리스트
    """
    log.info(f"[PubMed] 수집 시작 (키워드: {', '.join(keywords)}, 최대: {max_results}개)")

    # 1단계: esearch — 키워드로 PMID 목록 가져오기
    query = " OR ".join([f'"{k}"' for k in keywords])
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "date",
        "retmode": "json",
    }

    papers = []
    try:
        search_resp = _session.get(search_url, params=search_params, timeout=30)
        search_resp.raise_for_status()

        search_data = search_resp.json()
        pmids = search_data.get("esearchresult", {}).get("idlist", [])

        if not pmids:
            log.info("[PubMed] 검색 결과 없음")
            return papers

        # Rate limiting (NCBI 정책 준수: 3 req/sec)
        time.sleep(0.35)

        # 2단계: efetch — PMID로 초록 포함 상세 정보 가져오기
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "xml",
            "retmode": "xml",
        }

        fetch_resp = _session.get(fetch_url, params=fetch_params, timeout=30)
        fetch_resp.raise_for_status()

        root = ET.fromstring(fetch_resp.content)

        for article_elem in root.findall(".//PubmedArticle"):
            medline = article_elem.find(".//MedlineCitation")
            if medline is None:
                continue

            pmid_elem = medline.find("PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            # 제목
            title_elem = medline.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # 초록 (여러 AbstractText 요소를 결합)
            abstract_parts = []
            for abs_text in medline.findall(".//Abstract/AbstractText"):
                label = abs_text.get("Label", "")
                text = "".join(abs_text.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts) if abstract_parts else ""

            # 저널 이름
            journal_elem = medline.find(".//Journal/Title")
            source_journal = journal_elem.text if journal_elem is not None else ""

            # 출판 날짜
            pub_date_elem = medline.find(".//Article/Journal/JournalIssue/PubDate")
            if pub_date_elem is not None:
                year = pub_date_elem.findtext("Year", "")
                month = pub_date_elem.findtext("Month", "")
                day = pub_date_elem.findtext("Day", "")
                pub_date = f"{year}/{month}/{day}".rstrip("/")
            else:
                pub_date = "날짜 미상"

            # DOI
            doi = ""
            for eid in article_elem.findall(".//ArticleIdList/ArticleId"):
                if eid.get("IdType") == "doi":
                    doi = eid.text or ""
                    break

            link = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            papers.append({
                "source": f"PubMed ({source_journal})" if source_journal else "PubMed",
                "title": title,
                "summary": abstract if abstract else f"[PubMed PMID: {pmid}] 초록 없음",
                "link": link,
                "published": pub_date,
            })

        log.info(f"[PubMed] {len(papers)}개 수집 완료")

    except requests.exceptions.RequestException as e:
        log.error(f"[PubMed] 네트워크 오류: {e}")
    except (KeyError, ValueError) as e:
        log.error(f"[PubMed] 응답 파싱 오류: {e}")

    return papers


# ─────────────────────────────────────────────────────
# 5. OpenAlex (신규)
#    - search-lit SKILL Phase 5a 참조
#    - 전 분야 오픈 학술 메타데이터
#    - Polite pool: User-Agent에 email 포함 필요
# ─────────────────────────────────────────────────────
def fetch_openalex(keywords: List[str], max_results: int = 5) -> List[Dict]:
    """
    OpenAlex API에서 최신 논문을 검색합니다.
    2억 건 이상의 학술 문헌 메타데이터를 제공하는 오픈 소스입니다.

    API 문서: https://docs.openalex.org/

    Args:
        keywords: 검색 키워드 목록
        max_results: 최대 수집 개수

    Returns:
        논문 정보 딕셔너리 리스트
    """
    log.info(f"[OpenAlex] 수집 시작 (키워드: {', '.join(keywords)}, 최대: {max_results}개)")

    # OpenAlex 검색어 조합
    query = " ".join(keywords)
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": max_results,
        "sort": "publication_date:desc",
        "filter": "type:article",
        "select": "id,title,doi,publication_date,primary_location,abstract_inverted_index",
    }

    papers = []
    try:
        response = _session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        for work in data.get("results", []):
            title = work.get("title", "")
            pub_date = work.get("publication_date", "날짜 미상")
            doi = work.get("doi", "")
            link = doi if doi else work.get("id", "")

            # abstract_inverted_index를 일반 텍스트로 변환
            abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

            # 저널 이름
            primary = work.get("primary_location") or {}
            source_info = primary.get("source") or {}
            journal = source_info.get("display_name", "")

            if title:
                papers.append({
                    "source": f"OpenAlex ({journal})" if journal else "OpenAlex",
                    "title": title,
                    "summary": abstract or "초록 없음",
                    "link": link,
                    "published": pub_date,
                })

        log.info(f"[OpenAlex] {len(papers)}개 수집 완료")

    except requests.exceptions.RequestException as e:
        log.error(f"[OpenAlex] 네트워크 오류: {e}")
    except (KeyError, ValueError) as e:
        log.error(f"[OpenAlex] 응답 파싱 오류: {e}")

    return papers


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """
    OpenAlex의 abstract_inverted_index를 일반 텍스트로 복원합니다.

    inverted_index 형식: {"word": [position1, position2, ...], ...}
    """
    if not inverted_index:
        return ""

    try:
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        return " ".join(word for _, word in word_positions)
    except Exception:
        return ""


# ─────────────────────────────────────────────────────
# 6. bioRxiv / medRxiv (신규)
#    - search-lit SKILL의 bioRxiv 검색 참조
#    - 생명과학·의학 프리프린트 서버
# ─────────────────────────────────────────────────────
def fetch_biorxiv(keywords: List[str], max_results: int = 5, server: str = "biorxiv") -> List[Dict]:
    """
    bioRxiv 또는 medRxiv에서 최근 프리프린트를 검색합니다.

    API 문서: https://api.biorxiv.org/

    Args:
        keywords: 검색 키워드 목록
        max_results: 최대 수집 개수
        server: "biorxiv" 또는 "medrxiv"

    Returns:
        논문 정보 딕셔너리 리스트
    """
    log.info(f"[{server}] 수집 시작 (키워드: {', '.join(keywords)}, 최대: {max_results}개)")

    # bioRxiv content API — 최근 30일 논문 중 검색
    # API가 키워드 검색을 직접 지원하지 않으므로 최근 논문을 가져와 필터링
    from datetime import datetime, timedelta

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    url = f"https://api.biorxiv.org/details/{server}/{start_date}/{end_date}/0/50"

    papers = []
    try:
        response = _session.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        collection = data.get("collection", [])

        # 키워드 필터링 (제목 또는 초록에 키워드가 포함된 것만)
        keywords_lower = [k.lower() for k in keywords]
        filtered = []
        for item in collection:
            title = item.get("title", "").lower()
            abstract = item.get("abstract", "").lower()
            text = title + " " + abstract

            if any(kw in text for kw in keywords_lower):
                filtered.append(item)

        for item in filtered[:max_results]:
            doi = item.get("doi", "")
            papers.append({
                "source": server.capitalize(),
                "title": item.get("title", ""),
                "summary": item.get("abstract", ""),
                "link": f"https://doi.org/{doi}" if doi else "",
                "published": item.get("date", "날짜 미상"),
            })

        log.info(f"[{server}] {len(filtered)}개 매칭 중 {len(papers)}개 수집 완료")

    except requests.exceptions.RequestException as e:
        log.error(f"[{server}] 네트워크 오류: {e}")
    except (KeyError, ValueError) as e:
        log.error(f"[{server}] 응답 파싱 오류: {e}")

    return papers
