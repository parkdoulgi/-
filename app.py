import streamlit as st
import math
import random

# 페이지 레이아웃 설정
st.set_title = "란체스터 작전술 시뮬레이터"
st.set_page_config(page_title="란체스터 작전술 시뮬레이터", layout="wide")

st.title("🎲 란체스터 글로벌 작전술 시뮬레이터 (전장의 안개 반영)")
st.write("지형과 전술뿐만 아니라 날씨, 보급, 그리고 예측 불가능한 '돌발 변수'까지 실시간으로 계산하는 실전형 시뮬레이터입니다.")

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
    "집단군 (Army Group - 약 200,000명)": 200000,
    "야전군 (Field Army - 약 500,000명)": 500000
}

# 2. 핵심 군사 전술 정의
TACTICAL_OPTIONS = {
    "정면 공격 (Frontal Assault)": {
        "desc": "가장 기본적이고 정직한 공격. 보너스나 페널티가 없습니다.",
        "atk_mod": 1.0, "def_mod": 1.0, "lanchester_law": "제곱"
    },
    "포위 / 이중 포위 (Encirclement)": {
        "desc": "적의 측방과 후방을 차단. 규모의 우위를 극대화합니다. (공격 효율 +40%)",
        "atk_mod": 1.4, "def_mod": 1.0, "lanchester_law": "제곱"
    },
    "전격전 / 기갑 돌격 (Blitzkrieg)": {
        "desc": "기갑 및 항공 자산의 속도를 극대화하여 종심을 타격합니다. (기갑/항공 화력 +50%, 보병 효율 -10%)",
        "atk_mod": 1.2, "def_mod": 0.8, "lanchester_law": "제곱"
    },
    "종심 방어 (Defense in Depth)": {
        "desc": "방어선을 겹겹이 배치하여 적의 공격 에너지를 흡수합니다. (방어력 +50%, 란체스터 선형 법칙 강제 적용으로 피해 최소화)",
        "atk_mod": 0.8, "def_mod": 1.5, "lanchester_law": "선형"
    },
    "소모전 / 파상공세 (Attrition Warfare)": {
        "desc": "화력과 물량으로 적을 갉아먹는 고전적 전술. (포병 화력 +30%, 양측 피해 증가)",
        "atk_mod": 1.3, "def_mod": 0.9, "lanchester_law": "선형"
    },
    "네트워크 중심전 / 다영역작전 (NCW/MDO)": {
        "desc": "드론, 드론 군집, 유무인 복합운용 및 전 영역 합동 작전. (정보/드론/항공 화력 +60%, 지휘관 역량 가중치 증가)",
        "atk_mod": 1.5, "def_mod": 1.2, "lanchester_law": "제곱"
    }
}

# 3. 정규병과 및 기본 전투력 지수
BRANCH_POWER = {
    "보병 (정규 보병 단위)": 1.0,
    "기갑 (전차 및 장갑차)": 25.0,
    "포병 (자주포, 다연장 등)": 60.0,
    "방공 (대공 유도무기 등)": 40.0,
    "정보/드론 (UAV 및 전자전)": 15.0,
    "공병 (전투 및 시설공병)": 5.0,
    "항공 (공격헬기 및 공중 자산)": 120.0
}

