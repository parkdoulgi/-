import streamlit as st
import math

# 페이지 레이아웃 설정
st.set_page_config(page_title="란체스터 작전술 시뮬레이터", layout="wide")

st.title("🎖️ 란체스터 작전술·제대 복합 시뮬레이터 (자유 vs 공산)")
st.write("대규모 전선 관점에서 부대의 제대 규모, 제대 개수, 그리고 핵심 군사 전술을 융합하여 교전 결과를 예측합니다.")

# 1. 부대 규모(제대) 정의 (선택창 형식용)
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

# 2. 전선 규모에서 중요한 핵심 군사 전술 정의 및 효과
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

# 3. 정규병과 및 기본 전투력 지수 (소총수 = 1.0 기준)
BRANCH_POWER = {
    "보병 (정규 보병 단위)": 1.0,
    "기갑 (전차 및 장갑차)": 25.0,
    "포병 (자주포, 다연장 등)": 60.0,
    "방공 (대공 유도무기 등)": 40.0,
    "정보/드론 (UAV 및 전자전)": 15.0,
    "공병 (전투 및 시설공병)": 5.0,
    "항공 (공격헬기 및 공중 자산)": 120.0
}

st.markdown("---")

# [상단 중앙 설정 영역] ----------------------------------------------------
st.subheader("🌐 전장 환경 및 작전 교리 설정")
c_env1, c_env2, c_env3 = st.columns(3)

with c_env1:
    # 바(Slider) 형태에서 드롭다운 선택창(Selectbox)으로 변경
    selected_scale = st.selectbox(
        "📏 작전 부대 체급 (제대 규모)",
        options=list(UNIT_SCALES.keys()),
        index=4 # 기본값 '중대'
    )
    scale_weight = UNIT_SCALES[selected_scale]

with c_env2:
    terrain = st.selectbox("⛰️ 전장 지형 선택", ["평지 (보너스 없음)", "야지 (수풀/산악 - 기갑 효율 감소)", "시가지 (엄폐/건물 - 보병/비정규병 유리)"])

