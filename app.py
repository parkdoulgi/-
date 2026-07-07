import streamlit as st
import math

st.set_page_config(layout="wide") # 화면을 넓게 쓰기 위한 설정
st.title("🪖 란체스터 종합 전장 시뮬레이터")
st.write("보병, 전차, 전장 환경(방어 이점)까지 모두 고려한 실전형 계산기입니다.")

st.markdown("---")

# 화면을 3분할 (아군 / 전장 상황 / 적군)
col1, col_env, col2 = st.columns([2, 1.5, 2])

with col1:
    st.subheader("🔵 아군 (A) 부대 편성")
    A_inf = st.number_input("아군 보병 수 (명)", min_value=0, value=500, step=10)
    A_tank = st.number_input("아군 전차 수 (대)", min_value=0, value=30, step=5)
    
    st.markdown("**🛡️ 아군 숙련도 / 지원**")
    A_morale = st.slider("아군 사기 및 지휘력 (배율)", 0.5, 2.0, 1.0, 0.1)
    A_air = st.checkbox("아군 공중 지원 있음 (화력 +20%)")

with col_env:
    st.subheader("⛰️ 전장 환경 설정")
    st.write("방어 측은 요새나 지형지물의 이점을 얻습니다.")
    defender = st.radio("현재 방어 중인 진영", ("공평한 평지 전투", "아군(A)이 방어 중", "적군(B)이 방어 중"))
    
    # 방어 보너스 계수
    def_bonus = 1.0
    if defender != "공평한 평지 전투":
        def_bonus = st.slider("진지/요새 방어력 배율 (피해 감소)", 1.2, 3.0, 1.5, 0.1)

with col2:
    st.subheader("🔴 적군 (B) 부대 편성")
    B_inf = st.number_input("적군 보병 수 (명)", min_value=0, value=800, step=10)
    B_tank = st.number_input("적군 전차 수 (대)", min_value=0, value=15, step=5)
    
    st.markdown("**🛡️ 적군 숙련도 / 지원**")
    B_morale = st.slider("적군 사기 및 지휘력 (배율)", 0.5, 2.0, 1.0, 0.1)
    B_air = st.checkbox("적군 공중 지원 있음 (화력 +20%)")

st.markdown("---")

# '딸깍' 계산 버튼
if st.button("🚀 전면전 시뮬레이션 시작", type="primary", use_container_width=True):
    
    # --- 군사학적 가중치 설정 ---
    # 보병의 기본 전투력을 1로 잡았을 때, 현대 전차는 보병 수십 명의 가치를 가집니다.
    INF_POWER = 1.0
    TANK_POWER = 15.0 # 전차 1대 = 보병 15명의 화력
    
    # 1. 양측의 순수 총 화력(공격력) 계산
    A_base_power = (A_inf * INF_POWER) + (A_tank * TANK_POWER)
    B_base_power = (B_inf * INF_POWER) + (B_tank * TANK_POWER)
    
    # 버프 반영 (사기 및 공중지원)
    A_total_power = A_base_power * A_morale * (1.2 if A_air else 1.0)
    B_total_power = B_base_power * B_morale * (1.2 if B_air else 1.0)
    
    # 2. 방어 이점 반영 (상대방의 화력을 깎음)
    if defender == "아군(A)이 방어 중":
        B_total_power = B_total_power / def_bonus
    elif defender == "적군(B)이 방어 중":
        A_total_power = A_total_power / def_bonus

    # 3. 란체스터 제곱 법칙 계산 (규모의 제곱 * 화력)
    # 여기서는 보병 수로 환산한 '가상 규모'로 계산합니다.
    A_size_equivalent = A_inf + (A_tank * 5) # 방어력 관점에서의 전차 가치
    B_size_equivalent = B_inf + (B_tank * 5)
    
    A_force = (A_size_equivalent ** 2) * A_total_power
    B_force = (B_size_equivalent ** 2) * B_total_power
    
    # 4. 결과 출력
    st.header("📊 전투 분석 결과")
    
    if A_force > B_force:
        # 아군 승리 시 생존율 계산
        remaining_ratio = math.sqrt((A_force - B_force) / A_force)
        A_surv_inf = round(A_inf * remaining_ratio)
        A_surv_tank = round(A_tank * remaining_ratio)
        
        st.success("🏆 **아군(A)이 승리했습니다!**")
        st.write(f"**남은 아군 병력:** 보병 약 {A_surv_inf}명, 전차 약 {A_surv_tank}대")
        st.caption(f"적군은 전멸했으며, 아군은 초기 병력의 약 {round(remaining_ratio*100, 1)}%가 생존했습니다.")
        
    elif B_force > A_force:
        # 적군 승리 시 생존율 계산
        remaining_ratio = math.sqrt((B_force - A_force) / B_force)
        B_surv_inf = round(B_inf * remaining_ratio)
        B_surv_tank = round(B_tank * remaining_ratio)
        
        st.error("💀 **적군(B)에게 패배했습니다...**")
        st.write(f"**남은 적군 병력:** 보병 약 {B_surv_inf}명, 전차 약 {B_surv_tank}대")
        st.caption(f"아군은 전멸했으며, 적군은 초기 병력의 약 {round(remaining_ratio*100, 1)}%가 생존했습니다.")
        
    else:
        st.warning("🤝 양측 모두 치명적인 피해를 입고 동귀어진했습니다. (무승부)")