# 무작위 돌발 사건(전장의 안개) 풀
RANDOM_EVENTS = [
    {"title": "정상 교전", "desc": "특별한 돌발 변수 없이 정해진 시나리오대로 교전이 진행됩니다.", "blue_mod": 1.0, "red_mod": 1.0},
    {"title": "지단장 전사 (지휘 통제 마비)", "desc": "교전 초기, 자유진영의 주요 지휘관이 저격당해 지휘 체계가 일시 마비되었습니다. (자유진영 화력 -30%)", "blue_mod": 0.7, "red_mod": 1.0},
    {"title": "낙뢰 및 전자기 폭풍", "desc": "강한 낙뢰로 인해 양측의 무선 통신과 드론 자산이 일시 먹통이 되었습니다. (양측 첨단 자산 마비, 전체 화력 -15%)", "blue_mod": 0.85, "red_mod": 0.85},
    {"title": "공산진영 탄약고 대폭발", "desc": "자유진영 게릴라의 은밀한 침투로 공산진영의 전방 탄약고가 폭발했습니다. (공산진영 화력 -35%)", "blue_mod": 1.0, "red_mod": 0.65},
    {"title": "피아식별 오인 사격 (오사)", "desc": "자유진영의 항공 지원 중 오인 사격이 발생해 아군 부대를 타격했습니다. (자유진영 화력 -25%)", "blue_mod": 0.75, "red_mod": 1.0},
    {"title": "악천후로 인한 항공 자산 결항", "desc": "갑작스러운 폭우와 강풍으로 양측 모두 헬기 및 드론을 띄우지 못합니다. (항공/드론 화력 급감, 전체 화력 -20%)", "blue_mod": 0.8, "red_mod": 0.8},
    {"title": "결사 항전 (사기 충천)", "desc": "공산진영 부대가 퇴로가 끊기자 독전대의 감시 하에 미친 듯한 결사 항전을 개시합니다. (공산진영 화력 +25%)", "blue_mod": 1.0, "red_mod": 1.25},
    {"title": "기습적인 야간 야간전 돌입", "desc": "야간 투시경 장비가 우수한 자유진영이 야간 기습을 감행해 완벽한 주도권을 잡았습니다. (자유진영 화력 +30%)", "blue_mod": 1.3, "red_mod": 1.0}
]

st.markdown("---")

# [상단 종합 전장 변수 영역] ----------------------------------------------------
st.subheader("🌐 전장 환경 및 환경적 변수 설정")
c_env1, c_env2, c_env3, c_env4 = st.columns(4)

with c_env1:
    selected_scale = st.selectbox("📏 작전 부대 체급 (제대 규모)", options=list(UNIT_SCALES.keys()), index=4)
    scale_weight = UNIT_SCALES[selected_scale]

with c_env2:
    terrain = st.selectbox("⛰️ 전장 지형 선택", ["평지 (보너스 없음)", "야지 (수풀/산악 - 기갑 효율 감소)", "시가지 (엄폐/건물 - 보병/비정규병 유리)"])

with c_env3:
    # 날씨 변수 추가
    weather = st.selectbox("☀️ 기상 조건", ["맑음 (기본)", "폭우/폭설 (기갑 이동 및 포병 사격 제한)", "짙은 안개 (드론 및 항공 정찰 불가능)"])

with c_env4:
    tactics_relation = st.selectbox("⚔️ 공수 관계", ["공평한 조우전", "자유진영이 진지 방어 중", "공산진영이 진지 방어 중"])

st.markdown("---")

# [진영별 입력 영역] ----------------------------------------------------
col1, col2 = st.columns(2)

# --- 자유진영 (Blue Team) ---
with col1:
    st.header("🔵 자유진영 (Free World)")
    
    st.subheader("[🎖️ 작전 전술 고르기]")
    blue_tactics = st.selectbox("자유진영 적용 전술", list(TACTICAL_OPTIONS.keys()), key="blue_tac")
    st.caption(f"ℹ️ {TACTICAL_OPTIONS[blue_tactics]['desc']}")
    
    st.subheader("[📦 부대 규모 및 보급 변수]")
    blue_unit_count = st.number_input("자유진영 참전 제대 개수 (부대 수)", min_value=0, value=0, step=1, key="blue_uc")
    # 보급 상태 변수 추가
    blue_supply = st.select_slider("자유진영 보급 상태", options=["보급 끊김 (화력 -50%)", "부족", "원활 (기본)", "과충전 (화력 +10%)"], value="원활 (기본)", key="blue_sup")
    
    st.subheader("[정규 병력 편성 (제대 1개당 평균 구성)]")
    blue_regular = {}
    for branch in BRANCH_POWER.keys():
        blue_regular[branch] = st.number_input(f"자유 {branch} 수량", min_value=0, value=0, key=f"blue_{branch}")
        
    st.subheader("[비정규병 시스템]")
    blue_guerrilla = st.number_input("자유 민병대 / 게릴라 총합 (명)", min_value=0, value=0)
    
    st.subheader("[👨‍✈️ 숙련도 및 지휘]")
    blue_exp = st.selectbox("자유진영 훈련 숙련도", ["신병 (화력 -20%)", "정규병 (기본)", "베테랑/숙련병 (화력 +30%)", "최정예 특수부대 (화력 +70%)"], index=1, key="blue_ex")
    blue_morale = st.slider("자유진영 사기 및 지휘관 역량", 0.5, 2.0, 1.0, 0.1, key="blue_m")

