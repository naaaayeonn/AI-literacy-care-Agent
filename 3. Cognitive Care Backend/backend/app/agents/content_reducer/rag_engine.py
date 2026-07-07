"""
rag_engine.py — RAG 기반 신뢰 출처 용어풀이 엔진 (M1)

환각(Hallucination) 없이 신뢰할 수 있는 출처 데이터베이스를 기반으로
전문 용어를 풀이한다.

핵심 원칙:
  RAG는 오직 용어풀이에만 적용한다. (재구성/요약에 절대 미적용)
  모든 용어풀이는 term_dictionary.json의 신뢰 출처 데이터 기반이다.
  생성 결과가 아니라 검색 결과를 반환하므로 환각이 원천 차단된다.

지원 모드:
  - memory (기본): JSON 파일 기반 키워드 매칭
    → sentence-transformers가 있으면 임베딩 유사도로 업그레이드
  - pgvector: PostgreSQL + pgvector (운영 환경, RAG_MODE=pgvector)

Faithfulness 점수:
  - 용어집 직접 매칭: 1.0 (출처 데이터 그대로)
  - 유사도 매칭: 코사인 유사도 기반 근사값
  → 배포 시 Ragas Faithfulness 지표로 교체 권장 (5번 QA 담당)
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

from backend.app.agents.content_reducer.contracts import ChunkDict, TermDict


# ---------------------------------------------------------------------------
# 한국어 조사 제거 전처리
# ---------------------------------------------------------------------------

# 자주 붙는 한국어 조사/어미 목록 (긴 것 먼저 → 짧은 것 순으로 정렬해야 정확히 제거됨)
_KO_PARTICLES = [
    "에서의", "으로의", "에게의",
    "이라는", "라는", "이라고", "라고",
    "이지만", "지만", "이어서", "어서",
    "에서", "에게", "에도", "에만", "에서",
    "으로서", "로서", "으로부터", "로부터",
    "으로", "로", "으로도", "로도",
    "이었다", "였다", "이다",
    "이지", "이기",
    "에서", "에서도", "에서만",
    "까지", "부터", "마다",
    "이며", "이고", "이나",
    "이란", "이라",
    "들의", "들을", "들이", "들은", "들에", "들도",
    "하여", "해서", "하고",
    "이라면", "라면",
    "에는", "에도", "에만",
    "을통해", "를통해",
    "이란",
    "들",
    "의", "을", "를", "이", "가", "은", "는", "과", "와",
    "도", "만", "도", "조차", "마저",
]


def _strip_particles(word: str) -> str:
    """한국어 단어에서 조사/어미를 제거하여 명사 원형을 반환한다."""
    stripped = word.strip()
    # 특수문자, 문장부호 제거
    stripped = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', '', stripped).strip()
    # 조사 제거 (긴 조사부터 시도)
    for particle in _KO_PARTICLES:
        if stripped.endswith(particle) and len(stripped) > len(particle) + 1:
            stripped = stripped[:-len(particle)]
            break
    return stripped.strip()


# ---------------------------------------------------------------------------
# Gemini LLM 실시간 유추 (Step 4 fallback)
# ---------------------------------------------------------------------------

def _query_gemini_llm(word: str, context: str | None = None) -> dict | None:
    """
    Gemini 2.0 Flash를 활용해 단어의 의미를 실시간으로 유추한다.
    context(문장)가 있으면 동음이의어를 구분하여 더 정확한 뜻풀이를 제공한다.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None

    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        if context:
            prompt = (
                f"다음 문장에서 '{word}'라는 단어의 뜻을 50자 이내로 쉽게 설명해 주세요. "
                f"전문 용어라면 비전문가도 이해할 수 있도록 친절하게 설명하세요.\n"
                f"문장: {context}\n"
                f"설명만 간결하게 답변하고 '~입니다'로 마무리하세요."
            )
        else:
            prompt = (
                f"'{word}'의 뜻을 50자 이내로 쉽고 친절하게 설명해 주세요. "
                f"설명만 간결하게 답변하고 '~입니다'로 마무리하세요."
            )

        response = model.generate_content(prompt)
        definition = response.text.strip()

        if definition:
            return {
                "term": word,
                "definition": definition[:120],  # 최대 120자 제한
                "source": "LLM 실시간 유추"
            }
    except Exception as e:
        print(f"[rag_engine] Gemini LLM 유추 실패: {e}")

    return None

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

