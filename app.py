import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import random
import time

st.set_page_config(page_title="실제 지도 전술 시뮬레이터", layout="wide")

st.title("🗺️ 란체스터 실제 지도 전술 시뮬레이터")
st.write("실제 대한민국 전장 지형 좌표를 기반으로 부대 기호 마커가 전진 및 교전하는 모습을 관측하는 작전술 시뮬레이터입니다.")

# 1. 실제 가상 전장 위치 정의 (위도, 경도, 지형적 특성)
BATTLEGROUNDS = {
    "철원 DMZ 인근 (야지/계곡 중심)": {
        "center": [38.2500, 127.2000],
        "blue_start": [38.2100, 127.1600],
        "red_start": [38.2900, 127.2400],
        "terrain": "야지",
        "desc": "산악과 계곡이 깊어 기갑 장비 기동에 페널티가 부여됩니다."
    },
    "인천-부평 지구 (시가지/평지 중심)": {
        "center": [37.4900, 126.7200],
        "blue_start": [37.4500, 126.6800],
        "red_start": [37.5300, 126.7600],
        "terrain": "시가지",
        "desc": "건물 엄폐가 우수하여 보병 및 게릴라 화력이 급증합니다."
    }
}

# 제대 규모 및 전투력 지수 (이전과 동일)
UNIT_SCALES = {"소대 (30명)": 30, "중대 (120명)": 120, "대대 (500명)": 500, "여단 (3,500명)": 3500}
BRANCH_POWER = {"보병": 1.0, "기갑": 25.0, "포병": 60.0}

st.markdown("---")

# [상단 설정]
selected_bg = st.selectbox("📍 전장 지역 선택 (실제 지리 정보 반영)", list(BATTLEGROUNDS.keys()))
bg_data = BATTLEGROUNDS[selected_bg]
st.info(f"ℹ️ **지형 분석:** {bg_data['desc']}")

col1, col2 = st.columns(2)
with col1:
    st.subheader("🔵 자유진영 편성")
    blue_scale = st.selectbox("자유군 제대 규모", list(UNIT_SCALES.keys()), key="bs")
    blue_inf = st.number_input("자유 보병 수", min_value=1, value=10)
    blue_tk = st.number_input("자유 기갑 수", min_value=0, value=2)

with col2:
    st.subheader("🔴 공산진영 편성")
    red_scale = st.selectbox("공산군 제대 규모", list(UNIT_SCALES.keys()), key="rs")
    red_inf = st.number_input("공산 보병 수", min_value=1, value=10)
    red_tk = st.number_input("공산 기갑 수", min_value=0, value=2)

st.markdown("---")