# --- 공산진영 (Red Team) ---
with col2:
    st.header("🔴 공산진영 (Communist Bloc)")
    
    st.subheader("[🎖️ 작전 전술 고르기]")
    red_tactics = st.selectbox("공산진영 적용 전술", list(TACTICAL_OPTIONS.keys()), key="red_tac")
    st.caption(f"ℹ️ {TACTICAL_OPTIONS[red_tactics]['desc']}")
    
    st.subheader("[📦 부대 규모 및 보급 변수]")
    red_unit_count = st.number_input("공산진영 참전 제대 개수 (부대 수)", min_value=0, value=0, step=1, key="red_uc")
    # 보급 상태 변수 추가
    red_supply = st.select_slider("공산진영 보급 상태", options=["보급 끊김 (화력 -50%)", "부족", "원활 (기본)", "과충전 (화력 +10%)"], value="원활 (기본)", key="red_sup")
    
    st.subheader("[정규 병력 편성 (제대 1개당 평균 구성)]")
    red_regular = {}
    for branch in BRANCH_POWER.keys():
        red_regular[branch] = st.number_input(f"공산 {branch} 수량", min_value=0, value=0, key=f"red_{branch}")
        
    st.subheader("[비정규병 시스템]")
    red_guerrilla = st.number_input("공산 파르티잔 / 반군 총합 (명)", min_value=0, value=0)
    
    st.subheader("[👨‍✈️ 숙련도 및 지휘]")
    red_exp = st.selectbox("공산진영 훈련 숙련도", ["신병 (화력 -20%)", "정규병 (기본)", "베테랑/숙련병 (화력 +30%)", "최정예 특수부대 (화력 +70%)"], index=1, key="red_ex")
    red_morale = st.slider("공산진영 사기 및 지휘관 역량", 0.5, 2.0, 1.0, 0.1, key="red_m")

st.markdown("---")