with c_env3:
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
    
    st.subheader("[📦 부대 규모 및 제대 개수]")
    # 제대 개수 선택창 추가
    blue_unit_count = st.number_input("자유진영 참전 제대 개수 (부대 수)", min_value=0, value=0, step=1, key="blue_uc")
    
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
    
    st.subheader("[📦 부대 규모 및 제대 개수]")
    # 제대 개수 선택창 추가
    red_unit_count = st.number_input("공산진영 참전 제대 개수 (부대 수)", min_value=0, value=0, step=1, key="red_uc")
    
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
    
    def get_exp_modifier(exp_str):
        if "신병" in exp_str: return 0.8
        if "베테랑" in exp_str: return 1.3
        if "최정예" in exp_str: return 1.7
        return 1.0

    blue_exp_mod = get_exp_modifier(blue_exp)
    red_exp_mod = get_exp_modifier(red_exp)

    # 지형에 따른 전투력 맵 생성 (복사본)
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

    # 진영별 기본 교리 보너스
    blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.15
    blue_branch_power["정보/드론 (UAV 및 전자전)"] *= 1.15
    red_branch_power["포병 (자주포, 다연장 등)"] *= 1.15

    # ⚔️ 선택한 [작전 전술] 보너스 실시간 추가 결합
    b_tac_data = TACTICAL_OPTIONS[blue_tactics]
    r_tac_data = TACTICAL_OPTIONS[red_tactics]
    
    # 전격전 전술 반영 시 기갑/항공 강화
    if "전격전" in blue_tactics:
        blue_branch_power["기갑 (전차 및 장갑차)"] *= 1.5
        blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.5
        blue_branch_power["보병 (정규 보병 단위)"] *= 0.9
    if "전격전" in red_tactics:
        red_branch_power["기갑 (전차 및 장갑차)"] *= 1.5
        red_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.5
        red_branch_power["보병 (정규 보병 단위)"] *= 0.9
        
    # 네트워크 중심전 전술 반영 시 드론/항공 강화
    if "네트워크" in blue_tactics:
        blue_branch_power["정보/드론 (UAV 및 전자전)"] *= 1.6
        blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.6
    if "네트워크" in red_tactics:
        red_branch_power["정보/드론 (UAV 및 전자전)"] *= 1.6
        red_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.6

    # 소모전 반영 시 포병 강화
    if "소모전" in blue_tactics:
        blue_branch_power["포병 (자주포, 다연장 등)"] *= 1.3
    if "소모전" in red_tactics:
        red_branch_power["포병 (자주포, 다연장 등)"] *= 1.3

    # 최종 화력 및 총원 계산 (제대 개수 반영)
    def calc_final_metrics(regular_inputs, guerrilla_count, branch_power_map, exp_mod, morale_mod, unit_count, tac_mod):
        total_p = 0.0
        # 총원 = (제대당 정규군 수 * 제대 개수) + 비정규군 전체 수
        total_regular_in_one_unit = sum(regular_inputs.values())
        total_count = (total_regular_in_one_unit * unit_count) + guerrilla_count
        
        # 정규군 총 화력
        for br, num in regular_inputs.items():
            total_p += (num * unit_count * branch_power_map[br])
            
        # 비정규군 화력
        total_p += (guerrilla_count * (blue_g_power if "자유" in branch_power_map else red_g_power))
        
        # 숙련도 * 지휘관역량 * 전술계수(공격/방어) 반영
        total_p = total_p * exp_mod * morale_mod * tac_mod
        return total_p, total_count

    blue_p, blue_cnt = calc_final_metrics(blue_regular, blue_guerrilla, blue_branch_power, blue_exp_mod, blue_morale, blue_unit_count, b_tac_data["atk_mod"])
    red_p, red_cnt = calc_final_metrics(red_regular, red_guerrilla, red_branch_power, red_exp_mod, red_morale, red_unit_count, r_tac_data["atk_mod"])

    # 공수 관계(진지 방어) 보너스 추가 반영
    if "자유진영이 진지 방어" in tactics_relation: red_p /= 2.0
    elif "공산진영이 진지 방어" in tactics_relation: blue_p /= 2.0

    # 양측 중 하나라도 부대가 없으면 에러
    if blue_cnt == 0 or red_cnt == 0 or blue_unit_count == 0 or red_unit_count == 0:
        st.error("⚠️ 양측 진영에 참전 제대 개수(부대 수)와 병력을 최소 1개 이상 배치해야 교전이 시작됩니다!")
    else:
        # 란체스터 법칙 계산 (규모 가중치 = 제대 크기 배율)
        # 공식: (총 병력 수 * 제대 크기 배율)^2 * 총 화력 (제곱 법칙 기준)
        # 단, 종심방어나 소모전 같은 전술은 선형 법칙(1:1 소모)을 강제하여 물량 우위를 상쇄시킬 수 있음
        
        # 양측의 법칙 교차 검증 (한쪽이라도 선형 법칙(방어/소모전)을 고르면 전장은 선형전(참호전/지연전) 양상으로 흘러감)
        is_linear_war = (b_tac_data["lanchester_law"] == "선형" or r_tac_data["lanchester_law"] == "선형")
        
        if is_linear_war:
            # 란체스터 선형 법칙 (Square를 적용하지 않고 규모 * 화력으로 단순 비교)
            blue_force = (blue_cnt * scale_weight) * blue_p
            red_force = (red_cnt * scale_weight) * red_p
            law_used = "란체스터 선형 법칙 (고대전/참호전/소모전 양상 적용 - 규모의 제곱 우위 상쇄)"
        else:
            # 란체스터 제곱 법칙 (현대전 집중 포격 양상)
            blue_force = ((blue_cnt * scale_weight) ** 2) * blue_p
            red_force = ((red_cnt * scale_weight) ** 2) * red_p
            law_used = "란체스터 제곱 법칙 (현대전 집중 화력 양상 적용 - 규모의 제곱 우위 발동)"
        
        st.header("📊 참모본부 최종 작전 분석 결과")
        st.caption(f"⚖️ 적용된 물리 법칙: {law_used}")
        
        res_col1, res_col2 = st.columns(2)
        
        if blue_force > red_force:
            surv_ratio = math.sqrt((blue_force - red_force) / blue_force) if not is_linear_war else (blue_force - red_force) / blue_force
            surv_ratio = max(0.01, min(surv_ratio, 1.0)) # 안전장치
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
                st.caption("🔴 공산진영 군세는 작전 지역 내에서 완벽히 격멸되었습니다.")
                
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
                st.caption("🔵 자유진영 군세는 작전 지역 내에서 완벽히 격멸되었습니다.")
        else:
            st.warning("🤝 **무승부:** 양측의 작전 전술이 완벽히 상쇄되어 전열이 동귀어진했습니다.")
