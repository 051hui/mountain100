import json
import streamlit as st
from typing import Any, Dict, Optional
import google.generativeai as genai


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """
        Gemini API 클라이언트 초기화
        
        Args:
            api_key: API 키 (없으면 secrets에서 가져옴)
            model: 사용할 모델명
        """
        self.api_key = api_key or st.secrets["GEMINI_API_KEY"]
        self.model = model
        
        # Gemini SDK 초기화
        genai.configure(api_key=self.api_key)
        self._client = genai.GenerativeModel(model_name=self.model)

    def complete_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Gemini API를 사용하여 텍스트 생성
        
        Args:
            system_prompt: 시스템 프롬프트 (역할 정의)
            user_prompt: 사용자 프롬프트 (실제 요청)
            temperature: 응답 다양성 (0.0~1.0, 높을수록 창의적)
            
        Returns:
            생성된 텍스트 (translation의 경우 JSON 문자열)
        """
        try:
            # system_instruction과 함께 모델 생성
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_prompt
            )
            
            # generation_config 설정
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            
            # 텍스트 생성
            response = model.generate_content(
                user_prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            st.error(f"Gemini API 호출 오류: {e}")
            raise


def parse_json_strict(text: str) -> Dict[str, Any]:
    """
    LLM 출력에서 JSON을 안전하게 파싱
    
    Args:
        text: LLM이 생성한 텍스트
        
    Returns:
        파싱된 JSON 딕셔너리
    """
    t = text.strip()
    
    # 코드펜스 방어 (모델이 규칙을 어겼을 때 대비)
    if t.startswith("```"):
        t = t.strip("`").strip()
        if t.lower().startswith("json"):
            t = t[4:].strip()
    
    return json.loads(t)