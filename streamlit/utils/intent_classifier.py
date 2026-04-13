# utils/intent_classifier.py
"""
LLM 기반 의도 분류
패턴 매칭 대신 LLM이 유연하게 의도를 파악
"""
from utils.llm_client import GeminiClient


INTENT_SYSTEM_PROMPT = """당신은 등산로 추천 챗봇의 의도 분류 전문가입니다.

사용자 입력을 다음 5가지 중 하나로 분류하세요:

1. **recommend**: 새로운 등산로 추천 요청
   - 예: "힐링되는 곳", "가족과 갈만한 곳", "북한산 추천", "초급", "SNS 인증샷"
   - 산 이름만 언급해도 추천 요청
   - 스타일/난이도 키워드만 있어도 추천 요청

2. **refine**: 이전 추천 수정 요청
   - 예: "더 쉬운 곳", "좀 더 한적한", "별로야", "다른 거"
   - "더", "좀", "별로" 등이 있으면 대부분 수정 요청

3. **explain**: 추천 이유나 특정 코스 상세 설명 요청
   - 예: "왜 추천했어?", "가리산 01코스 설명해줘", "이유가 뭐야?"
   - 특정 코스명이 언급되면서 설명 요청

4. **question**: 산이나 등산에 대한 일반 질문
   - 예: "북한산은 어떤 산이야?", "황매산에 강아지 가능해?", "몇 개 코스 있어?"
   - 추천이 아닌 정보 질문

5. **other**: 위 어느 것도 아님
   - 예: "안녕", "고마워", "핫케이크 만드는 법"

**중요 규칙:**
- 산 이름 + 아무 말 → 대부분 recommend (예외: "어떤 산이야?"는 question)
- 스타일/난이도 키워드만 → recommend
- "?" 있어도 "추천", "찾아" 등 있으면 → recommend
- 맥락이 애매하면 recommend로 (추천이 핵심 기능)

**출력 형식:**
반드시 다음 중 하나만 출력하세요:
recommend
refine
explain
question
other

**절대 다른 설명이나 부연 없이 단어 하나만 출력하세요.**"""


def classify_intent_with_llm(
    client: GeminiClient, 
    user_input: str, 
    has_previous_results: bool = False
) -> str:
    """
    LLM을 사용하여 의도 분류
    
    Args:
        client: Gemini API 클라이언트
        user_input: 사용자 입력
        has_previous_results: 이전 추천 결과가 있는지 여부
        
    Returns:
        "recommend", "refine", "explain", "question", "other" 중 하나
    """
    
    context = ""
    if has_previous_results:
        context = "\n\n참고: 이전에 추천 결과가 있습니다. 사용자가 그것에 대해 말하는 것일 수 있습니다."
    
    user_prompt = f"""사용자 입력: "{user_input}"{context}

위 입력의 의도를 분류하세요. 
반드시 recommend, refine, explain, question, other 중 하나만 출력하세요."""

    try:
        # temperature 0으로 일관성 보장
        response = client.complete_text(
            INTENT_SYSTEM_PROMPT, 
            user_prompt, 
            temperature=0.0
        ).strip().lower()
        
        # 검증
        valid_intents = ["recommend", "refine", "explain", "question", "other"]
        if response in valid_intents:
            return response
        else:
            # LLM이 이상한 답을 하면 recommend로 (안전장치)
            print(f"Invalid intent from LLM: {response}, defaulting to recommend")
            return "recommend"
            
    except Exception as e:
        print(f"Intent classification failed: {e}")
        # 실패 시 기본값: recommend
        return "recommend"


def extract_mountain_name(user_input: str, all_mountains: list) -> str:
    """
    사용자 입력에서 산 이름 추출
    
    Args:
        user_input: 사용자 입력
        all_mountains: 모든 산 이름 리스트
        
    Returns:
        찾은 산 이름 또는 None
    """
    user_clean = user_input.replace(" ", "").replace("등산로", "").replace("추천", "").replace("코스", "")
    
    for mountain in all_mountains:
        mountain_clean = str(mountain).strip().replace(" ", "")
        
        # 여러 방법으로 매칭
        if (mountain_clean in user_clean or
            mountain_clean in user_input or
            str(mountain).strip() in user_input):
            return mountain
    
    return None
