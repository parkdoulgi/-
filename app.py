import streamlit as st
import math
import random
import time

# 페이지 레이아웃 설정
st.set_page_config(page_title="란체스터 턴제 작전 시뮬레이터", layout="wide")

st.title("🎮 란체스터 턴제 작전 시뮬레이터 (+가상 전술 지도)")
st.write("작전 개시 버튼을 누르면, 하단에 가상의 10x10 작전 지도가 생성되며 부대 이동과 지형별 교전 상황이 실시간 격자로 시각화됩니다.")

# 1. 부대 규모(제대) 정의
UNIT_SCALES = {
    "팀 (Team - 약 3~5명)": 1,
    "반 (Section - 약 10명 내외)": 2,
    "분대 (Squad - 약 10명)": 10,
    "소대 (Platoon - 약 30명)": 30,
    "중대 (Company - 약 120명)": 120,
    "대대 (Battalion - 약 500명)": 500,
    "연대 (Regiment - 약 1,500명)": 1500,
    "여단 (Brigade - 약 3,500명)": 3500,
    "사단 (Division - 약 12,000명)": 12000,
    "군단 (Corps - 약 50,000명)": 50000,
}

# 2. 핵심 군사 전술 정의
TACTICAL_OPTIONS = {
    "정면 공격 (Frontal Assault)": {"atk_mod": 1.0, "def_mod": 1.0, "law": "제곱", "desc": "정직한 정면 승부."},
    "포위 / 이중 포위 (Encirclement)": {"atk_mod": 1.4, "def_mod": 1.0, "law": "제곱", "desc": "적의 측후방 차단, 화력 +40%"},
    "전격전 / 기갑 돌격 (Blitzkrieg)": {"atk_mod": 1.3, "def_mod": 0.8, "law": "제곱", "desc": "기갑/항공 중심 종심 타격"},
    "종심 방어 (Defense in Depth)": {"atk_mod": 0.8, "def_mod": 1.5, "law": "선형", "desc": "방어선 중첩, 선형 법칙 강제 적용"},
    "소모전 / 파상공세 (Attrition Warfare)": {"atk_mod": 1.2, "def_mod": 0.9, "law": "선형", "desc": "참호전 유도, 일대일 갉아먹기"}
}

# 3. 정규병과 및 기본 전투력 지수
BRANCH_POWER = {
    "보병 (정규 보병)": 1.0,
    "기갑 (전차/장갑차)": 25.0,
    "포병 (자주포/다연장)": 60.0,
    "정보/드론 (UAV)": 15.0,
    "항공 (공격헬기)": 120.0
}

# 매 턴 터질 수 있는 전장의 안개 돌발 이벤트
RANDOM_EVENTS = [
    {"title": "정상 교전", "blue": 1.0, "red": 1.0, "desc": "특이사항 없음."},
    {"title": "지휘관 저격당함!", "blue": 0.7, "red": 1.0, "desc": "자유진영 지휘 마비 (화력 -30%)"},
    {"title": "적 탄약고 대폭발!", "blue": 1.0, "red": 0.65, "desc": "공산진영 군수 마비 (화력 -35%)"},
    {"title": "악천후 대공습", "blue": 0.8, "red": 0.8, "desc": "양측 기동 및 시야 제한 (화력 -20%)"},
    {"title": "야간 기습 감행", "blue": 1.3, "red": 0.9, "desc": "야간 장비가 우수한 자유진영의 야습 (+30%)"},
    {"title": "공산군 결사 항전", "blue": 0.9, "red": 1.3, "desc": "배수의 진을 친 공산군의 반격 (+30%)"}
]

st.markdown("---")

# [상단 종합 전장 환경 설정]
st.subheader("🌐 글로벌 전장 인프라 설정")
c_env1, c_env2, c_env3 = st.columns(3)

with c_env1:
    selected_scale = st.selectbox("📏 작전 부대 체급 (제대 규모)", options=list(UNIT_SCALES.keys()), index=4)
    scale_weight = UNIT_SCALES[selected_scale]
with c_env2:
    terrain_type = st.selectbox("⛰️ 대표 전장 환경", ["평지 중심 전장", "야지(산악) 중심 전장", "시가지 중심 전장"])
with c_env3:
    tactics_relation = st.selectbox("⚔️ 초기 배치 상태", ["공평한 조우전", "자유진영 진지방어", "공산진영 진지방어"])

st.markdown("---")

# [진영별 입력 영역]
col1, col2 = st.columns(2)

