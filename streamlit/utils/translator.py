# utils/translator.py
from typing import Dict, Any
from utils.llm_prompts import TRANSLATE_SYSTEM_PROMPT, make_translate_user_prompt
from utils.llm_client import GeminiClient, parse_json_strict


REQUIRED_KEYS = {
    "intent", "cluster_preference", "constraints", "exclude",
    "unavailable_needs", "clarifying_questions", "notes_for_ui"
}


def translate_plan(
    client: GeminiClient, 
    user_message: str, 
    intent: str,
    last_plan: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    사용자의 자연어를 추천 엔진 파라미터로 변환
    
    Args:
        client: Gemini API 클라이언트
        user_message: 사용자 입력 메시지
        intent: 의도 분류 결과 ("recommend" 또는 "refine")
        last_plan: 이전 추천 파라미터 (refine 시 사용)
        
    Returns:
        변환된 파라미터 딕셔너리
    """
    try:
        raw = client.complete_text(
            system_prompt=TRANSLATE_SYSTEM_PROMPT,
            user_prompt=make_translate_user_prompt(user_message, intent, last_plan),
        )
        
        plan = parse_json_strict(raw)
        
    except Exception as e:
        print(f"Translation 파싱 오류: {e}")
        plan = _fallback_plan(intent)
    
    # 필수 키 검증
    if not REQUIRED_KEYS.issubset(plan.keys()):
        missing = REQUIRED_KEYS - set(plan.keys())
        print(f"필수 키 누락: {missing}")
        plan = _fallback_plan(intent)
    
    # 안전장치: intent 강제
    plan["intent"] = intent
    
    # 길이 제한 및 기본값 설정
    plan["clarifying_questions"] = (plan.get("clarifying_questions") or [])[:2]
    plan["unavailable_needs"] = plan.get("unavailable_needs") or []
    plan["notes_for_ui"] = plan.get("notes_for_ui") or ""
    
    # constraints 기본값
    if not plan.get("constraints"):
        plan["constraints"] = {}
    
    # exclude 기본값
    if not plan.get("exclude"):
        plan["exclude"] = {"mountains": [], "trails": []}
    
    return plan


def _fallback_plan(intent: str) -> Dict[str, Any]:
    """파싱 실패 시 기본 플랜 반환"""
    return {
        "intent": intent,
        "cluster_preference": "any",
        "constraints": {
            "difficulty_min": None,
            "difficulty_max": None,
            "infra_min": None,
            "infra_max": None,
            "park_dist_max": None,
            "distance_max_km": None,
            "altitude_min_m": None,
            "altitude_max_m": None
        },
        "exclude": {"mountains": [], "trails": []},
        "unavailable_needs": [],
        "clarifying_questions": [],
        "notes_for_ui": "번역 결과를 파싱하지 못해 기본 기준으로 진행합니다."
    }
