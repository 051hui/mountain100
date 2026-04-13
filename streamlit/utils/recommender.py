# recommender.py
from typing import Dict, Any
import pandas as pd


# 클러스터 매핑
CLUSTER_MAP = {
    "seasonal": 0,  # 계절매력
    "view": 2,      # 전망/사진
    "family": 3,    # 가족/인프라
    "healing": 4,   # 힐링
    "hidden": 5,    # 오지/숨은명소
    "any": None
}

# 난이도 매핑
DIFFICULTY_MAP = {
    1: ["입문"],
    2: ["초급", "초급1", "초급2", "초급3"],
    3: ["중급", "중급1", "중급2", "중급3"],
    4: ["상급", "상급1", "상급2", "상급3"],
    5: ["최상급", "최상급1", "최상급2", "최상급3"],
    6: ["초인", "초인1", "초인2", "초인3"],
    7: ["신", "신1", "신2", "신3"]
}


def get_difficulty_levels(min_level: int = None, max_level: int = None) -> list:
    """난이도 범위를 실제 난이도 레이블 리스트로 변환"""
    if min_level is None:
        min_level = 1
    if max_level is None:
        max_level = 7
    
    levels = []
    for level in range(min_level, max_level + 1):
        levels.extend(DIFFICULTY_MAP.get(level, []))
    
    return levels


def run_recommender(
    trails_df: pd.DataFrame, 
    plan: Dict[str, Any], 
    top_k: int = 5
) -> pd.DataFrame:
    """
    기존 추천 엔진 실행
    
    Args:
        trails_df: 등산로 데이터프레임
        plan: LLM translation 결과
        top_k: 반환할 추천 개수
        
    Returns:
        추천된 등산로 데이터프레임 (score 컬럼 포함)
    """
    df = trails_df.copy()
    
    # 1) 클러스터 필터링
    cluster_pref = plan.get("cluster_preference", "any")
    cluster_id = CLUSTER_MAP.get(cluster_pref)
    
    if cluster_id is not None:
        df = df[df["Cluster"] == cluster_id]
    
    # 2) 제약조건 적용
    constraints = plan.get("constraints", {})
    
    # 난이도 필터링
    diff_min = constraints.get("difficulty_min")
    diff_max = constraints.get("difficulty_max")
    if diff_min is not None or diff_max is not None:
        allowed_levels = get_difficulty_levels(diff_min, diff_max)
        df = df[df["난이도"].isin(allowed_levels)]
    
    # 인프라 점수 필터링
    infra_min = constraints.get("infra_min")
    infra_max = constraints.get("infra_max")
    if infra_min is not None:
        df = df[df["관광인프라점수"] >= infra_min]
    if infra_max is not None:
        df = df[df["관광인프라점수"] <= infra_max]
    
    # 주차장 거리 필터링
    park_dist_max = constraints.get("park_dist_max")
    if park_dist_max is not None:
        df = df[
            (df["주차장거리_m"] != -1) &  # 데이터 있는 것만
            (df["주차장거리_m"] <= park_dist_max)
        ]
    
    # 총 거리 필터링
    distance_max = constraints.get("distance_max_km")
    if distance_max is not None:
        df = df[df["총거리_km"] <= distance_max]
    
    # 고도 필터링
    altitude_min = constraints.get("altitude_min_m")
    altitude_max = constraints.get("altitude_max_m")
    if altitude_min is not None:
        df = df[df["최고고도_m"] >= altitude_min]
    if altitude_max is not None:
        df = df[df["최고고도_m"] <= altitude_max]
    
    # 3) 제외 조건 적용
    exclude = plan.get("exclude", {})
    if exclude.get("mountains"):
        df = df[~df["산이름"].isin(exclude["mountains"])]
    if exclude.get("trails"):
        df = df[~df["코스명"].isin(exclude["trails"])]
    
    # 4) 매력종합점수 기준으로 정렬
    if not df.empty:
        df = df.sort_values("매력종합점수", ascending=False)
        df = df.head(top_k)
        
        # score 컬럼 추가 (매력종합점수를 그대로 사용)
        df["score"] = df["매력종합점수"]
    
    # 메타 정보 저장
    df.attrs["cluster"] = cluster_pref
    df.attrs["constraints"] = constraints
    
    return df
