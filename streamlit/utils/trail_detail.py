# utils/trail_detail.py (새 파일 생성)
import streamlit as st
import pandas as pd
import os
import gpxpy
import folium
import re 
from streamlit_folium import st_folium

def show_trail_detail(selected_row, df_infra):
    """
    등산로 상세 정보 + 지도 + 인프라 표시 함수
    
    Parameters:
    - selected_row: 선택된 등산로 데이터 (pandas Series)
    - df_infra: 관광 인프라 데이터프레임
    """
    
    mt_name = selected_row['산이름']
    course_name = selected_row['코스명']
    
    st.subheader(f"🥾 {course_name}")
    
    # 인프라 데이터 필터링
    pin_location = None
    pin_popup = None
    current_category = st.session_state.get('infra_category_radio', '음식점')
    infra_display = pd.DataFrame()
    
    if not df_infra.empty:
        if 'trail_code' in df_infra.columns:
            infra_filtered = df_infra[df_infra['trail_code'] == course_name]
        else:
            infra_filtered = df_infra[df_infra['mountain_name'] == mt_name]
        
        infra_display = infra_filtered[infra_filtered['category'] == current_category].reset_index(drop=True)
        
        if 'infra_list' in st.session_state and st.session_state.infra_list['selection']['rows']:
            sel_idx = st.session_state.infra_list['selection']['rows'][0]
            if sel_idx < len(infra_display):
                sel_infra_row = infra_display.iloc[sel_idx]
                pin_location = [sel_infra_row['lat'], sel_infra_row['lng']]
                pin_popup = sel_infra_row['place_name']
    
    # 지도 & 상세정보 레이아웃
    col_map, col_info = st.columns([1.2, 1])
    
    with col_map:
        _render_trail_map(mt_name, course_name, pin_location, pin_popup)
    
    with col_info:
        _render_trail_info(selected_row)
    
    # 관광 인프라 리스트
    if not infra_display.empty:
        _render_infra_list(infra_display, current_category, pin_popup)
    else:
        st.info(f"선택하신 '{course_name}' 주변에는 해당 카테고리의 시설 정보가 없습니다.")