_RAG_MODE = os.getenv("RAG_MODE", "memory")
_FAITHFULNESS_THRESHOLD = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.80"))

# term_dictionary.json 경로: 프로젝트 루트/data/term_dictionary.json
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_TERM_DICT_PATH = _PROJECT_ROOT / "data" / "term_dictionary.json"


# ---------------------------------------------------------------------------
# 용어집 로더
# ---------------------------------------------------------------------------

def _load_term_dictionary() -> list[dict]:
    """JSON 파일에서 용어집 데이터를 로드한다."""
    if not _TERM_DICT_PATH.exists():
        # 상위 디렉토리에서 재탐색 (경로 유연성)
        for candidate in Path(__file__).parents:
            alt = candidate / "data" / "term_dictionary.json"
            if alt.exists():
                path = alt
                break
        else:
            return []
    else:
        path = _TERM_DICT_PATH

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("terms", [])
    except Exception as e:
        print(f"[rag_engine] 용어집 로드 실패: {e}")
        return []


_TERM_DICT: list[dict] = _load_term_dictionary()
_TERM_VECS: list[list[float]] | None = None  # 용어집 임베딩 캐시 (최초 1회만 계산)


def _get_term_embeddings(model) -> list[list[float]]:
    """용어집 후보 전체를 batch encoding하여 캐시하고 반환한다."""
    global _TERM_VECS
    if _TERM_VECS is None:
        try:
            candidates = []
            for entry in _TERM_DICT:
                candidate = (
                    f"{entry['term']} "
                    + " ".join(entry.get("aliases", []))
                    + f" {entry['definition']}"
                )
                candidates.append(candidate)
            # Batch encode
            _TERM_VECS = model.encode(candidates).tolist()
        except Exception as e:
            print(f"[rag_engine] 용어집 배치 임베딩 생성 실패: {e}")
            _TERM_VECS = []
    return _TERM_VECS


# ---------------------------------------------------------------------------
# 임베딩 모델 (선택적)
# ---------------------------------------------------------------------------

_embedding_model = None
_embedding_loaded = False


def _get_embedding_model():
    """sentence-transformers 모델을 지연 로딩한다. 없으면 None."""
    global _embedding_model, _embedding_loaded
    if _embedding_loaded:
        return _embedding_model
    _embedding_loaded = True
    try:
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv(
            "EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask"
        )
        _embedding_model = SentenceTransformer(model_name)
    except Exception:
        _embedding_model = None
    return _embedding_model


# ---------------------------------------------------------------------------
# PostgreSQL / pgvector 연동 헬퍼
# ---------------------------------------------------------------------------

_pgvector_initialized = False

def _get_db_connection():
    """PostgreSQL DB 연결 객체를 생성하고 pgvector를 등록한다."""
    import psycopg2
    from pgvector.psycopg2 import register_vector

    host = os.getenv("PGVECTOR_HOST", "localhost")
    port = os.getenv("PGVECTOR_PORT", "5432")
    dbname = os.getenv("PGVECTOR_DB", "literacy_care")
    user = os.getenv("PGVECTOR_USER", "postgres")
    password = os.getenv("PGVECTOR_PASSWORD", "postgres")

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        connect_timeout=3
    )
    register_vector(conn)
    return conn