# [계산 및 시뮬레이션] ----------------------------------------------------
if st.button("🚀 전술·작전술 시뮬레이터 가동 (딸깍)", type="primary", use_container_width=True):
    
    # 1. 숙련도 변수 변환
    def get_exp_modifier(exp_str):
        if "신병" in exp_str: return 0.8
        if "베테랑" in exp_str: return 1.3
        if "최정예" in exp_str: return 1.7
        return 1.0

    # 2. 보급 변수 배율 변환
    def get_supply_modifier(sup_str):
        if "보급 끊김" in sup_str: return 0.5
        if "부족" in sup_str: return 0.8
        if "과충전" in sup_str: return 1.1
        return 1.0

    blue_exp_mod = get_exp_modifier(blue_exp)
    red_exp_mod = get_exp_modifier(red_exp)
    
    blue_sup_mod = get_supply_modifier(blue_supply)
    red_sup_mod = get_supply_modifier(red_supply)

    # 지형/날씨에 따른 전투력 맵 생성 (복사본)
    blue_branch_power = BRANCH_POWER.copy()
    red_branch_power = BRANCH_POWER.copy()
    
    blue_g_power = 0.5 
    red_g_power = 0.5 
    
    # 지형 변수 반영
    if "야지" in terrain:
        blue_branch_power["기갑 (전차 및 장갑차)"] *= 0.7
        red_branch_power["기갑 (전차 및 장갑차)"] *= 0.7
        blue_g_power = 0.7
        red_g_power = 0.7
    elif "시가지" in terrain:
        blue_branch_power["기갑 (전차 및 장갑차)"] *= 0.5
        blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 0.6
        red_branch_power["기갑 (전차 및 장갑차)"] *= 0.5
        red_branch_power["항공 (공격헬기 및 공중 자산)"] *= 0.6
        blue_branch_power["보병 (정규 보병 단위)"] *= 1.3
        red_branch_power["보병 (정규 보병 단위)"] *= 1.3
        blue_g_power = 1.5
        red_g_power = 1.5

    # 🌤️ 날씨 변수 추가 반영
    if "폭우/폭설" in weather:
        # 진흙탕(기동 불능) 및 시야 제한으로 기갑/포병 화력 감소
        blue_branch_power["기갑 (전차 및 장갑차)"] *= 0.6
        red_branch_power["기갑 (전차 및 장갑차)"] *= 0.6
        blue_branch_power["포병 (자주포, 다연장 등)"] *= 0.7
        red_branch_power["포병 (자주포, 다연장 등)"] *= 0.7
    elif "짙은 안개" in weather:
        # 가시거리 제한으로 정보/드론 및 공격헬기 마비
        blue_branch_power["정보/드론 (UAV 및 전자전)"] *= 0.3
        red_branch_power["정보/드론 (UAV 및 전자전)"] *= 0.3
        blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 0.4
        red_branch_power["항공 (공격헬기 및 공중 자산)"] *= 0.4

    # 진영별 기본 교리 보너스
    blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.15
    blue_branch_power["정보/드론 (UAV 및 전자전)"] *= 1.15
    red_branch_power["포병 (자주포, 다연장 등)"] *= 1.15

    # 선택한 [작전 전술] 보너스 결합
    b_tac_data = TACTICAL_OPTIONS[blue_tactics]
    r_tac_data = TACTICAL_OPTIONS[red_tactics]
    
    if "전격전" in blue_tactics:
        blue_branch_power["기갑 (전차 및 장갑차)"] *= 1.5
        blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.5
        blue_branch_power["보병 (정규 보병 단위)"] *= 0.9
    if "전격전" in red_tactics:
        red_branch_power["기갑 (전차 및 장갑차)"] *= 1.5
        red_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.5
        red_branch_power["보병 (정규 보병 단위)"] *= 0.9
        
    if "네트워크" in blue_tactics:
        blue_branch_power["정보/드론 (UAV 및 전자전)"] *= 1.6
        blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.6
    if "네트워크" in red_tactics:
        red_branch_power["정보/드론 (UAV 및 전자전)"] *= 1.6
        red_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.6

    if "소모전" in blue_tactics:
        blue_branch_power["포병 (자주포, 다연장 등)"] *= 1.3
    if "소모전" in red_tactics:
        red_branch_power["포병 (자주포, 다연장 등)"] *= 1.3

    # 🎲 [전장의 안개] 실시간 무작위 이벤트 추출
    battle_event = random.choice(RANDOM_EVENTS)

    # 최종 화력 및 총원 계산 (보급 및 랜덤 이벤트 변수 곱연산 반영)
    def calc_final_metrics(regular_inputs, guerrilla_count, branch_power_map, exp_mod, morale_mod, unit_count, tac_mod, sup_mod, event_mod):
        total_p = 0.0
        total_regular_in_one_unit = sum(regular_inputs.values())
        total_count = (total_regular_in_one_unit * unit_count) + guerrilla_count
        
        # 정규군 총 화력
        for br, num in regular_inputs.items():
            total_p += (num * unit_count * branch_power_map[br])
            
        # 비정규군 화력
        total_p += (guerrilla_count * (blue_g_power if "자유" in branch_power_map else red_g_power))
        
        # [변수 결합]: 기본화력 * 숙련도 * 지휘관역량 * 전술 * 보급 * 돌발사건
        total_p = total_p * exp_mod * morale_mod * tac_mod * sup_mod * event_mod
        return total_p, total_count

    blue_p, blue_cnt = calc_final_metrics(blue_regular, blue_guerrilla, blue_branch_power, blue_exp_mod, blue_morale, blue_unit_count, b_tac_data["atk_mod"], blue_sup_mod, battle_event["blue_mod"])
    red_p, red_cnt = calc_final_metrics(red_regular, red_guerrilla, red_branch_power, red_exp_mod, red_morale, red_unit_count, r_tac_data["atk_mod"], red_sup_mod, battle_event["red_mod"])

    # 공수 관계 방어선 보너스
    if "자유진영이 진지 방어" in tactics_relation: red_p /= 2.0
    elif "공산진영이 진지 방어" in tactics_relation: blue_p /= 2.0

    # 예외 검사
    if blue_cnt == 0 or red_cnt == 0 or blue_unit_count == 0 or red_unit_count == 0:
        st.error("⚠️ 양측 진영에 참전 부대 수와 병력을 배치해 주세요!")
    else:
        # 물리 법칙 판단
        is_linear_war = (b_tac_data["lanchester_law"] == "선형" or r_tac_data["lanchester_law"] == "선형")
        
        if is_linear_war:
            blue_force = (blue_cnt * scale_weight) * blue_p
            red_force = (red_cnt * scale_weight) * red_p
            law_used = "란체스터 선형 법칙 (고대전/참호전/소모전 양상)"
        else:
            blue_force = ((blue_cnt * scale_weight) ** 2) * blue_p
            red_force = ((red_cnt * scale_weight) ** 2) * red_p
            law_used = "란체스터 제곱 법칙 (현대전 집중 화력 양상)"
        
        # 🚨 화면에 전장의 안개 경고 출력
        st.warning(f"📢 **[전장의 안개 발생] 돌발 사건 발생: {battle_event['title']}**\n\n{battle_event['desc']}")
        
        st.header("📊 참모본부 최종 작전 분석 결과")
        st.caption(f"⚖️ 적용된 물리 법칙: {law_used}")
        
        res_col1, res_col2 = st.columns(2)
        
        if blue_force > red_force:
            surv_ratio = math.sqrt((blue_force - red_force) / blue_force) if not is_linear_war else (blue_force - red_force) / blue_force
            surv_ratio = max(0.01, min(surv_ratio, 1.0))
            with res_col1:
                st.success("🏆 **자유진영 (Blue Team) 작전 성공!**")
                st.metric("자유진영 예상 총 생존율", f"{round(surv_ratio * 100, 1)}%")
                st.write(f"- 선택한 전술: **{blue_tactics}**")
            with res_col2:
                st.write("### 📉 잔존 병력 및 장비 예측 (총합)")
                for br, num in blue_regular.items():
                    total_br = num * blue_unit_count
                    if total_br > 0:
                        st.write(f"- {br}: 총 {total_br} ➡️ **{int(total_br * surv_ratio)}**")
                if blue_guerrilla > 0:
                    st.write(f"- 비정규 민병대: {blue_guerrilla}명 ➡️ **{int(blue_guerrilla * surv_ratio)}명**")
                st.caption("🔴 공산진영 군세는 전장의 무작위 불확실성과 화력 열세로 인해 전멸했습니다.")
                
        elif red_force > blue_force:
            surv_ratio = math.sqrt((red_force - blue_force) / red_force) if not is_linear_war else (red_force - blue_force) / red_force
            surv_ratio = max(0.01, min(surv_ratio, 1.0))
            with res_col1:
                st.error("💀 **공산진영 (Red Team) 작전 성공...**")
                st.metric("공산진영 예상 총 생존율", f"{round(surv_ratio * 100, 1)}%")
                st.write(f"- 선택한 전술: **{red_tactics}**")
            with res_col2:
                st.write("### 📈 잔존 병력 및 장비 예측 (총합)")
                for br, num in red_regular.items():
                    total_br = num * red_unit_count
                    if total_br > 0:
                        st.write(f"- {br}: 총 {total_br} ➡️ **{int(total_br * surv_ratio)}**")
                if red_guerrilla > 0:
                    st.write(f"- 비정규 파르티잔: {red_guerrilla}명 ➡️ **{int(red_guerrilla * surv_ratio)}명**")
                st.caption("🔵 자유진영 군세는 전장의 무작위 불확실성과 화력 열세로 인해 전멸했습니다.")
        else:
            st.warning("🤝 **무승부:** 양측의 작전과 전장 변수가 완벽히 상쇄되었습니다.")
