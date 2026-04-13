import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import platform
import os

st.header("🥾 분석 페이지")
st.write("")
# =============================================================================
# 운영체제별 한글 폰트 설정
# =============================================================================
def set_korean_font():
    """운영체제에 따라 적절한 한글 폰트 설정"""
    system = platform.system()
    if system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = 'AppleGothic'
    elif system == 'Windows':  # Windows
        plt.rcParams['font.family'] = 'Malgun Gothic'
    else:  # Linux
        plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.family'] = 'Malgun Gothic' # Windows: Malgun Gothic, Mac: AppleGothic

set_korean_font()
# =============================================================================
# 데이터 로드
# =============================================================================

# @st.cache_data: 데이터 캐싱 데코레이터
# 주요 특징:
# - 동일한 입력에 대해 결과를 메모리에 저장하여 재사용
# - 앱 재실행 시에도 캐시된 데이터 유지 (성능 향상)
@st.cache_data
def load_mountain_path():
    """100대명산 데이터셋 로드"""
    try:
        # 1. 현재 파일(pages/app.py)의 폴더 경로를 구함 -> .../프로젝트/pages
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. 상위 폴더(프로젝트 루트) 경로를 구함 -> .../프로젝트
        # (pages 폴더의 부모 폴더로 이동)
        root_dir = os.path.dirname(current_dir)
        
        # 3. 상위 폴더 기준에서 data 폴더 안의 파일 경로 생성
        file_path = os.path.join(root_dir, 'data', '100mountains_dashboard.csv')
        
        # 4. 파일 읽기
        df = pd.read_csv(file_path)
        
        df.columns = ['코스명', '산이름', '유형설명', '최고고도_m', '누적상승_m', '편도거리_km', '총거리_km', '예상시간_분', '예상시간', 
            '출발_lat', '출발_lon', '도착_lat', '도착_lon', '난이도', '세부난이도', '난이도점수',
            '관광인프라점수','주차장_접근성점수','정류장_접근성점수','코스수','가중치','매력종합점수',
            '전망','힐링','사진','등산로','성취감','계절매력','특출매력','특출점수',
            '주차장거리_m','정류장거리_m','위치', '주차장명', '정류장명', 'Cluster']
        return df
        
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다.\n시도한 경로: {file_path}")
        return pd.DataFrame()

df = load_mountain_path()
if df.empty:
    st.stop()

# =============================================================================
# 데이터 개요
st.subheader("📋 데이터 개요")

# 데이터 주요 메트릭 표시
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("산림청 선정 100대 명산", "100개")
with col2:
    st.metric("분석에 활용한 등산로 코스", f"{df['코스명'].nunique():,}개")
with col3:
    st.metric("수집한 리뷰 분석", "33,700+")
with col4:
    st.metric("수집한 관광 POI 데이터", "415,300+")