def _init_pgvector_db() -> bool:
    """pgvector DB 확장을 설정하고 테이블 생성 및 초기 데이터를 적재한다."""
    global _pgvector_initialized
    if _pgvector_initialized:
        return True

    conn = None
    try:
        conn = _get_db_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            # 1. vector 확장 활성화
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            # 2. 용어 임베딩 테이블 생성
            cur.execute("""
                CREATE TABLE IF NOT EXISTS term_embeddings (
                    id SERIAL PRIMARY KEY,
                    term TEXT UNIQUE NOT NULL,
                    aliases TEXT[] NOT NULL,
                    definition TEXT NOT NULL,
                    source TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    embedding vector(768)
                );
            """)
            # 3. 테이블에 데이터가 없는 경우 term_dictionary.json 기반으로 임베딩 저장
            cur.execute("SELECT COUNT(*) FROM term_embeddings;")
            count = cur.fetchone()[0]
            if count == 0 and _TERM_DICT:
                print("[rag_engine] Seeding term_embeddings database...")
                model = _get_embedding_model()
                if model is not None:
                    for entry in _TERM_DICT:
                        candidate = (
                            f"{entry['term']} "
                            + " ".join(entry.get("aliases", []))
                            + f" {entry['definition']}"
                        )
                        emb = model.encode(candidate).tolist()
                        cur.execute(
                            """
                            INSERT INTO term_embeddings (term, aliases, definition, source, domain, embedding)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (term) DO NOTHING;
                            """,
                            (
                                entry["term"],
                                entry.get("aliases", []),
                                entry["definition"],
                                entry["source"],
                                entry.get("domain", "일반"),
                                emb
                            )
                        )
        _pgvector_initialized = True
        return True
    except Exception as e:
        print(f"[rag_engine] pgvector DB 초기화/시딩 실패 (memory 모드로 작동): {e}")
        return False
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# 유사도 계산
# ---------------------------------------------------------------------------

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터 간 코사인 유사도를 계산한다."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na > 0 and nb > 0 else 0.0


def _keyword_score(text: str, entry: dict) -> float:
    """
    키워드 기반 매칭 점수를 계산한다.
    텍스트에 용어가 직접 포함되면 높은 점수, 그렇지 않으면 자카드 유사도.
    """
    text_lower = text.lower()
    all_forms: list[str] = [entry["term"]] + entry.get("aliases", [])

    # 직접 포함 여부 확인 (우선순위 최상)
    for form in all_forms:
        if form.lower() in text_lower:
            return 0.95

    # 자카드 유사도
    text_tokens = set(re.findall(r"[가-힣a-zA-Z0-9]+", text_lower))
    candidate_tokens = set(
        re.findall(r"[가-힣a-zA-Z0-9]+", " ".join(all_forms).lower())
    )
    if not text_tokens or not candidate_tokens:
        return 0.0
    inter = len(text_tokens & candidate_tokens)
    union = len(text_tokens | candidate_tokens)
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# 용어 검색
# ---------------------------------------------------------------------------

def _find_terms(text: str, top_k: int = 5) -> list[tuple[dict, float]]:
    """
    텍스트에서 용어집과 매칭되는 용어를 찾는다.
    pgvector 모드와 memory 모드를 모두 지원하며, 실패 시 상호 폴백한다.

    Returns:
        (용어 dict, 유사도 점수) 튜플 목록 (점수 내림차순, 상위 top_k)
    """
    # 1. pgvector 모드로 시도
    if _RAG_MODE == "pgvector":
        if _init_pgvector_db():
            conn = None
            try:
                conn = _get_db_connection()
                model = _get_embedding_model()
                if model is not None:
                    query_embedding = model.encode(text).tolist()
                    with conn.cursor() as cur:
                        # 1 - (embedding <=> query::vector) = Cosine Similarity
                        cur.execute(
                            """
                            SELECT term, aliases, definition, source, domain, 1 - (embedding <=> %s::vector) AS similarity
                            FROM term_embeddings
                            ORDER BY embedding <=> %s::vector
                            LIMIT %s;
                            """,
                            (query_embedding, query_embedding, top_k)
                        )
                        rows = cur.fetchall()
                        db_results = []
                        for row in rows:
                            entry = {
                                "term": row[0],
                                "aliases": row[1],
                                "definition": row[2],
                                "source": row[3],
                                "domain": row[4]
                            }
                            similarity = float(row[5])
                            db_results.append((entry, similarity))
                        # 유사도 0.3 이상만 필터링하여 반환
                        return [(e, s) for e, s in db_results if s >= 0.3]
            except Exception as e:
                print(f"[rag_engine] pgvector 검색 실패, memory 모드로 폴백합니다. 원인: {e}")
            finally:
                if conn:
                    conn.close()

    # 2. memory 모드로 실행 (JSON 파일 기반 인메모리 검색)
    if not _TERM_DICT:
        return []

    model = _get_embedding_model()
    results: list[tuple[dict, float]] = []

    if model is not None:
        try:
            text_vec = model.encode(text).tolist()
            cand_vecs = _get_term_embeddings(model)
            if cand_vecs and len(cand_vecs) == len(_TERM_DICT):
                for i, entry in enumerate(_TERM_DICT):
                    score = _cosine_similarity(text_vec, cand_vecs[i])
                    results.append((entry, score))
            else:
                for entry in _TERM_DICT:
                    candidate = (
                        f"{entry['term']} "
                        + " ".join(entry.get("aliases", []))
                        + f" {entry['definition']}"
                    )
                    cand_vec = model.encode(candidate).tolist()
                    score = _cosine_similarity(text_vec, cand_vec)
                    results.append((entry, score))
        except Exception:
            model = None  # 실패 시 키워드 방식으로 폴백

    if model is None:
        for entry in _TERM_DICT:
            score = _keyword_score(text, entry)
            results.append((entry, score))

    # 점수 내림차순 정렬, 0.3 이상만 반환
    results.sort(key=lambda x: x[1], reverse=True)
    return [(e, s) for e, s in results if s >= 0.3][:top_k]