# [시뮬레이션 구동]
if st.button("⚔️ 실제 지도상에서 작전 개시", type="primary", use_container_width=True):
    
    # 기초 능력치 계산
    b_scale_w = UNIT_SCALES[blue_scale]
    r_scale_w = UNIT_SCALES[red_scale]
    
    blue_start_HP = (blue_inf + blue_tk) * b_scale_w
    red_start_HP = (red_inf + red_tk) * r_scale_w
    
    # 지형 보너스 
    b_tk_pow, r_tk_pow = 25.0, 25.0
    b_inf_pow, r_inf_pow = 1.0, 1.0
    if bg_data["terrain"] == "야지":
        b_tk_pow *= 0.7; r_tk_pow *= 0.7
    elif bg_data["terrain"] == "시가지":
        b_tk_pow *= 0.5; r_tk_pow *= 0.5
        b_inf_pow *= 1.3; r_inf_pow *= 1.3
        
    blue_base_dmg = (blue_inf * b_inf_pow + blue_tk * b_tk_pow)
    red_base_dmg = (red_inf * r_inf_pow + red_tk * r_tk_pow)
    
    B_HP, R_HP = float(blue_start_HP), float(red_start_HP)
    
    # 좌표 변수 (턴이 지날수록 두 시작점의 중간 지점으로 이동)
    b_curr_lat, b_curr_lon = bg_data["blue_start"]
    r_curr_lat, r_curr_lon = bg_data["red_start"]
    
    # 두 진영의 정중앙 격돌 지점 좌표 계산
    mid_lat = (b_curr_lat + r_curr_lat) / 2
    mid_lon = (b_curr_lon + r_curr_lon) / 2

    # UI 레이아웃 준비
    st.subheader("📡 위성 실시간 전술 지도 지휘소")
    map_placeholder = st.empty()
    log_placeholder = st.empty()
    
    # 간단한 4턴 고속 시뮬레이션 애니메이션 효과
    for turn in range(1, 5):
        # 1. 턴별 부대 이동 좌표 동적 계산
        weight = turn / 4.0  # 4턴째에 정확히 중앙에서 충돌
        
        b_lat = bg_data["blue_start"][0] + (mid_lat - bg_data["blue_start"][0]) * weight
        b_lon = bg_data["blue_start"][1] + (mid_lon - bg_data["blue_start"][1]) * weight
        
        r_lat = bg_data["red_start"][0] + (mid_lat - bg_data["red_start"][0]) * weight
        r_lon = bg_data["red_start"][1] + (mid_lon - bg_data["red_start"][1]) * weight
        
        # 2. 전투력 소모 연산 (충돌하는 4턴째에 큰 피해 발생)
        if turn == 4:
            b_dmg = blue_base_dmg * random.uniform(0.7, 1.2)
            r_dmg = red_base_dmg * random.uniform(0.7, 1.2)
            B_HP = max(0, B_HP - r_dmg)
            R_HP = max(0, R_HP - b_dmg)
        
        # 3. Folium 지도 객체 생성 및 실제 지도 타일 로드
        m = folium.Map(location=bg_data["center"], zoom_start=12, tiles="OpenStreetMap")
        
        # 자유군 제대 심볼 마커 (🔵 표시 및 툴팁 제공)
        if B_HP > 0:
            folium.Marker(
                location=[b_lat, b_lon],
                popup=f"자유군 {blue_scale}",
                tooltip=f"🔵 자유군 잔존 병력: {int(B_HP)}명",
                icon=folium.DivIcon(html=f"<div style='font-size: 24px;'>🔵</div>")
            ).add_to(m)
            
        # 공산군 제대 심볼 마커 (🔴 표시 및 툴팁 제공)
        if R_HP > 0:
            folium.Marker(
                location=[r_lat, r_lon],
                popup=f"공산군 {red_scale}",
                tooltip=f"🔴 공산군 잔존 병력: {int(R_HP)}명",
                icon=folium.DivIcon(html=f"<div style='font-size: 24px;'>🔴</div>")
            ).add_to(m)
            
        # 4턴째 격돌 연출 (💥 교전 심볼 추가)
        if turn == 4 and B_HP > 0 and R_HP > 0:
            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.DivIcon(html=f"<div style='font-size: 30px;'>💥</div>")
            ).add_to(m)

        # 지도 컴포넌트를 화면에 렌더링
        with map_placeholder.container():
            st_folium(m, width=900, height=450, key=f"map_turn_{turn}")
            
        # 하단 로그 출력
        with log_placeholder.container():
            st.markdown(f"### 🎯 제 {turn} 턴 기동 상황 보고")
            if turn < 4:
                st.write("✈️ 양측 부대가 작전 지역 중앙 전선으로 기동 및 전진 중입니다.")
            else:
                st.markdown(f"💥 **중앙 전선 접적완료! 격렬한 교전이 발생했습니다.**")
                st.write(f"- 자유군 잔존군세: {int(B_HP)} / {int(blue_start_HP)}")
                st.write(f"- 공산군 잔존군세: {int(R_HP)} / {int(red_start_HP)}")
                
        time.sleep(1.5)  # 지도가 리로드되며 기동하는 연출을 체감하기 위한 딜레이

    # 최종 브리핑
    st.success("🏁 작전 종료: 부대 기동 및 접적 시뮬레이션이 성공적으로 완료되었습니다.")