# =============================================================================
# 등산로 분석
st.divider()
st.subheader("📊 등산로 분석")
# 탭 3개 생성 (이모지로 시각적 구분)
tab1, tab2, tab3 = st.tabs(["💪난이도", "🏔️등산로 거리/고도", "🛵접근성"])
with tab1:
    st.subheader("💪난이도 분포")
    st.caption("걱정 마세요, 내 실력에 딱 맞는 코스는 반드시 있습니다.")

    # 데이터 집계
    count_df = df['난이도'].value_counts().reindex(['입문', '초급', '중급', '상급', '최상급', '초인', '신']).reset_index()
    count_df.columns = ['난이도', '개수']

    # Plotly 그래프 생성
    fig = px.bar(count_df, x='난이도', y='개수', 
                 text='개수',  # 막대 위에 숫자 표시
                 color='난이도', # 난이도별 색상 다르게
                 color_discrete_sequence=px.colors.qualitative.Pastel # 파스텔 톤 색상
                )
    
    # 디자인 다듬기
    fig.update_layout(showlegend=False) # 범례 숨김 (x축에 있으므로)
    
    st.plotly_chart(fig, width='stretch')
    # 데이터 정렬 (난이도 점수가 있다고 가정)
    # 만약 '난이도점수' 컬럼이 문자열이라면 숫자로 변환 필요: df['난이도점수'] = pd.to_numeric(df['난이도점수'])
    
    # TOP 5
    st.subheader("💧🔥난이도 쉬움 vs 어려움")
    st.caption("입문에서 시작해서 신의 경지까지")
    # 가장 어려운 TOP 5 (점수 내림차순)
    top_hard = df.sort_values(by='난이도점수', ascending=False).head(5)
    
    # 가장 쉬운 TOP 5 (점수 오름차순)
    top_easy = df.sort_values(by='난이도점수', ascending=True).head(5)

    # 화면 분할 (1:1 비율)
    col1, col2 = st.columns(2)

    # 함수: 리스트를 예쁘게 출력해주는 헬퍼 함수
    def show_top5_list(container, title, icon, data, color_theme):
        with container:
            # 컨테이너박스로 감싸서 카드처럼 보이게 만듦
            with st.container(border=True):
                st.markdown(f"#### {icon} {title}")
                
                for idx, (i, row) in enumerate(data.iterrows()):
                    rank = idx + 1
                    # 1,2,3등은 메달 이모지, 나머지는 숫자
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                    
                    # 텍스트 출력 (산이름 - 코스명)
                    st.markdown(
                        f"""
                        <div style='padding: 5px; border-radius: 5px; margin-bottom: 5px; background-color: rgba(255,255,255,0.05);'>
                            <span style='font-size: 1.1em;'>{medal} <b>{row['산이름']}</b></span>
                            <br>
                            <span style='color: gray; font-size: 0.9em;'>&nbsp;&nbsp;&nbsp;&nbsp;└ {row['코스명']} ({row['난이도']})</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

    # 오른쪽 컬럼: 쉬운 코스
    show_top5_list(col1, "가장 쉬운 코스 TOP 5", "💧", top_easy, "blue")

    # 왼쪽 컬럼: 어려운 코스
    show_top5_list(col2, "가장 어려운 코스 TOP 5", "🔥", top_hard, "red")

with tab2:
    st.subheader("📏등산로 거리 분포")
    st.caption('대부분의 코스는 5~15km 사이')
    fig = px.histogram(df, x='총거리_km', nbins=20,
                       labels={'총거리_km': '총거리 (km)', 'count': '코스 개수'},
                       color_discrete_sequence=['teal'])
    
    st.plotly_chart(fig, width='stretch')

    st.subheader("🏔️등산로 고도 분포")
    st.caption('동네 뒷산 높이부터 2,000m급 고산까지')
    fig = px.histogram(df, x='최고고도_m', nbins=20,
                       labels={'최고고도_m': '최고고도 (m)', 'count': '코스 개수'},
                       color_discrete_sequence=['orange'])
    
    st.plotly_chart(fig, width='stretch')

    st.subheader("📈거리 vs 고도 관계 (산점도)")
    st.caption('왼쪽 아래에서 오른쪽 위로 이어지는 난이도 스펙트럼')
    # 산점도 생성 (X: 거리, Y: 고도, 색상: 난이도)
    fig_scatter = px.scatter(
        df, 
        x='총거리_km', 
        y='최고고도_m', 
        color='난이도',                 # 난이도별로 색상 구분 (분석에 매우 유용)
        hover_data=['산이름', '코스명', '예상시간'],  # 마우스 올렸을 때 뜨는 정보
        labels={
            '총거리_km': '총거리 (km)', 
            '최고고도_m': '최고고도 (m)',
            '난이도': '코스 난이도'
        },
        category_orders={"난이도": ['입문', '초급', '중급', '상급', '최상급', '초인', '신']} # 범례 순서 정렬 (데이터에 맞게 조정 가능)
    )
    
    # 점 크기 및 투명도 조절 (겹친 점 보기 편하게)
    fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))
    
    st.plotly_chart(fig_scatter, width='stretch')

with tab3:
    st.subheader("🚗 자차 vs 🚌 버스 접근성 비교")
    st.caption("뚜벅이 등산러의 비애... 대중교통 이용 시 도보 이동 거리를 확인하세요.")

    # 1. 데이터 전처리 (Wide -> Long 변환 및 단위 변경)
    access_df = df.melt(value_vars=['주차장거리_m', '정류장거리_m'], 
                        var_name='접근수단', 
                        value_name='거리_m')
    
    # 거리 단위를 m -> km로 변환 (가독성 향상)
    access_df['거리_km'] = access_df['거리_m'] / 1000
    
    # 이름 예쁘게 변경
    access_df['접근수단'] = access_df['접근수단'].map({
        '주차장거리_m': '주차장', 
        '정류장거리_m': '버스정류장'
    })

    # 2. 바이올린 플롯 생성 (스타일 개선)
    fig_violin = px.violin(access_df, 
                           x='접근수단', 
                           y='거리_km', 
                           color='접근수단',
                           box=True,           # 박스플롯 표시 (중앙값, 분위수)
                           points=False,       # 지저분한 개별 점들은 제거 (깔끔하게!)
                           hover_data=access_df.columns,
                           color_discrete_map={'주차장': '#1f77b4', '버스정류장': '#ff7f0e'}, # 색상 지정
                           title="등산로 입구까지의 거리 분포 (최대 10km 이내)")

    # 3. 핵심: Y축 범위를 제한해서 '눌린' 그래프 펴주기
    fig_violin.update_yaxes(range=[0, 2.5], title_text="거리 (km)") 
    
    st.plotly_chart(fig_violin, width='stretch')

    st.subheader("🏃‍♂️ 접근성과 난이도의 상관관계")
    st.caption("도심(주차장)에서 멀어질수록 산이 험해질까요?")

    fig_access_diff = px.scatter(df, 
                                 x='주차장거리_m', 
                                 y='난이도점수',
                                 color='난이도',
                                 size='총거리_km',
                                 hover_data=['산이름', '코스명', '주차장명'],
                                 labels={'주차장거리_m': '주차장 거리 (m)', '난이도점수': '난이도 점수'},
                                 title="주차장 거리 vs 난이도 점수")
    
    st.plotly_chart(fig_access_diff, width='stretch')