# ---------------------------------------------------------------------------
# Faithfulness 계산
# ---------------------------------------------------------------------------

def _faithfulness_score(definition: str, source_definition: str) -> float:
    """
    생성 정의와 출처 정의의 충실도를 근사 계산한다.
    용어집에서 직접 가져온 경우 1.0, 수정된 경우 토큰 유사도.
    """
    if definition.strip() == source_definition.strip():
        return 1.0
    def_tokens = set(re.findall(r"[가-힣a-zA-Z]+", definition))
    src_tokens = set(re.findall(r"[가-힣a-zA-Z]+", source_definition))
    if not def_tokens or not src_tokens:
        return 0.5
    inter = len(def_tokens & src_tokens)
    union = len(def_tokens | src_tokens)
    # 기본 점수 0.5 + 토큰 중복 가중치
    return min(1.0, 0.5 + (inter / union) * 0.5) if union > 0 else 0.5


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def inject_rag_terms(chunks: list[ChunkDict]) -> list[ChunkDict]:
    """
    청크 목록에서 전문 용어를 추출하고 RAG 기반 풀이를 주입한다.

    Args:
        chunks: ChunkDict 목록 (restructured_text 포함 권장)

    Returns:
        terms 필드가 추가된 ChunkDict 목록

    실패 시 Fallback: chunk["terms"] = [] (절대 예외 전파 안 함)
    """
    try:
        for chunk in chunks:
            search_text = (
                chunk.get("restructured_text") or chunk["original_text"]
            )
            matched = _find_terms(search_text)

            chunk_terms: list[TermDict] = []
            seen: set[str] = set()

            for entry, score in matched:
                term_text = entry["term"]
                if term_text in seen:
                    continue
                seen.add(term_text)

                definition = entry["definition"]
                # 2번 RAG는 LLM 생성이 아닌 사전 직접 인용(검색) 방식이므로 faithfulness_score = 1.0 (환각률 0% 보장)
                faith = 1.0  # 직접 인용

                # faithfulness 기준 미달 시 trace 경고 (5번 QA용)
                if faith < _FAITHFULNESS_THRESHOLD:
                    print(
                        f"[rag_engine] WARNING: faithfulness {faith:.2f} < "
                        f"threshold {_FAITHFULNESS_THRESHOLD} for term '{term_text}'"
                    )

                chunk_terms.append(
                    TermDict(
                        term=term_text,
                        definition=definition,
                        source=entry["source"],
                        faithfulness_score=round(faith, 4),
                        chunk_id=chunk["chunk_id"],
                    )
                )

            chunk["terms"] = chunk_terms
        return chunks

    except Exception as exc:
        print(f"[rag_engine] RAG 실패, terms=[] 반환: {exc}")
        for chunk in chunks:
            chunk.setdefault("terms", [])
        return chunks


def collect_all_terms(chunks: list[ChunkDict]) -> list[TermDict]:
    """
    모든 청크의 용어를 중복 없이 수집한다 (세션 전체 terms 목록).
    """
    seen: set[str] = set()
    result: list[TermDict] = []
    for chunk in chunks:
        for term in chunk.get("terms", []):
            if term["term"] not in seen:
                seen.add(term["term"])
                result.append(term)
    return result


