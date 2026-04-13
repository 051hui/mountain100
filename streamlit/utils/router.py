# router.py
import re


REFINE_PATTERNS = [
    r"더\s*(한적|조용|사람\s*적)",
    r"더\s*(쉬운|가벼운|초보)",
    r"더\s*(뷰|경치)",
    r"(별로|마음에\s*안|다른\s*거|다시|바꿔)",
    r"(너무\s*멀|가까운\s*걸로|거리)",
    r"(좀\s*더|조금\s*더|덜)",
]

EXPLAIN_PATTERNS = [
    r"(왜|이유|근거).*(추천|나왔|골랐)",
    r"(설명|소개).*(해줘|해봐|해주세요|알려줘)",
    r"(이\s*결과).*(왜|이유)",
    r"(어떻게|무슨\s*기준)",
    r"(자세히|상세히|더).*(알려|설명|소개)",
    r"\w+산.*\d+.*(코스|번).*(대해|설명|알려|소개)",  # "ㅇㅇ산 2번 코스에 대해"
]

# 추천 요청 패턴 강화
RECOMMEND_PATTERNS = [
    r"(추천|갈만한|어디\s*가|코스|등산로)",
    r"(찾아줘|골라줘|제안해줘|보여줘|알려줘)",
    r"(어디|어느|뭐)\s*(좋|괜찮)",
    r"\w+산.*(추천|가고|갈|코스|등산)",  # "ㅇㅇ산에서 추천", "ㅇㅇ산 가고싶어"
    r"(초급|중급|상급|쉬운|어려운).*(코스|등산로)",  # 난이도 언급
    r"(엄마|아빠|가족|친구).*(같이|함께)",  # 동행 언급
]

QUESTION_PATTERNS = [
    r"\w+산.*(어떤|어디|뭐가|어때)",  # "ㅇㅇ산은 어떤 산이야"
    r"\w+산.*(있어|있나|있는지)",  # "ㅇㅇ산에 코스 있어?"
    r"(뭐야|어때|가능|있어|없어|언제|어떻게)",
    r"(기준|정의|의미|특징)",
    r"(몇\s*개|얼마나|어느\s*정도)",
]


def route_intent(msg: str) -> str:
    """
    사용자 메시지의 의도를 분류
    
    Args:
        msg: 사용자 입력 메시지
        
    Returns:
        "recommend", "refine", "explain", "question", "other" 중 하나
    """
    m = msg.strip()
    
    # 순서가 중요: 더 구체적인 패턴을 먼저 체크
    
    # 1. 추천 수정 (가장 먼저 체크)
    if any(re.search(p, m) for p in REFINE_PATTERNS):
        return "refine"
    
    # 2. 설명 요청 (특정 코스에 대한 질문)
    if any(re.search(p, m) for p in EXPLAIN_PATTERNS):
        return "explain"
    
    # 3. 추천 요청 (산 이름 + 추천/코스 키워드)
    if any(re.search(p, m) for p in RECOMMEND_PATTERNS):
        return "recommend"
    
    # 4. 정보 질문 (산에 대한 일반 질문)
    if any(re.search(p, m) for p in QUESTION_PATTERNS):
        return "question"
    
    return "other"