with col1:
    st.header("🔵 자유진영 (Free World)")
    blue_tactics = st.selectbox("자유진영 작전 교리", list(TACTICAL_OPTIONS.keys()), key="b_tac")
    blue_unit_count = st.number_input("참전 제대 개수 (부대 수)", min_value=1, value=1, key="b_uc")
    
    st.write("**[제대 1개당 평균 편제]**")
    blue_regular = {}
    for branch in BRANCH_POWER.keys():
        blue_regular[branch] = st.number_input(f"자유 {branch} 수량", min_value=0, value=10 if "보병" in branch else 0, key=f"b_{branch}")
    blue_guerrilla = st.number_input("자유 민병대/게릴라 (명)", min_value=0, value=0, key="b_g")
    blue_morale = st.slider("지휘관 역량 및 사기", 0.5, 2.0, 1.0, 0.1, key="b_m")

with col2:
    st.header("🔴 공산진영 (Communist Bloc)")
    red_tactics = st.selectbox("공산진영 작전 교리", list(TACTICAL_OPTIONS.keys()), key="r_tac")
    red_unit_count = st.number_input("참전 제대 개수 (부대 수)", min_value=1, value=1, key="r_uc")
    
    st.write("**[제대 1개당 평균 편제]**")
    red_regular = {}
    for branch in BRANCH_POWER.keys():
        red_regular[branch] = st.number_input(f"공산 {branch} 수량", min_value=0, value=10 if "보병" in branch else 0, key=f"r_{branch}")
    red_guerrilla = st.number_input("공산 파르티잔/반군 (명)", min_value=0, value=0, key="r_g")
    red_morale = st.slider("지휘관 역량 및 사기", 0.5, 2.0, 1.0, 0.1, key="r_m")

st.markdown("---")