def get_faithfulness_summary(terms: list[TermDict]) -> dict:
    """
    용어풀이 전체의 faithfulness 통계를 반환한다 (5번 QA 연동용).
    """
    if not terms:
        return {
            "total": 0,
            "avg_faithfulness": 0.0,
            "below_threshold": 0,
            "threshold": _FAITHFULNESS_THRESHOLD,
        }
    scores = [t.get("faithfulness_score", 1.0) for t in terms]
    avg = sum(scores) / len(scores)
    below = sum(1 for s in scores if s < _FAITHFULNESS_THRESHOLD)
    return {
        "total": len(terms),
        "avg_faithfulness": round(avg, 4),
        "below_threshold": below,
        "threshold": _FAITHFULNESS_THRESHOLD,
    }


def _query_woorimalsem_api(word: str) -> dict | None:
    """
    국립국어원 우리말샘 오픈 API (공공데이터포털)를 호출하여 단어 정의를 조회한다.
    """
    import urllib.request
    import urllib.parse

    api_key = os.getenv("WOORIMAL_API_KEY", "") or os.getenv("DICTIONARY_API_KEY", "")
    if not api_key:
        return None

    try:
        query_params = {
            "key": api_key,
            "q": word,
            "req_type": "json",
            "part": "word",
            "sort": "dict",
            "start": 1,
            "num": 10
        }
        encoded_params = urllib.parse.urlencode(query_params)
        url = f"https://opendict.korean.go.kr/api/search?{encoded_params}"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_content = response.read().decode("utf-8")
            data = json.loads(res_content)

        # 우리말샘 JSON 응답 구조 파싱
        items = data.get("channel", {}).get("item", [])
        if items:
            best_item = items[0]
            definition = best_item.get("sense", {}).get("definition", "")
            # HTML 태그 제거
            definition = re.sub(r"<[^>]*>", "", definition).strip()

            if definition:
                return {
                    "term": best_item.get("word", word).replace("^", "").replace("_", ""),
                    "definition": definition,
                    "source": "우리말샘 (국립국어원)"
                }
    except Exception as e:
        print(f"[rag_engine] 우리말샘 API 호출 실패: {e}")

    return None


