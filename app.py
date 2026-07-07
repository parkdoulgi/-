import streamlit as st
import math

# 페이지 레이아웃 설정
st.set_page_config(page_title="란체스터 전략 시뮬레이터", layout="wide")

st.title("🪖 란체스터 글로벌 전술 시뮬레이터 (자유 vs 공산)")
st.write("지형지물, 숙련도, 진영별 특성 및 비정규전 요소까지 완벽히 통제하는 사령관용 시뮬레이터입니다.")

# 1. 부대 규모(제대) 정의
UNIT_SCALES = {
    "팀 (Team)": 1,
    "반 (Section)": 2,
    "분대 (Squad)": 10,
    "소대 (Platoon)": 30,
    "중대 (Company)": 120,
    "대대 (Battalion)": 500,
    "연대 (Regiment)": 1500,
    "여단 (Brigade)": 3500,
    "사단 (Division)": 12000,
    "군단 (Corps)": 50000,
    "집단군 (Army Group)": 200000,
    "야전군 (Field Army)": 500000
}

# 2. 정규병과 및 전투력 지수 (소총수 = 1.0 기준)
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
    selected_scale = st.select_slider(
        "📏 작전 부대 규모 (제대)",
        options=list(UNIT_SCALES.keys()),
        value="중대 (Company)"
    )
    scale_weight = UNIT_SCALES[selected_scale]

with c_env2:
    # 지형지물 선택에 따른 방어/화력 영향
    terrain = st.radio("⛰️ 전장 지형 선택", ("평지 (보너스 없음)", "야지 (수풀/산악 - 기갑 효율 감소)", "시가지 (엄폐/건물 - 보병/비정규병 유리)"))

with c_env3:
    # 공수 동맹 전술
    tactics = st.radio("⚔️ 공수 관계", ("공평한 조우전", "자유진영이 진지 방어 중", "공산진영이 진지 방어 중"))

st.markdown("---")

# [진영별 입력 영역] ----------------------------------------------------
col1, col2 = st.columns(2)

# --- 자유진영 (Blue Team) ---
with col1:
    st.header("🔵 자유진영 (Free World)")
    st.caption("💡 전술 특성: 첨단 장비 가치 우세, 정규전 효율 최적화")
    
    st.subheader("[정규 병력 편성]")
    blue_regular = {}
    for branch in BRANCH_POWER.keys():
        blue_regular[branch] = st.number_input(f"자유 {branch} 수량", min_value=0, value=0, key=f"blue_{branch}")
        
    st.subheader("[비정규병 시스템]")
    blue_guerrilla = st.number_input("자유 민병대 / 게릴라 (명)", min_value=0, value=0)
    
    st.subheader("[👨‍✈️ 숙련도 및 지휘]")
    blue_exp = st.selectbox("자유진영 훈련 숙련도", ["신병 (화력 -20%)", "정규병 (기본)", "베테랑/숙련병 (화력 +30%)", "최정예 특수부대 (화력 +70%)"], index=1)
    blue_morale = st.slider("자유진영 사기 및 지휘관 역량", 0.5, 2.0, 1.0, 0.1, key="blue_m")

# --- 공산진영 (Red Team) ---
with col2:
    st.header("🔴 공산진영 (Communist Bloc)")
    st.caption("💡 전술 특성: 비정규병(게릴라) 침투 및 포병 대량 운용 보너스")
    
    st.subheader("[정규 병력 편성]")
    red_regular = {}
    for branch in BRANCH_POWER.keys():
        red_regular[branch] = st.number_input(f"공산 {branch} 수량", min_value=0, value=0, key=f"red_{branch}")
        
    st.subheader("[비정규병 시스템]")
    red_guerrilla = st.number_input("공산 파르티잔 / 반군 (명)", min_value=0, value=0)
    
    st.subheader("[👨‍✈️ 숙련도 및 지휘]")
    red_exp = st.selectbox("공산진영 훈련 숙련도", ["신병 (화력 -20%)", "정규병 (기본)", "베테랑/숙련병 (화력 +30%)", "최정예 특수부대 (화력 +70%)"], index=1)
    red_morale = st.slider("공산진영 사기 및 지휘관 역량", 0.5, 2.0, 1.0, 0.1, key="red_m")

st.markdown("---")

