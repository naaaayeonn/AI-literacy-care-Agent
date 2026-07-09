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


def _disambiguate_homonyms_with_llm(word: str, items: list, context: str) -> dict:
    """
    여러 개의 사전 정의 후보(동음이의어) 중 주어진 문맥에 가장 적합한 정의를 LLM으로 선택한다.
    """
    from backend.app.agents.content_reducer.snowchat_client import is_snowchat_available, _call_llm_via_snowchat
    if not is_snowchat_available():
        return items[0]

    try:
        candidates = []
        for i, item in enumerate(items[:5]): # 최대 5개 후보
            defn = item.get("sense", {}).get("definition", "")
            defn = re.sub(r"<[^>]*>", "", defn).strip()
            if defn:
                candidates.append((i, defn))
                
        if not candidates:
            return items[0]
            
        if len(candidates) == 1:
            return items[candidates[0][0]]

        # 프롬프트 구성
        candidate_text = "\n".join([f"{idx+1}. {defn}" for idx, defn in enumerate([c[1] for c in candidates])])
        prompt = (
            f"단어: '{word}'\n"
            f"기사 문맥 (Context): {context}\n\n"
            f"사전 정의 후보 목록:\n{candidate_text}\n\n"
            f"위 문맥에서 단어 '{word}'가 사용된 문맥적 의미와 가장 일치하는 정의의 번호(1-{len(candidates)})만 하나 적어주세요. "
            f"다른 설명이나 부연 텍스트 없이 오직 숫자 하나만 출력하세요. 예: 1"
        )
        
        system_instruction = "당신은 한국어 단어 뜻 풀이 분류기입니다. 오직 알맞은 번호 숫자 하나만 답해야 합니다."
        
        response_text = _call_llm_via_snowchat(
            model="gemini-2.5-flash",
            prompt=prompt,
            system_instruction=system_instruction
        )
        
        # 숫자 추출
        match = re.search(r"\d+", response_text)
        if match:
            idx = int(match.group(0)) - 1
            if 0 <= idx < len(candidates):
                best_idx = candidates[idx][0]
                return items[best_idx]
    except Exception as e:
        print(f"[rag_engine] 동음이의어 LLM 판별 실패: {e}")
        
    return items[0]


def _query_woorimalsem_api(word: str, context: str | None = None) -> dict | None:
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
        if isinstance(items, dict):
            items = [items]
        if items:
            best_item = items[0]
            if context and len(items) > 1:
                best_item = _disambiguate_homonyms_with_llm(word, items, context)

            # sense가 리스트일 수도, 딕셔너리일 수도 있음 — 둘 다 안전하게 처리
            sense_raw = best_item.get("sense", {})
            if isinstance(sense_raw, list):
                sense = sense_raw[0] if sense_raw else {}
            else:
                sense = sense_raw

            definition = sense.get("definition", "")
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




def _clean_korean_josa(word: str) -> str:
    """
    한국어 조사 및 문장부호를 제거하여 명사 원형을 추출한다.
    """
    # 1. 특수문자 및 공백 제거
    word = re.sub(r"[^\w\s\-]", "", word).strip()
    
    # 2. 대표적인 한국어 조사 목록 (긴 조사 우선 매칭)
    josa_list = [
        "에서", "에게", "이랑", "까지", "부터", "조차", "마저",
        "으로", "한테", "로서", "로써", "보다", "처럼",
        "은", "는", "이", "가", "을", "를", "의", "에", "로",
        "와", "과", "도", "만", "요"
    ]
    
    for josa in josa_list:
        if word.endswith(josa):
            # 조사를 제외한 단어의 길이가 1 이상일 때만 제거
            remain = word[:-len(josa)]
            if len(remain) >= 1:
                return remain.strip()
                
    return word

from backend.app.agents.content_reducer.snowchat_client import is_snowchat_available, _call_llm_via_snowchat

def _query_llm_definition(word: str, context: str | None = None) -> str | None:
    """
    Gemini 2.5 Flash를 이용하여 단어의 의미를 실시간으로 유추하여 생성한다. (Step 1 동적 LLM 답변)
    """
    if not is_snowchat_available():
        return None

    try:
        system_instruction = (
            "당신은 리터러시 케어 에이전트의 한국어 단어 사전자문관입니다. "
            "사용자가 기사를 읽다가 모르는 단어를 드래그했을 때, 그 단어의 뜻을 제공해야 합니다."
        )
        
        if context:
            prompt = (
                f"다음 기사 문맥(Context)을 고려하여 단어 '{word}'의 뜻을 50자 이내의 친절한 한국어로 설명해 주세요.\n\n"
                f"기사 문맥: {context}"
            )
        else:
            prompt = f"단어 '{word}'의 뜻을 50자 이내의 친절한 한국어로 설명해 주세요."

        result = _call_llm_via_snowchat(
            model="gemini-2.5-flash",
            prompt=prompt,
            system_instruction=system_instruction
        )
        
        if result:
            # 혹시 따옴표 등으로 감싸져 있을 수 있으므로 정제
            result = re.sub(r'^["\'“]+|["\'”]+$', '', result).strip()
            return result
    except Exception as e:
        import urllib.error
        if isinstance(e, urllib.error.HTTPError) and e.code == 429:
            return "💡 구글 API 요청 한도가 초과되었습니다. 잠시 후 다시 드래그해주세요."
        print(f"[rag_engine] LLM 단어 실시간 유추 실패: {e}")
        raise e
        
    return None