# [턴제 시뮬레이션 및 지도 렌더링]
if st.button("⚔️ 턴제 작전 시뮬레이션 개시 (지도 전개)", type="primary", use_container_width=True):
    
    # 가상의 8x8 고정 작전 지도 베이스라인 생성
    # ⬜ 평지, ⛰️ 산악/야지, 🏢 시가지
    base_map = []
    terrain_elements = ["⬜", "⬜", "⬜", "⛰️", "⛰️", "🏢"] if "평지" in terrain_type else (
                       ["⛰️", "⛰️", "⛰️", "⬜", "⬜", "🏢"] if "야지" in terrain_type else 
                       ["🏢", "🏢", "🏢", "⬜", "⛰️", "⬜"])
    
    for r in range(8):
        row = [random.choice(terrain_elements) for _ in range(8)]
        base_map.append(row)
        
    # 초기 진영 마커 위치 설정 (자유군은 왼쪽 상단, 공산군은 오른쪽 하단에서 시작하여 전진)
    b_x, b_y = 0, 0
    r_x, r_y = 7, 7

    # 초기 HP 연산
    blue_single_total = sum(blue_regular.values())
    red_single_total = sum(red_regular.values())
    blue_start_HP = (blue_single_total * blue_unit_count * scale_weight) + blue_guerrilla
    red_start_HP = (red_single_total * red_unit_count * scale_weight) + red_guerrilla

    B_HP, R_HP = float(blue_start_HP), float(red_start_HP)
    b_tac, r_tac = TACTICAL_OPTIONS[blue_tactics], TACTICAL_OPTIONS[red_tactics]
    is_linear = (b_tac["law"] == "선형" or r_tac["law"] == "선형")
    
    blue_def_mod = 2.0 if "자유진영 진지방어" in tactics_relation else 1.0
    red_def_mod = 2.0 if "공산진영 진지방어" in tactics_relation else 1.0

    st.subheader("🛰️ 참모본부 위성 실시간 전술 지도 및 작전 로그")
    
    # 맵 전용 화면 플레이스홀더와 로그 플레이스홀더를 분리하여 깔끔하게 배치
    map_placeholder = st.empty()
    log_placeholder = st.empty()
    
    turn = 1
    max_turns = 12
    
    while B_HP > 0 and R_HP > 0 and turn <= max_turns:
        # 1. 부대 이동 애니메이션 시뮬레이션 (턴이 지날수록 중앙 전선으로 전진)
        if turn == 2: b_x, b_y = 1, 2; r_x, r_y = 6, 5
        elif turn == 3: b_x, b_y = 2, 3; r_x, r_y = 5, 4
        elif turn >= 4: b_x, b_y = 3, 4; r_x, r_y = 4, 4  # 4턴부터는 정면 충돌 교전 지역 고정
        
        # 현재 부대가 위치한 타일의 지형 파악
        current_tile = base_map[b_y][b_x] if turn < 4 else base_map[3][4]
        
        # 지형별 실시간 화력 가중치 연산
        blue_power_map = BRANCH_POWER.copy()
        red_power_map = BRANCH_POWER.copy()
        b_g_pow, r_g_pow = 0.5, 0.5
        
        if current_tile == "⛰️":
            blue_power_map["기갑 (전차/장갑차)"] *= 0.7; red_power_map["기갑 (전차/장갑차)"] *= 0.7
            b_g_pow, r_g_pow = 0.8, 0.8
        elif current_tile == "🏢":
            blue_power_map["기갑 (전차/장갑차)"] *= 0.5; red_power_map["기갑 (전차/장갑차)"] *= 0.5
            blue_power_map["보병 (정규 보병)"] *= 1.3; red_power_map["보병 (정규 보병)"] *= 1.3
            b_g_pow, r_g_pow = 1.5, 1.5

        blue_base_dmg = sum(blue_regular[br] * blue_unit_count * blue_power_map[br] for br in BRANCH_POWER.keys()) + (blue_guerrilla * b_g_pow)
        red_base_dmg = sum(red_regular[br] * red_unit_count * red_power_map[br] for br in BRANCH_POWER.keys()) + (red_guerrilla * r_g_pow)

        # 🎲 랜덤 이벤트
        evt = random.choice(RANDOM_EVENTS)
        
        # 란체스터 화력 연산
        if not is_linear:
            b_current_dmg = blue_base_dmg * (B_HP / blue_start_HP) * b_tac["atk_mod"] * blue_morale * evt["blue"]
            r_current_dmg = red_base_dmg * (R_HP / red_start_HP) * r_tac["atk_mod"] * red_morale * evt["red"]
        else:
            b_current_dmg = blue_base_dmg * b_tac["atk_mod"] * blue_morale * evt["blue"] * 0.4
            r_current_dmg = red_base_dmg * r_tac["atk_mod"] * red_morale * evt["red"] * 0.4
            
        b_inflict = max(1.0, b_current_dmg / red_def_mod)
        r_inflict = max(1.0, r_current_dmg / blue_def_mod)
        
        B_HP = max(0, B_HP - r_inflict)
        R_HP = max(0, R_HP - b_inflict)
        
        # 🗺️ 2. 지도 실시간 그래픽 업데이트 (문자열 조합)
        map_html = "<div style='font-family: monospace; line-height: 1.5; letter-spacing: 5px; font-size: 24px; background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 2px solid #444; width: fit-content; margin: auto;'>"
        for y in range(8):
            row_str = ""
            for x in range(8):
                if x == b_x and y == b_y and B_HP > 0:
                    row_str += "🔵" # 자유군 부대 마커
                elif x == r_x and y == r_y and R_HP > 0:
                    row_str += "🔴" # 공산군 부대 마커
                elif turn >= 4 and x == 4 and y == 4 and B_HP > 0 and R_HP > 0:
                    row_str += "💥" # 정면 격돌 전선 마커
                else:
                    row_str += base_map[y][x]
            map_html += row_str + "<br>"
        map_html += "</div>"
        
        # 지도 화면 인쇄
        with map_placeholder.container():
            st.markdown("<p style='text-align: center; color: #aaa; font-weight: bold;'>[ 위성 관측 실시간 전장 작전 지도 ]</p>", unsafe_allow_html=True)
            st.markdown(map_html, unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 14px; color: #888;'>범례: ⬜ 평지 | ⛰️ 산악 | 🏢 시가지 | 🔵 자유군 | 🔴 공산군 | 💥 교전지</p>", unsafe_allow_html=True)

        # 📊 3. 하단 잔존 게이지 및 텍스트 로그 업데이트
        with log_placeholder.container():
            st.markdown(f"### ⚔️ **제 {turn} 턴 전황 보고** (현재 격전지 지형: {current_tile} | 돌발 변수: `{evt['title']}`)")
            st.caption(f"💬 *전장 보고: {evt['desc']}*")
            
            b_per = (B_HP / blue_start_HP) * 100
            r_per = (R_HP / red_start_HP) * 100
            
            col_b, col_r = st.columns(2)
            with col_b:
                st.write(f"🔵 **자유진영 군세:** {round(b_per, 1)}% ({int(B_HP)}명)")
                st.progress(B_HP / blue_start_HP)
            with col_r:
                st.write(f"🔴 **공산진영 군세:** {round(r_per, 1)}% ({int(R_HP)}명)")
                st.progress(R_HP / red_start_HP)
                
            st.markdown(f"**💥 교전 피해:** 자유군 타격량 {int(b_inflict)} ⚔️ 공산군 타격량 {int(r_inflict)}")
            st.markdown("---")
            
        turn += 1
        time.sleep(1.2) # 지도가 움직이는 모습을 관측할 수 있도록 시간 간격 조정

    # 최종 결과 보고
    st.header("🏁 참모본부 최종 전과 분석 보고서")
    if B_HP > 0 and R_HP == 0:
        st.success(f"🏆 **자유진영 승리!** 공산진영 세력을 격멸하고 작전 지도를 완전히 확보했습니다.")
    elif R_HP > 0 and B_HP == 0:
        st.error(f"💀 **공산진영 승리...** 자유진영 전선이 돌파당하며 작전 지도에서 패퇴했습니다.")
    else:
        st.warning("🤝 **교착 상태:** 양측 모두 전멸하거나 작전 기한 초과로 휴전에 돌입했습니다.")
