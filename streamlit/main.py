"""
Streamlit 산·등산로 개인화 추천 시스템 (멀티페이지)

실행 전:
1. python train_model.py 실행하여 모델 저장 <-- 얜 아님(아마도)‼️
2. .streamlit/secrets.toml에 GEMINI_API_KEY 설정‼

실행: streamlit run main.py
"""

import streamlit as st

# =============================================================================
# 앱 전체 설정
# =============================================================================
st.set_page_config(
    page_title="오르樂 내리樂 : 산·등산로 추천 시스템",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# 앱 전체 스타일 설정
# =============================================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"], p, div, h1, h2, h3, h4, h5, h6, span, button, input, textarea, label {
        font-family: 'IBM Plex Sans KR', sans-serif !important;
    }
    
    .st-emotion-cache-ixgm6x, .st-emotion-cache-4si8ij, .st-emotion-cache-xt25cl {
        font-family: 'Material Symbols Rounded' !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)



# =============================================================================
# 페이지 정의 (st.Page)
# =============================================================================
home_page = st.Page(
    page="pages/01_home.py",
    title="홈",
    icon="🏠",
    default=True
)

analysis_page = st.Page(
    page="pages/02_analysis.py",
    title="등산로 분석",
    icon="🥾"
)

trail_page = st.Page(
    page="pages/03_trail.py",
    title="맞춤 등산로 조회",
    icon="🔍"
)

mountain_page = st.Page(
    page="pages/04_mountain.py",
    title="산 정보 조회",
    icon="⛰️"
)


chatbot_page = st.Page(
    page="pages/05_chatbot.py",
    title="AI 등산로 추천",
    icon="💬"
)

# =============================================================================
# 네비게이션 구성 (st.navigation)
# =============================================================================
pg = st.navigation({
    "메인": [home_page],
    "기능": [analysis_page, trail_page, mountain_page, chatbot_page]
})

# =============================================================================
# 공통 사이드바
# =============================================================================
with st.sidebar:
    st.caption("© 2025 내일배움캠프 여행갈4람")

# =============================================================================
# 페이지 실행
# =============================================================================
pg.run()