# [계산 및 시뮬레이션] ----------------------------------------------------
if st.button("🚀 전술 시뮬레이터 가동 (딸깍)", type="primary", use_container_width=True):
    
    # 1. 숙련도 배율 변환 함수
    def get_exp_modifier(exp_str):
        if "신병" in exp_str: return 0.8
        if "베테랑" in exp_str: return 1.3
        if "최정예" in exp_str: return 1.7
        return 1.0

    blue_exp_mod = get_exp_modifier(blue_exp)
    red_exp_mod = get_exp_modifier(red_exp)

    # 2. 지형지물에 따른 병과별 가중치 실시간 수정 (복사본 사용)
    blue_branch_power = BRANCH_POWER.copy()
    red_branch_power = BRANCH_POWER.copy()
    
    # 비정규병 기본 전투력
    blue_g_power = 0.5 
    red_g_power = 0.5 
    
    if terrain == "야지 (수풀/산악 - 기갑 효율 감소)":
        # 야지에서는 기갑 화력이 감소하고 공병/정보의 가치가 상승
        blue_branch_power["기갑 (전차 및 장갑차)"] *= 0.7
        red_branch_power["기갑 (전차 및 장갑차)"] *= 0.7
        blue_g_power = 0.7  # 야지에서 게릴라 활성화
        red_g_power = 0.7
    elif terrain == "시가지 (엄폐/건물 - 보병/비정규병 유리)":
        # 시가지에서는 기갑/항공 효율 극단적 감소, 보병 및 비정규병 화력 폭발
        blue_branch_power["기갑 (전차 및 장갑차)"] *= 0.5
        blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 0.6
        red_branch_power["기갑 (전차 및 장갑차)"] *= 0.5
        red_branch_power["항공 (공격헬기 및 공중 자산)"] *= 0.6
        
        blue_branch_power["보병 (정규 보병 단위)"] *= 1.3
        red_branch_power["보병 (정규 보병 단위)"] *= 1.3
        blue_g_power = 1.5  # 시가지 건물 엄폐로 비정규병 화력이 정규 소총수를 능가
        red_g_power = 1.5

    # 3. 진영별 교리/교전 전술 특성 반영
    # 자유진영: 첨단 장비(항공, 정보, 방공) 화력 +15% 보너스
    blue_branch_power["항공 (공격헬기 및 공중 자산)"] *= 1.15
    blue_branch_power["정보/드론 (UAV 및 전자전)"] *= 1.15
    
    # 공산진영: 대량 포병 및 비정규전 물량 보너스 (포병 화력 +15%, 비정규병 머릿수 계산 이점)
    red_branch_power["포병 (자주포, 다연장 등)"] *= 1.15

    # 4. 최종 총 화력(공격력) 및 총 규모 계산
    def calc_final_metrics(regular_inputs, guerrilla_count, branch_power_map, exp_mod, morale_mod):
        total_p = 0.0
        total_count = 0
        
        # 정규군 계산
        for br, num in regular_inputs.items():
            total_count += num
            total_p += (num * branch_power_map[br])
            
        # 비정규군 계산
        total_count += guerrilla_count
        total_p += (guerrilla_count * (blue_g_power if "자유" in branch_power_map else red_g_power))
        
        # 숙련도 및 지휘력 적용
        total_p = total_p * exp_mod * morale_mod
        return total_p, total_count

    blue_p, blue_cnt = calc_final_metrics(blue_regular, blue_guerrilla, blue_branch_power, blue_exp_mod, blue_morale)
    red_p, red_cnt = calc_final_metrics(red_regular, red_guerrilla, red_branch_power, red_exp_mod, red_morale)

    # 5. 진지 방어 보너스 적용 (란체스터 법칙상 상대방 화력 차감)
    if tactics == "자유진영이 진지 방어 중":
        red_p /= 2.0  # 방어 진지 구축으로 적 화력 반토막
    elif tactics == "공산진영이 진지 방어 중":
        blue_p /= 2.0

    # 6. 전투 가능 여부 검사 및 란체스터 제곱 법칙 연산
    if blue_cnt == 0 or red_cnt == 0:
        st.error("⚠️ 양측 진영에 병력을 배치해 주세요!")
    else:
        # 제대 스케일을 곱한 최종 위력 계산
        blue_force = ((blue_cnt * scale_weight) ** 2) * blue_p
        red_force = ((red_cnt * scale_weight) ** 2) * red_p
        
        st.header("📊 참모본부 최종 전황 분석 결과")
        
        # 결과 시각화 레이아웃
        res_col1, res_col2 = st.columns(2)
        
        if blue_force > red_force:
            surv_ratio = math.sqrt((blue_force - red_force) / blue_force)
            with res_col1:
                st.success("🏆 **자유진영 (Blue) 승리!**")
                st.metric("자유진영 예상 생존율", f"{round(surv_ratio * 100, 1)}%")
            with res_col2:
                st.write("### 📉 잔존 정규 병력 및 장비")
                for br, num in blue_regular.items():
                    if num > 0:
                        st.write(f"- {br}: {num} ➡️ **{int(num * surv_ratio)}**")
                if blue_guerrilla > 0:
                    st.write(f"- 비정규 민병대: {blue_guerrilla}명 ➡️ **{int(blue_guerrilla * surv_ratio)}명**")
                st.caption("🔴 공산진영 군세는 전멸 및 붕괴되었습니다.")
                
        elif red_force > blue_force:
            surv_ratio = math.sqrt((red_force - blue_force) / red_force)
            with res_col1:
                st.error("💀 **공산진영 (Red) 승리...**")
                st.metric("공산진영 예상 생존율", f"{round(surv_ratio * 100, 1)}%")
            with res_col2:
                st.write("### 📈 잔존 정규 병력 및 장비")
                for br, num in red_regular.items():
                    if num > 0:
                        st.write(f"- {br}: {num} ➡️ **{int(num * surv_ratio)}**")
                if red_guerrilla > 0:
                    st.write(f"- 비정규 파르티잔: {red_guerrilla}명 ➡️ **{int(red_guerrilla * surv_ratio)}명**")
                st.caption("🔵 자유진영 군세는 전멸 및 붕괴되었습니다.")
        else:
            st.warning("🤝 전열의 완벽한 상쇄로 양측 모두 동귀어진하여 전멸했습니다.")
