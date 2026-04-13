import streamlit as st
import pandas as pd
import os
import gpxpy
import folium
from streamlit_folium import st_folium
from utils.trail_detail import show_trail_detail #-------------------------‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️

# -----------------------------------------------------------------------------
# 0. 데이터 로드 및 초기 설정 (기존과 동일하되 Cluster 컬럼 처리 확인)
# -----------------------------------------------------------------------------
@st.cache_data
def load_mountain_path():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        file_path = os.path.join(root_dir, 'data', '100mountains_dashboard.csv')
        
        df = pd.read_csv(file_path)
        
        full_columns = [
            '코스명', '산이름', '유형설명', '최고고도_m', '누적상승_m', '편도거리_km', '총거리_km', '예상시간_분', '예상시간', 
            '출발_lat', '출발_lon', '도착_lat', '도착_lon', '난이도', '세부난이도', '난이도점수',
            '관광인프라점수','주차장_접근성점수','정류장_접근성점수','코스수','가중치','매력종합점수',
            '전망','힐링','사진','등산로','성취감','계절매력','특출매력','특출점수',
            '주차장거리_m','정류장거리_m','위치', '주차장명', '정류장명', 'Cluster'
        ]
        
        if len(df.columns) == len(full_columns):
            df.columns = full_columns
        elif len(df.columns) >= 33: 
             df.columns = full_columns[:len(df.columns)]
        
        numeric_cols = ['난이도점수', '관광인프라점수', '매력종합점수', '주차장거리_m', '정류장거리_m', '총거리_km', '최고고도_m', 'Cluster']
        
        for col in numeric_cols:
            if col in df.columns:
                # 주차장 거리는 데이터가 없으면 -1로 채움 (0m와 구분하기 위해)
                if col == '주차장거리_m':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(-1)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        str_cols = ['주차장명', '정류장명', '위치']
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].fillna("-")
            
        return df
        
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {file_path}")
        return pd.DataFrame()

# ... (load_infra_data 함수는 기존 동일) ...
@st.cache_data
def load_infra_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        file_path = os.path.join(root_dir, 'data', '관광인프라.csv')
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

df = load_mountain_path()
df_infra = load_infra_data()

if df.empty:
    st.stop()

st.header("🔍 맞춤 등산로 조회")

difficulty_levels = ['입문', '초급', '중급', '상급', '최상급', '초인', '신']

# -----------------------------------------------------------------------------
# [변경] 클러스터 매핑 정의 ("전체 보기" 제거, 순수 데이터만 남김)
# -----------------------------------------------------------------------------
cluster_map = {
    "🌸 계절매력": 0,
    "📷 전망/사진": 2,
    "👨‍👩‍👧‍👦 가족/인프라": 3,
    "🌿 힐링": 4,
    "💎 오지/숨은명소": 5
}
cluster_options = list(cluster_map.keys())

# -----------------------------------------------------------------------------
# 1. 세션 상태 초기화
# -----------------------------------------------------------------------------
if 'diff_slider' not in st.session_state:
    st.session_state.diff_slider = ('입문', '신')
if 'infra_slider' not in st.session_state:
    st.session_state.infra_slider = (0.0, 10.0)
if 'park_dist_slider' not in st.session_state:
    st.session_state.park_dist_slider = 2000

def reset_infra_selection():
    if 'infra_list' in st.session_state:
        del st.session_state['infra_list']

# -----------------------------------------------------------------------------
# 2. 콜백 함수 (Cluster 선택 시 슬라이더 초기화 또는 프리셋 적용)
# -----------------------------------------------------------------------------
def set_search_condition():
    # 사용자가 테마(클러스터)를 바꿨을 때, 기존 필터가 방해되지 않도록
    # 슬라이더를 '전체 범위'로 초기화해주는 것이 좋습니다.
    # (필요하다면 클러스터 성격에 맞춰 범위를 좁혀줄 수도 있습니다)
    
    selection = st.session_state.type_selection
    target_cluster = cluster_map.get(selection)

    # 기본적으로 필터 초기화 (해당 클러스터의 모든 데이터를 보여주기 위함)
    st.session_state['diff_slider'] = ('입문', '신')
    st.session_state['infra_slider'] = (0.0, 10.0)
    st.session_state['park_dist_slider'] = 2000

    # [선택사항] 클러스터 성격에 따른 "제안" 세팅 (원하시면 주석 해제)
    # if target_cluster == 3: # 가족/인프라
    #     st.session_state['infra_slider'] = (5.0, 10.0) # 인프라 좋은 곳 위주
    #     st.session_state['diff_slider'] = ('입문', '중급') # 너무 어렵지 않게
    # elif target_cluster == 5: # 오지/숨은명소
    #     st.session_state['infra_slider'] = (0.0, 4.0) # 인프라 적은 곳

# -----------------------------------------------------------------------------
# 3. UI 구성
# -----------------------------------------------------------------------------
st.markdown("##### 선호하는 등산 테마를 선택해주세요")