def _render_trail_map(mt_name, course_name, pin_location=None, pin_popup=None):
    """GPX 경로 지도 렌더링"""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gpx_folder = os.path.join(base_path, 'data', '100대명산', mt_name)
    gpx_file_path = None
    
    if os.path.exists(gpx_folder):
        files = os.listdir(gpx_folder)
        gpx_files = [f for f in files if f.endswith('.gpx')]
        
        if gpx_files:
            # -----------------------------------------------------------
            # [변경 시작] 코스 번호와 일치하는 GPX 파일 찾기
            # -----------------------------------------------------------
            target_file = None
            try:
                # 1. 코스명에서 숫자 추출 (예: "가리산_02" -> 2)
                # 만약 숫자가 없으면 에러가 나서 except로 빠지고 첫번째 파일 사용
                c_nums = re.findall(r'\d+', course_name)
                if c_nums:
                    course_idx = int(c_nums[-1])  # 맨 뒤 숫자 사용

                    # 2. 파일 리스트 뒤지기
                    for f in gpx_files:
                        f_nums = re.findall(r'\d+', f)
                        if f_nums and int(f_nums[-1]) == course_idx:
                            target_file = f
                            break
            except Exception:
                pass

            # 찾는 파일이 있으면 그거 쓰고, 없으면 그냥 첫 번째 파일(fallback) 사용
            if target_file:
                gpx_file_path = os.path.join(gpx_folder, target_file)
            else:
                gpx_file_path = os.path.join(gpx_folder, gpx_files[0])
    
    if gpx_file_path and os.path.exists(gpx_file_path):
        try:
            with open(gpx_file_path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
            
            points = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        points.append([point.latitude, point.longitude])
            
            if points:
                start_pos = points[0]
                m = folium.Map(location=start_pos, zoom_start=13)
                folium.PolyLine(points, color="red", weight=5, opacity=0.8).add_to(m)
                folium.Marker(points[0], popup="출발", icon=folium.Icon(color='green', icon='play')).add_to(m)
                folium.Marker(points[-1], popup="도착", icon=folium.Icon(color='blue', icon='stop')).add_to(m)
                
                if pin_location:
                    folium.Marker(
                        pin_location,
                        popup=pin_popup,
                        icon=folium.Icon(color='orange', icon='star')
                    ).add_to(m)
                
                st_folium(m, width=700, height=400)
            else:
                st.warning("GPX 경로 없음")
        except Exception as e:
            st.error(f"오류: {e}")
    else:
        st.container(height=400, border=True).info("GPX 파일 없음")


def _render_trail_info(selected_row):
    """등산로 상세 정보 렌더링"""
    dist_str = f"{selected_row['총거리_km']} km"
    time_str = f"{selected_row['예상시간']}"
    alt_str = f"{int(selected_row['최고고도_m'])} m"
    diff_str = f"{selected_row['세부난이도']}"
    
    p_name = str(selected_row.get('주차장명', '-'))
    p_dist = selected_row.get('주차장거리_m', 0)
    b_name = str(selected_row.get('정류장명', '-'))
    b_dist = selected_row.get('정류장거리_m', 0)
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("⏱️ 소요 시간", help="거리와 고도차를 반영한 추정 시간입니다. (평지 1km당 15분 + 상승 100m당 10분 + 하강 100m당 5분)")
            st.markdown(f":orange[**{time_str}**]")
            st.caption("📏 총 거리", help="등산로 입구(들머리)에서 정상 또는 반환점까지 이동한 후 다시 돌아오는 총 산행 거리입니다.")
            st.markdown(f"**{dist_str}**")
        with c2:
            st.caption("⛰️ 최고 고도", help="등산로에서 가장 높은 지점의 해발 고도입니다.")
            st.markdown(f"**{alt_str}**")
            st.caption("💪 난이도", help="거리·고도·경사도를 반영한 난이도입니다. (입문 < 초급 < 중급 < 상급 < 최상급 < 초인 < 신, 숫자가 클수록 어려움)")
            st.markdown(f":green[**{diff_str}**]")
        
        st.divider()
        
        st.caption("🅿️ 주차장", help="등산로 입구(들머리)에서 가장 가까운 공영/사설 주차장까지의 직선 거리입니다.")
        if p_name in ['-', 'nan', 'None'] or p_dist == 0:
            st.markdown("-")
        else:
            st.markdown(f"**{p_name}** <span style='color:grey; font-size:0.8em'>({int(p_dist)}m)</span>", unsafe_allow_html=True)
        
        st.caption("🚏 버스 정류장", help="등산로 입구(들머리)에서 가장 가까운 버스 정류장까지의 직선 거리입니다.")
        if b_name in ['-', 'nan', 'None'] or b_dist == 0:
            st.markdown("-")
        else:
            st.markdown(f"**{b_name}** <span style='color:grey; font-size:0.8em'>({int(b_dist)}m)</span>", unsafe_allow_html=True)


def _render_infra_list(infra_display, current_category, pin_popup):
    """관광 인프라 리스트 렌더링"""
    categories = ["음식점", "카페", "숙박", "관광명소"]
    
    def reset_infra_selection():
        if 'infra_list' in st.session_state:
            del st.session_state['infra_list']
    
    st.radio(
        "카테고리 선택",
        categories,
        index=categories.index(current_category) if current_category in categories else 0,
        key="infra_category_radio",
        horizontal=True,
        on_change=reset_infra_selection,
        label_visibility="collapsed"
    )
    
    st.write("")
    
    infra_display['location_type'] = infra_display['base_type'].apply(
        lambda x: '출발지' if x == 'start' else '도착지'
    )
    
    cols_to_show = ['place_name', 'location_type', 'distance_m', 'address']
    col_config = {
        "place_name": st.column_config.TextColumn("장소명"),
        "location_type": st.column_config.TextColumn("기준 위치"),
        "distance_m": st.column_config.NumberColumn("거리", format="%d m"),
        "address": st.column_config.TextColumn("주소")
    }
    
    if current_category == '관광명소':
        cols_to_show.insert(1, 'tour_spot_type')
        col_config["tour_spot_type"] = st.column_config.TextColumn("구분")
    
    st.dataframe(
        infra_display[cols_to_show],
        key="infra_list",
        on_select="rerun",
        selection_mode="single-row",
        width='stretch',
        hide_index=True,
        column_config=col_config
    )
    
    if pin_popup:
        st.info(f"📍 지도에 '{pin_popup}' 위치가 표시되었습니다. (주황색 별)")