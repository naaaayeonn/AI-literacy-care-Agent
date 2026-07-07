# -*- coding: utf-8 -*-
import json
import os
from pathlib import Path

# 기존 term_dictionary.json 경로
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DICT_PATH = PROJECT_ROOT / "data" / "term_dictionary.json"

# 기존 데이터 로드
if DICT_PATH.exists():
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {
        "version": "1.0.0",
        "description": "AI 리터러시 케어 에이전트 용어집 — 신뢰 출처 기반 RAG 데이터 (M1)",
        "terms": []
    }

existing_terms = {t["term"] for t in data["terms"]}

# 추가할 용어 정의 (IT 및 교육/일반 도메인 총 80개 이상 추가)
additional_terms = [
    # --- IT 도메인 추가 ---
    {
        "term": "데이터베이스",
        "aliases": ["DB", "database"],
        "definition": "체계적으로 정리된 데이터의 집합으로, 여러 사람이 공유하여 사용할 수 있도록 구조화된 정보의 저장소.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "클라우드 컴퓨팅",
        "aliases": ["cloud computing", "클라우드"],
        "definition": "인터넷을 통해 서버, 스토리지, 데이터베이스, 네트워크 등 컴퓨팅 서비스를 필요에 따라 유연하게 제공하는 기술.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "프론트엔드",
        "aliases": ["frontend"],
        "definition": "웹사이트나 웹 애플리케이션에서 사용자가 직접 눈으로 보고 상호작용하는 화면과 영역.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "백엔드",
        "aliases": ["backend"],
        "definition": "웹 애플리케이션의 뒷단에서 사용자 눈에 보이지 않게 데이터를 처리하고 저장하는 영역.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "사용자 인터페이스",
        "aliases": ["UI", "User Interface"],
        "definition": "사용자가 디지털 디바이스나 소프트웨어와 상호작용할 수 있도록 돕는 화면 구성, 버튼 등의 시각적 매개체.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "사용자 경험",
        "aliases": ["UX", "User Experience"],
        "definition": "사용자가 어떤 시스템이나 서비스를 직·간접적으로 이용하면서 느끼는 총체적인 감정과 경험.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "암호화",
        "aliases": ["encryption"],
        "definition": "데이터의 내용을 승인받지 않은 제3자가 알 수 없도록 특별한 규칙을 이용해 변환하는 과정.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "복호화",
        "aliases": ["decryption"],
        "definition": "암호화된 데이터를 다시 원래의 평문 상태로 복원하는 과정.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "사물인터넷",
        "aliases": ["IoT", "Internet of Things"],
        "definition": "각종 사물에 센서와 통신 기능을 내장하여 인터넷에 연결하고 서로 데이터를 주고받게 하는 기술.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "빅데이터",
        "aliases": ["big data"],
        "definition": "기존 데이터베이스 관리 도구로는 다루기 어려울 정도로 막대하고 다변화된 대량의 데이터 집합.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "블록체인",
        "aliases": ["blockchain"],
        "definition": "데이터를 분산 저장하고 해시 체인을 통해 검증함으로써 임의 조작을 원천적으로 막는 분산 원장 기술.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "도커",
        "aliases": ["Docker"],
        "definition": "소프트웨어를 컨테이너라는 독립된 표준 가상화 패키지로 묶어 어디서나 동일하게 실행되도록 돕는 도구.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "쿠버네티스",
        "aliases": ["Kubernetes", "K8s"],
        "definition": "수많은 컨테이너화된 애플리케이션의 배포, 확장, 관리를 자동화해 주는 오픈소스 오케스트레이션 플랫폼.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "파이썬",
        "aliases": ["Python"],
        "definition": "가독성이 높고 문법이 간결하여 다양한 분야, 특히 인공지능과 데이터 분석에서 널리 쓰이는 고급 프로그래밍 언어.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "컴파일러",
        "aliases": ["compiler"],
        "definition": "사람이 작성한 프로그래밍 언어 소스 코드를 컴퓨터가 직접 실행할 수 있는 기계어로 한꺼번에 번역해 주는 프로그램.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "인터프리터",
        "aliases": ["interpreter"],
        "definition": "프로그래밍 언어의 소스 코드를 한꺼번에 번역하지 않고, 한 행씩 읽어 들여 즉시 실행하는 프로그램.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "방화벽",
        "aliases": ["firewall"],
        "definition": "네트워크 외부의 비정상적인 접근을 차단하고, 허가된 통신만 허용하도록 설계된 하드웨어 및 소프트웨어 보안 시스템.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "랜섬웨어",
        "aliases": ["ransomware"],
        "definition": "사용자의 컴퓨터 파일을 모두 암호화하여 인질로 잡고, 해독해 주는 대가로 금전을 요구하는 악성 프로그램.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "데이터 분석",
        "aliases": ["data analysis"],
        "definition": "유용한 정보를 발굴하고 결론을 도출하여 의사결정을 돕기 위해 데이터를 정리, 가공, 검사하는 과정.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "중앙처리장치",
        "aliases": ["CPU", "Central Processing Unit"],
        "definition": "컴퓨터 시스템의 모든 컴퓨터 연산과 제어 명령을 실행하는 가장 핵심적인 반도체 하드웨어 장치.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "그래픽처리장치",
        "aliases": ["GPU", "Graphics Processing Unit"],
        "definition": "대규모 대화형 그래픽과 병렬 처리에 특화된 연산 장치. 최근 인공지능 모델 학습에 필수적으로 쓰인다.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "피싱",
        "aliases": ["phishing"],
        "definition": "가짜 웹사이트나 이메일을 통해 사용자를 속여 비밀번호나 카드 정보 같은 중요 개인정보를 갈취하는 사기 수법.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "깃",
        "aliases": ["Git"],
        "definition": "소스 코드의 변경 이력을 관리하고 여러 명의 개발자가 효율적으로 협업할 수 있도록 돕는 분산 버전 관리 시스템.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "버전 관리",
        "aliases": ["version control", "형상 관리"],
        "definition": "파일이나 프로그램의 소스 코드 변경 이력을 기록하여, 오류 발생 시 이전 시점으로 쉽게 되돌리거나 병합할 수 있게 돕는 시스템.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "클라이언트",
        "aliases": ["client"],
        "definition": "네트워크 상에서 서버에 서비스나 자원을 요청하고 이를 받아 사용하는 사용자용 컴퓨터 또는 소프트웨어.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "서버",
        "aliases": ["server"],
        "definition": "네트워크를 통해 연결된 다른 컴퓨터(클라이언트)들에게 정보나 서비스를 제공하는 중심 컴퓨터 시스템.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "프로토콜",
        "aliases": ["protocol"],
        "definition": "컴퓨터나 네트워크 장비들이 서로 원활하게 통신하기 위해 정의한 약속이자 통신 규약.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "도메인 네임",
        "aliases": ["domain name", "도메인"],
        "definition": "숫자로 이루어진 복잡한 인터넷 IP 주소를 사람이 기억하기 쉽게 문자로 표현한 고유한 인터넷 주소.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "스토리지",
        "aliases": ["storage", "저장소"],
        "definition": "대량의 디지털 데이터를 장기간 안전하게 보관하기 위한 물리적 혹은 가상의 대용량 저장 매체.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "가상 머신",
        "aliases": ["VM", "virtual machine"],
        "definition": "하나의 물리적 컴퓨터 환경 위에서 소프트웨어로 하드웨어를 에뮬레이션하여 독립된 OS를 구동하는 가상 컴퓨터.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "운영체제",
        "aliases": ["OS", "Operating System"],
        "definition": "컴퓨터 하드웨어와 사용자 사이의 인터페이스 역할을 하며, 시스템 자원을 관리하는 핵심 시스템 소프트웨어.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "해시 함수",
        "aliases": ["hash function", "해시"],
        "definition": "임의의 길이를 가진 데이터를 고정된 길이의 고유한 문자열이나 숫자로 바꾸는 수학적 알고리즘.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "데이터 웨어하우스",
        "aliases": ["Data Warehouse", "DW"],
        "definition": "기업이나 조직의 효율적인 의사결정을 돕기 위해 여러 시스템으로부터 수집한 통합 분석용 데이터베이스.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "소프트웨어 라이프사이클",
        "aliases": ["Software Lifecycle", "소프트웨어 생명 주기"],
        "definition": "소프트웨어의 계획, 요구 분석, 설계, 개발, 테스트, 운영 및 유지보수에 이르는 전체적인 생애 주기 단계.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "마이크로서비스",
        "aliases": ["Microservices", "MSA"],
        "definition": "하나의 큰 애플리케이션을 결합도가 낮은 독립적인 여러 작은 서비스 단위로 쪼개어 개발하고 배포하는 아키텍처.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "클래스",
        "aliases": ["class"],
        "definition": "객체 지향 프로그래밍에서 특정 종류의 객체를 생성하기 위해 속성과 메서드를 정의해 둔 일종의 설계도.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "상속",
        "aliases": ["inheritance"],
        "definition": "이미 정의된 클래스의 속성과 기능을 그대로 물려받아 새로운 자식 클래스를 신속하게 만드는 프로그래밍 기법.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "다형성",
        "aliases": ["polymorphism"],
        "definition": "동일한 메서드 호출이 객체의 실제 타입에 따라 서로 다른 방식으로 동작하도록 구현하는 객체 지향 프로그래밍의 특성.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "캡슐화",
        "aliases": ["encapsulation"],
        "definition": "클래스 내부의 세부 구현이나 데이터를 외부로부터 숨기고 필수 인터페이스만 노출하여 무결성을 보호하는 방법.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "버그",
        "aliases": ["bug"],
        "definition": "컴퓨터 프로그램이 개발자가 예상치 못한 잘못된 결과를 내거나 오작동하도록 만드는 소스 코드상의 결함이나 오류.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "디버깅",
        "aliases": ["debugging"],
        "definition": "컴퓨터 프로그램 내부에 존재하는 프로그램의 원인(버그)을 찾아내고 이를 올바르게 수정하는 일련의 작업 과정.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "SQL",
        "aliases": ["Structured Query Language"],
        "definition": "관계형 데이터베이스에 저장된 데이터를 검색, 입력, 수정, 삭제하는 등의 관리를 위해 사용하는 관계형 표준 질의 언어.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "관계형 데이터베이스",
        "aliases": ["RDBMS", "Relational Database"],
        "definition": "데이터를 행과 열을 가진 표(Table) 형태로 정리하고, 각 테이블 간의 논리적 관계를 설정하여 데이터를 관리하는 시스템.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "NoSQL",
        "aliases": ["Not Only SQL"],
        "definition": "전통적인 관계형 테이블 형식을 벗어나, 비정형·대용량 데이터를 유연하게 저장하기 위한 분산 데이터베이스 기술의 총칭.",
        "source": "도메인 용어집 IT 편",
        "domain": "IT"
    },
    {
        "term": "인덱스",
        "aliases": ["index", "색인"],
        "definition": "데이터베이스에서 원하는 정보를 빠르게 검색할 수 있도록 테이블의 특정 데이터를 정렬하여 별도로 보관하는 색인 장치.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "트랜잭션",
        "aliases": ["transaction"],
        "definition": "데이터베이스 관리에서 작업의 완전성을 보장하기 위해 한꺼번에 수행되어야 하는 논리적인 연산 단위들의 집합.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "REST",
        "aliases": ["Representational State Transfer"],
        "definition": "웹의 기존 기술인 HTTP 프로토콜을 그대로 활용하여 분산 자원들의 고유 주소를 기반으로 설계하는 아키텍처 스타일.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "포트",
        "aliases": ["port"],
        "definition": "컴퓨터나 서버에서 통신을 수행할 때 외부의 다른 디바이스나 프로세스와 연결하기 위한 가상의 통신 연결 통로.",
        "source": "표준국어대사전",
        "domain": "IT"
    },
    {
        "term": "IP 주소",
        "aliases": ["IP address", "IP"],
        "definition": "인터넷에 연결된 모든 디바이스들이 가지는 컴퓨터 네트워크 상의 고유한 논리 식별 번호.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "인터넷 프로토콜",
        "aliases": ["IP", "Internet Protocol"],
        "definition": "송신 호스트에서 수신 호스트까지 데이터를 온전하게 보내기 위해 약속한 컴퓨터 네트워크 계층의 핵심 통신 규약.",
        "source": "한국정보통신기술협회(TTA) 정보통신용어사전",
        "domain": "IT"
    },
    {
        "term": "웹 브라우저",
        "aliases": ["browser", "브라우저"],
        "definition": "인터넷 웹 서버에 보관되어 있는 다양한 정보들을 화면으로 읽고 상호작용할 수 있도록 변환해 주는 뷰어 프로그램.",
        "source": "표준국어대사전",
        "domain": "IT"
    },

    # --- 교육 및 일반 도메인 추가 ---
    {
        "term": "인지 발달",
        "aliases": ["cognitive development"],
        "definition": "개인이 성장하면서 주변 세상을 지각하고 지식, 이해력, 사고를 넓혀가는 지적 성장의 단계별 발달 과정.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "비계 설정",
        "aliases": ["스캐폴딩", "scaffolding"],
        "definition": "아동이나 학습자가 스스로 해결할 수 없는 과제에 직면했을 때 교사나 동료가 일시적으로 조력과 힌트를 제공하는 교수 방법.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "자기주도학습",
        "aliases": ["self-directed learning"],
        "definition": "학습자가 주체가 되어 자신의 교육 요구를 진단하고, 목표를 설정하고, 적합한 전략을 찾아 스스로 실행 및 평가하는 주체적 학습 형태.",
        "source": "교육학대사전",
        "domain": "교육"
    },
    {
        "term": "학습 동기",
        "aliases": ["learning motivation", "학습동기"],
        "definition": "특정한 학습 활동을 시작하고, 그 방향을 설정하며, 적극적인 학습 태도를 끝까지 유지하도록 돕는 내적인 심리 욕구.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "피아제의 발달이론",
        "aliases": ["Jean Piaget", "피아제"],
        "definition": "장 피아제가 제안한 인간 인지 구조의 네 가지 주요 발달 단계(감각운동기, 전조작기, 구체적 조작기, 형식적 조작기)를 다룬 발달이론.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "비고츠키 사회문화이론",
        "aliases": ["Lev Vygotsky", "비고츠키"],
        "definition": "레프 비고츠키가 제안한 이론으로, 아동의 고차적 지적 발달이 사회적 상호작용과 언어 도구의 사용을 통해 사회문화적으로 형성된다고 주장하는 이론.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "근접 발달 영역",
        "aliases": ["ZPD", "Zone of Proximal Development"],
        "definition": "독립적으로 해결할 수 있는 현재 발달 수준과 유능한 타인의 도움을 받아 도달할 수 있는 잠재적 발달 수준 사이의 지적 영역.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "형성 평가",
        "aliases": ["formative evaluation", "형성평가"],
        "definition": "교수·학습 과정 중에 학생의 이해도를 즉시 파악하여 가르치는 방식을 개선하고 피드백을 주기 위해 실시하는 주기적인 약식 평가.",
        "source": "교육학대사전",
        "domain": "교육"
    },
    {
        "term": "총괄 평가",
        "aliases": ["summative evaluation", "총합평가"],
        "definition": "일정 교과 과정이나 단원이 모두 끝난 시점에 최종 성적을 부여하고 목표 달성 정도를 확인하기 위해 치르는 종합 평가.",
        "source": "교육학대사전",
        "domain": "교육"
    },
    {
        "term": "피드백",
        "aliases": ["feedback"],
        "definition": "학습자의 반응이나 결과에 대하여, 학습의 방향을 수정하거나 올바르게 교정해 주기 위해 제공하는 모든 반응이자 교정 정보.",
        "source": "표준국어대사전",
        "domain": "교육"
    },
    {
        "term": "교육과정",
        "aliases": ["curriculum"],
        "definition": "학교나 학교 밖 교육 기관에서 학습자가 달성해야 할 교육 목적에 맞춰 체계적으로 편성한 종합적인 교육 계획표이자 계획.",
        "source": "표준국어대사전",
        "domain": "교육"
    },
    {
        "term": "학습 장애",
        "aliases": ["learning disability"],
        "definition": "정상적인 지능을 가졌음에도 불구하고 신경학적 요인 등으로 인해 읽기, 쓰기, 수학적 추론 등의 특정 학습 기능에서 뚜렷한 장애를 보이는 상태.",
        "source": "특수교육학 용어사전",
        "domain": "교육"
    },
    {
        "term": "주의력결핍 과잉행동장애",
        "aliases": ["ADHD"],
        "definition": "아동기나 청소년기에 흔히 나타나는 정신과적 질환으로, 산만함과 충동성, 주의력 결핍 등을 특징으로 하는 장애.",
        "source": "의학학술지 용어사전",
        "domain": "교육"
    },
    {
        "term": "난독증",
        "aliases": ["dyslexia"],
        "definition": "지능과 시각, 청각은 지극히 정상이나 글자를 해독하고 유창하게 읽는 과정에 뚜렷한 곤란을 겪는 읽기 기능 상의 장애.",
        "source": "특수교육학 용어사전",
        "domain": "교육"
    },
    {
        "term": "문맥",
        "aliases": ["context"],
        "definition": "글이나 말에서 특정 단어가 사용되었을 때 그 앞뒤에 나타나는 내용의 연결 관계와 전체적인 언어 상황.",
        "source": "표준국어대사전",
        "domain": "교육"
    },
    {
        "term": "지각",
        "aliases": ["perception"],
        "definition": "오감을 통한 자극을 뇌에서 종합하여 주변 대상의 성질이나 현재 처한 환경적 상황을 파악하는 인간의 심리 과정.",
        "source": "표준국어대사전",
        "domain": "교육"
    },
    {
        "term": "단기 기억",
        "aliases": ["short-term memory", "단기기억"],
        "definition": "외부의 정보가 감각 등록기를 거쳐 전달된 후 수십 초 이내의 아주 짧은 시간 동안만 뇌 속에 임시 보관되는 기억 상태.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "장기 기억",
        "aliases": ["long-term memory", "장기기억"],
        "definition": "뇌 속에서 반영구적 혹은 영구적으로 보존되는 정보 저장소. 무제한에 가까운 엄청난 저장 용량을 가진다.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "작업 기억",
        "aliases": ["working memory", "작업기억"],
        "definition": "특정한 지적 과제를 수행할 때, 필요한 정보들을 일시적으로 기억에 유지하면서 복잡한 추론과 가공 작업을 진행하는 능동적 기억 영역.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "학습부진",
        "aliases": ["underachievement"],
        "definition": "지적 능력 수준은 지극히 정상이나 교수 방법, 심리적 요인, 환경 탓으로 교육 목표에 미달하는 학업 성취도를 보이는 상태.",
        "source": "교육학대사전",
        "domain": "교육"
    },
    {
        "term": "비판적 사고",
        "aliases": ["critical thinking"],
        "definition": "어떤 논증이나 지식을 맹목적으로 받아들이지 않고, 그 사실 논리적 신뢰성이나 전제를 따져 타당성을 검토하는 적극적인 사고방식.",
        "source": "철학학술 사전",
        "domain": "교육"
    },
    {
        "term": "다중 지능 이론",
        "aliases": ["multiple intelligences", "하워드 가드너"],
        "definition": "하워드 가드너가 제안한 지능 이론으로, 인간의 지능이 단일한 지표가 아닌 언어, 수학, 음악, 신체운동 등 최소 8가지 이상의 독립적 지능들로 구성된다는 주장.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "자아 효능감",
        "aliases": ["self-efficacy", "자기효능감"],
        "definition": "특정 과제를 마주했을 때 자신이 이를 성공적으로 끝마칠 수 있다고 생각하는 주체적 기대와 신념적 감정.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "수행 평가",
        "aliases": ["performance assessment", "수행평가"],
        "definition": "선택형 필기시험 위주 평가를 탈피하여, 학생이 자신의 결과물을 만드는 전체 행동 과정을 직접 관찰하고 평가하는 방식.",
        "source": "교육학대사전",
        "domain": "교육"
    },
    {
        "term": "창의성",
        "aliases": ["creativity", "창의력"],
        "definition": "새롭고 유용하며 가치 있는 생각이나 아이디어를 스스로 생성하고 실생활의 유용한 형태로 표출해 내는 정신적 능력.",
        "source": "표준국어대사전",
        "domain": "교육"
    },
    {
        "term": "협동 학습",
        "aliases": ["cooperative learning", "협동학습"],
        "definition": "소규모 학습 모둠을 구성하여 성원 간의 긍정적인 상호작용과 자율적 노력을 기반으로 공동의 목표를 달성하는 학습 모형.",
        "source": "교육학대사전",
        "domain": "교육"
    },
    {
        "term": "도식",
        "aliases": ["schema", "스키마"],
        "definition": "인간이 세상을 인지하고 환경에 적응하는 과정에서 머릿속에 형성하는 지식과 이해 행동의 조직체이자 인지 틀.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "동화",
        "aliases": ["assimilation"],
        "definition": "새로운 정보를 자신이 이미 소유하고 있는 인지 틀(스키마)에 맞춰 변형하여 수용하는 인지적 처리 방식.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "조절",
        "aliases": ["accommodation"],
        "definition": "기존 스키마로는 새로운 정보나 자극을 도저히 이해할 수 없을 때, 자신의 인지 구조 자체를 변형하고 고치는 인지적 조율 방법.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    },
    {
        "term": "평형화",
        "aliases": ["equilibration"],
        "definition": "아동이 동화와 조절 과정을 통해 주위 환경과 내부 인지 틀 사이의 부조화를 해결하고 인지적 평형 상태를 유지해 나가는 상태.",
        "source": "교육심리학 용어사전",
        "domain": "교육"
    }
]

# 중복 방지 병합
added_count = 0
for term in additional_terms:
    if term["term"] not in existing_terms:
        data["terms"].append(term)
        existing_terms.add(term["term"])
        added_count += 1

# 총 개수 확인
total_count = len(data["terms"])
print(f"추가된 용어 개수: {added_count}")
print(f"전체 용어 개수: {total_count}")

# 파일 다시 쓰기
with open(DICT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("term_dictionary.json 파일 업데이트 완료!")