st.pills(
    "등산 테마",
    options=cluster_options,
    selection_mode="single",
    key="type_selection",
    on_change=set_search_condition,
    default=None,
    help="사용자의 정성적 경험(리뷰 텍스트)과 정량적 환경 지표(관광 인프라, 주차장 거리)를 분석하여 도출한 5가지 테마입니다."
)

st.divider()

st.markdown("##### 세부 조건을 조절해보세요")

col1, space1, col2, space2, col3= st.columns([1, 0.2, 1, 0.2, 1])

with col1:
    diff_val = st.select_slider(
        "산행 난이도",
        options=difficulty_levels,
        value=st.session_state['diff_slider'],
        key="diff_slider" ,
        help="""거리와 누적 상승 고도를 기반으로 산출한 점수에 경사도 가중치를 적용했습니다.
        ※ 같은 등급 내에서는 숫자가 클수록 더 어렵습니다. (예: 초급1 < 초급3)

        [등급별 비율]
        • 입문 : 하위 5%
        • 초급 : 5 ~ 30% (25%)
        • 중급 : 30 ~ 65% (35%)
        • 상급 : 65 ~ 89% (24%)
        • 최상급 : 89 ~ 97%
        • 초인, 신 : 상위 3% 이내"""
    )

with col2:
    infra_val = st.slider(
        "관광 인프라 (점수)",
        min_value=0.0, max_value=10.0,
        value=st.session_state['infra_slider'],
        key="infra_slider",
        help="등산로 반경 5km 내의 식당, 카페, 숙소, 관광지 수를 집계한 점수입니다.\n\n거리가 가까울수록 높은 가중치(1km 이내: 1.0, 3km 이내: 0.8, 5km 이내: 0.5)를 부여하고, 로그(ln) 함수를 적용하여 0~10점 척도로 환산했습니다."
    )

with col3:
    park_dist_val = st.slider(
        "주차장 거리 (m 이내)",
        min_value=0, max_value=2000,
        step=100,
        value=st.session_state['park_dist_slider'],
        key="park_dist_slider",
        help="등산로 입구(들머리)에서 가장 가까운 공영/사설 주차장까지의 직선 거리입니다."
    )

# -----------------------------------------------------------------------------
# 4. 데이터 필터링 [핵심 변경 구간]
# -----------------------------------------------------------------------------
try:
    # 1) 공통 필터 조건
    start_idx = difficulty_levels.index(diff_val[0])
    end_idx = difficulty_levels.index(diff_val[1])
    selected_levels = difficulty_levels[start_idx : end_idx + 1]

    common_condition = (
        (df['난이도'].isin(selected_levels)) &
        (df['관광인프라점수'] >= infra_val[0]) & (df['관광인프라점수'] <= infra_val[1]) &
        (df['주차장거리_m'] != -1) &            # [변경] -1(데이터 없음)인 경우만 제외
        (df['주차장거리_m'] <= park_dist_val)   # 0m(바로 앞)인 경우는 여기에 포함되어 살아남음
    )

    # 2) 테마(Cluster) 필터링 로직
    current_selection = st.session_state.get('type_selection')
    
    if current_selection is None:
        filtered_df = df[common_condition]
    else:
        target_cluster_id = cluster_map.get(current_selection)
        filtered_df = df[
            (df['Cluster'] == target_cluster_id) & 
            common_condition
        ]
        
except Exception as e:
    st.error(f"필터링 오류 발생: {e}")
    filtered_df = pd.DataFrame()

# -----------------------------------------------------------------------------
# 5. 결과 출력
# -----------------------------------------------------------------------------
st.write(f"검색 결과: **{len(filtered_df)}**개의 코스를 찾았습니다.")

display_cols = ['코스명', '위치', '총거리_km', '최고고도_m', '세부난이도', '관광인프라점수', '매력종합점수', '주차장거리_m']

if not filtered_df.empty:
    sorted_df = filtered_df.sort_values('매력종합점수', ascending=False)
    
    event = st.dataframe(
        sorted_df[display_cols],
        hide_index=True,
        width='stretch',
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "관광인프라점수": st.column_config.ProgressColumn("인프라", format="%.1f", min_value=0, max_value=10),
            "매력종합점수": st.column_config.NumberColumn("매력도", format="⭐ %.1f"),
            "주차장거리_m": st.column_config.NumberColumn("주차장", format="%d m"),
            "총거리_km": st.column_config.NumberColumn("총 거리", format="%.1f km"),
            "최고고도_m": st.column_config.NumberColumn("고도", format="%d m")
        }
    )

    # -------------------------------------------------------------------------
    # 6. 선택된 코스 상세 정보 & 지도 & 인프라
    # -------------------------------------------------------------------------
    if len(event.selection.rows) > 0:
        st.divider()
        
        # 1) 선택된 등산로 데이터 가져오기
        selected_index = event.selection.rows[0]
        selected_row = sorted_df.iloc[selected_index]
        
        show_trail_detail(selected_row, df_infra)

    else:
        st.info("등산로를 선택하면 상세 정보가 표시됩니다.")
else:
    st.info("조건에 맞는 등산로가 없습니다. 다른 테마나 조건을 선택해보세요.")