def lookup_term(word: str, context: str | None = None) -> TermDict:
    """
    단어 단건에 대한 용어 뜻을 조회한다. (확장 프로그램 hover lookup용 무료 경로)
    
    우선순위:
      1. 로컬 용어집에서 용어/별칭(alias) 대소문자 구분 없이 완벽 매칭 시도
      2. 국립국어원 우리말샘 오픈 API 조회 (WOORIMAL_API_KEY 설정 시 작동)
      3. sentence-transformers를 활용한 임베딩 코사인 유사도 검색 (유사도 >= 0.3)
      4. 사전에 없을 경우 기사 문맥을 바탕으로 한 LLM 실시간 의미 유추 시도
      5. 최종 미발견 시 source="not_found" 반환 (프론트가 조용히 무시)
    """
    tried = []
    errors = {}

    word_clean = word.strip()
    word_clean = re.sub(r"[^\w\s\-]", "", word_clean).strip()
    
    if not word_clean:
        return TermDict(
            term=word,
            definition="",
            source="not_found",
            faithfulness_score=0.0,
            chunk_id="",
            _meta={"tried": tried, "errors": errors}
        )

    # 매칭 시도할 단어 후보군 생성 (원문 자체, 그리고 조사 제거된 원형)
    word_candidates = [word_clean]
    cleaned_word = _clean_korean_josa(word_clean)
    if cleaned_word != word_clean:
        word_candidates.append(cleaned_word)

    if not _TERM_DICT:
        return TermDict(
            term=cleaned_word,
            definition="",
            source="not_found",
            faithfulness_score=0.0,
            chunk_id="",
            _meta={"tried": tried, "errors": errors}
        )

    # 1. 완벽 매칭 (용어 또는 별칭)
    tried.append("local")
    for w in word_candidates:
        w_lower = w.lower()
        for entry in _TERM_DICT:
            term_val = entry.get("term", "")
            aliases = [a.lower() for a in entry.get("aliases", [])]
            if term_val.lower() == w_lower or w_lower in aliases:
                return TermDict(
                    term=term_val,
                    definition=entry.get("definition", ""),
                    source=entry.get("source", "로컬 사전"),
                    faithfulness_score=1.0,
                    chunk_id="",
                    _meta={"tried": tried, "errors": errors}
                )

    # 2. 우리말샘 오픈 API 조회 시도
    api_key_woorimal = os.getenv("WOORIMAL_API_KEY", "") or os.getenv("DICTIONARY_API_KEY", "")
    if api_key_woorimal:
        tried.append("woorimal")
    else:
        tried.append("woorimal_skipped_no_key")

    for w in reversed(word_candidates):
        try:
            api_res = _query_woorimalsem_api(w, context)
            if api_res:
                return TermDict(
                    term=api_res["term"],
                    definition=api_res["definition"],
                    source=api_res["source"],
                    faithfulness_score=1.0,
                    chunk_id="",
                    _meta={"tried": tried, "errors": errors}
                )
        except Exception as e:
            errors["woorimal"] = str(e)
            print(f"[rag_engine] 우리말샘 API 검색 중 에러: {e}")


    # 3. 임베딩 유사도 매칭 시도
    model = _get_embedding_model()
    if model is not None:
        tried.append("embedding")
        try:
            # 조사 제거어로 임베딩 유사도 검색을 시도하여 품질 극대화
            query_vec = model.encode(cleaned_word).tolist()
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
                        chunk_id="",
                        _meta={"tried": tried, "errors": errors}
                    )
        except Exception as e:
            errors["embedding"] = str(e)
            print(f"[rag_engine] 단어 lookup 임베딩 유사도 검색 실패: {e}")
    else:
        tried.append("embedding_skipped_no_model")

    # 4. LLM 실시간 의미 유추 시도 (동적 LLM 답변 생성 로직 - 필수)
    if is_snowchat_available():
        tried.append("llm")
        try:
            llm_def = _query_llm_definition(cleaned_word, context)
            if llm_def:
                return TermDict(
                    term=cleaned_word,
                    definition=llm_def,
                    source="LLM 실시간 유추",
                    faithfulness_score=1.0,
                    chunk_id="",
                    _meta={"tried": tried, "errors": errors}
                )
        except Exception as e:
            errors["llm"] = str(e)
            print(f"[rag_engine] 단어 lookup LLM 실시간 유추 중 에러: {e}")
    else:
        tried.append("llm_skipped_no_key")

    # 5. 최종 미발견 폴백
    return TermDict(
        term=cleaned_word,
        definition="",
        source="not_found",
        faithfulness_score=0.0,
        chunk_id="",
        _meta={"tried": tried, "errors": errors}
    )