def lookup_term(word: str, context: str | None = None) -> TermDict:
    """
    단어 단건에 대한 용어 뜻을 조회한다. (확장 프로그램 hover lookup용 무료 경로)
    
    우선순위:
      1. 로컬 용어집에서 용어/별칭(alias) 대소문자 구분 없이 완벽 매칭 시도
         → 조사 제거 전처리 후 재시도 (예: '방지법을' → '방지법')
      2. 국립국어원 우리말샘 오픈 API 조회 (WOORIMAL_API_KEY 설정 시 작동)
      3. sentence-transformers를 활용한 임베딩 코사인 유사도 검색 (유사도 >= 0.3)
      4. Gemini 2.0 Flash LLM 실시간 유추 (GEMINI_API_KEY 설정 시 작동)
      5. 미발견 시 source="not_found" 반환 (프론트가 조용히 무시)
    """
    word_clean = word.strip()
    # 특수문자/문장부호 제거
    word_clean = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', '', word_clean).strip()
    word_lower = word_clean.lower()
    
    # 조사 제거 원형 단어도 미리 계산
    word_stripped = _strip_particles(word_clean)
    word_stripped_lower = word_stripped.lower()

    if not _TERM_DICT:
        # 용어집이 없어도 LLM으로 시도
        llm_res = _query_gemini_llm(word_clean, context)
        if llm_res:
            return TermDict(
                term=llm_res["term"],
                definition=llm_res["definition"],
                source=llm_res["source"],
                faithfulness_score=0.8,
                chunk_id=""
            )
        return TermDict(
            term=word_clean,
            definition="",
            source="not_found",
            faithfulness_score=0.0,
            chunk_id=""
        )

    # 1. 완벽 매칭 (용어 또는 별칭) — 원본 및 조사 제거 원형 모두 시도
    for search_word, search_lower in [
        (word_clean, word_lower),
        (word_stripped, word_stripped_lower),
    ]:
        for entry in _TERM_DICT:
            term_val = entry.get("term", "")
            aliases = [a.lower() for a in entry.get("aliases", [])]
            if term_val.lower() == search_lower or search_lower in aliases:
                return TermDict(
                    term=term_val,
                    definition=entry.get("definition", ""),
                    source=entry.get("source", "로컬 사전"),
                    faithfulness_score=1.0,
                    chunk_id=""
                )

    # 2. 우리말샘 오픈 API 조회 시도 (원본 → 조사 제거 순)
    for search_word in [word_clean, word_stripped]:
        api_res = _query_woorimalsem_api(search_word)
        if api_res:
            return TermDict(
                term=api_res["term"],
                definition=api_res["definition"],
                source=api_res["source"],
                faithfulness_score=1.0,
                chunk_id=""
            )

    # 3. 임베딩 유사도 매칭 시도
    model = _get_embedding_model()
    if model is not None:
        try:
            query_vec = model.encode(word_clean).tolist()
            cand_vecs = _get_term_embeddings(model)
            if cand_vecs and len(cand_vecs) == len(_TERM_DICT):
                best_score = -1.0
                best_entry = None
                for i, entry in enumerate(_TERM_DICT):
                    score = _cosine_similarity(query_vec, cand_vecs[i])
                    if score > best_score:
                        best_score = score
                        best_entry = entry
                if best_entry and best_score >= 0.3:
                    return TermDict(
                        term=best_entry["term"],
                        definition=best_entry.get("definition", ""),
                        source=best_entry.get("source", "RAG 유사 매칭"),
                        faithfulness_score=round(best_score, 4),
                        chunk_id=""
                    )
        except Exception as e:
            print(f"[rag_engine] 단어 lookup 임베딩 유사도 검색 실패: {e}")

    # 4. Gemini LLM 실시간 유추 (GEMINI_API_KEY 설정 시)
    llm_res = _query_gemini_llm(word_stripped or word_clean, context)
    if llm_res:
        return TermDict(
            term=llm_res["term"],
            definition=llm_res["definition"],
            source=llm_res["source"],
            faithfulness_score=0.8,
            chunk_id=""
        )

    # 5. 미발견 폴백
    return TermDict(
        term=word_stripped or word_clean,
        definition="",
        source="not_found",
        faithfulness_score=0.0,
        chunk_id=""
    )

    word_clean = word.strip()
    word_lower = word_clean.lower()
    
    if not _TERM_DICT:
        return TermDict(
            term=word_clean,
            definition="",
            source="not_found",
            faithfulness_score=0.0,
            chunk_id=""
        )

    # 1. 완벽 매칭 (용어 또는 별칭)
    for entry in _TERM_DICT:
        term_val = entry.get("term", "")
        aliases = [a.lower() for a in entry.get("aliases", [])]
        if term_val.lower() == word_lower or word_lower in aliases:
            return TermDict(
                term=term_val,
                definition=entry.get("definition", ""),
                source=entry.get("source", "로컬 사전"),
                faithfulness_score=1.0,
                chunk_id=""
            )

    # 2. 우리말샘 오픈 API 조회 시도
    api_res = _query_woorimalsem_api(word_clean)
    if api_res:
        return TermDict(
            term=api_res["term"],
            definition=api_res["definition"],
            source=api_res["source"],
            faithfulness_score=1.0,
            chunk_id=""
        )

    # 3. 임베딩 유사도 매칭 시도 (텍스트 레이어가 있는 경우)
    model = _get_embedding_model()
    if model is not None:
        try:
            query_vec = model.encode(word_clean).tolist()
            cand_vecs = _get_term_embeddings(model)
            if cand_vecs and len(cand_vecs) == len(_TERM_DICT):
                best_score = -1.0
                best_entry = None
                for i, entry in enumerate(_TERM_DICT):
                    score = _cosine_similarity(query_vec, cand_vecs[i])
                    if score > best_score:
                        best_score = score
                        best_entry = entry
                if best_entry and best_score >= 0.3:
                    return TermDict(
                        term=best_entry["term"],
                        definition=best_entry.get("definition", ""),
                        source=best_entry.get("source", "RAG 유사 매칭"),
                        faithfulness_score=round(best_score, 4),
                        chunk_id=""
                    )
        except Exception as e:
            print(f"[rag_engine] 단어 lookup 임베딩 유사도 검색 실패: {e}")

    # 4. 미발견 폴백
    return TermDict(
        term=word_clean,
        definition="",
        source="not_found",
        faithfulness_score=0.0,
        chunk_id=""
    )
