import streamlit as st
import math

# 페이지 레이아웃을 넓게 설정
st.set_page_config(page_title="ROKA 란체스터 작전 시뮬레이터", layout="wide")

st.title("🎖️ 대한민국 육군 병과·제대별 란체스터 시뮬레이터")
st.write("나무위키 공식 육군 군사특기 편제와 부대 규모를 반영한 최종 정밀 계산기입니다.")

# 1. 부대 규모(제대) 및 가중치 정의
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

# 2. 대한민국 육군 병과 분류 및 전투력 지수 (소총수 기본 화력 = 1.0 기준)
ROKA_BRANCHES = {
    "⚔️ 전투 병과": {
        "보병 (소총수/박격포/특전 등)": 1.0,
        "기갑 (K계열 전차/장갑차 조종 등)": 25.0,
        "포병 (K-9자주포/다연장로켓 등)": 60.0,
        "방공 (천마/비호/휴대용유도무기 등)": 40.0,
        "정보 (UAV운용/드론/전자전 등)": 15.0,
        "공병 (전투공병/공병장비 등)": 5.0,
        "정보통신 (전술통신/무선전송 등)": 3.0,
        "항공 (공격헬기/항공운용 등)": 120.0
    },
    "🛠️ 기술/행정/특수 병과": {
        "화생방 (정찰/제독/연막 등)": 4.0,
        "군수 (병기정비/탄약/병참보급/수송 등)": 2.0,
        "군사경찰 (특임대/수사 등)": 3.5,
        "의무 (군의/의정/간호 등 - 전투 지속력 버프)": 2.0,
        "행정/특수 (인사/재정/정훈/법무/군종 등)": 1.0
    }
}

st.markdown("---")

# 3. 부대 규모(제대) 선택 슬라이더
selected_scale = st.select_slider(
    "📏 작전 수행 부대 규모(제대) 선택",
    options=list(UNIT_SCALES.keys()),
    value="중대 (Company)"
)
scale_weight = UNIT_SCALES[selected_scale]

st.info(f"현재 설정된 작전 규모: **{selected_scale}** (기본 단위 대비 작전 가중치 {scale_weight:,}배 적용)")

st.markdown("---")

# 4. 양측 진영 입력 칸 배치 (왼쪽 아군 / 오른쪽 적군)
col1, col2 = st.columns(2)

# 각 진영의 입력값을 담을 그릇(딕셔너리)
a_inputs = {}
b_inputs = {}

with col1:
    st.subheader("🔵 대한민국 육군 (A 진영)")
    # 모든 병과의 기본값은 0으로 설정
    for category, branches in ROKA_BRANCHES.items():
        st.caption(f"[{category}]")
        for branch in branches.keys():
            a_inputs[branch] = st.number_input(f"A군 {branch} 수량", min_value=0, value=0, step=1, key=f"a_{branch}")
    
    st.markdown("**🛡️ 전술 지휘 요소**")
    a_leader = st.slider("아군 지휘관 역량 및 사기 (배율)", 0.5, 2.0, 1.0, 0.1, key="a_leader_slider")

with col2:
    st.subheader("🔴 대항군 / 적군 (B 진영)")
    for category, branches in ROKA_BRANCHES.items():
        st.caption(f"[{category}]")
        for branch in branches.keys():
            b_inputs[branch] = st.number_input(f"B군 {branch} 수량", min_value=0, value=0, step=1, key=f"b_{branch}")
            
    st.markdown("**🛡️ 전술 지휘 요소**")
    b_leader = st.slider("적군 지휘관 역량 및 사기 (배율)", 0.5, 2.0, 1.0, 0.1, key="b_leader_slider")

st.markdown("---")

# 5. 전투 시뮬레이션 계산 로직 ('딸깍' 버튼)
if st.button("⚔️ 대한민국 육군 교전 시뮬레이션 시작 (딸깍)", type="primary", use_container_width=True):
    
    # 총 화력 및 총 장비 수량 계산 함수
    def evaluate_force(inputs, leader_bonus):
        total_combat_power = 0.0
        total_units_count = 0
        
        for category, branches in ROKA_BRANCHES.items():
            for branch, power_val in branches.items():
                quantity = inputs[branch]
                total_units_count += quantity
                # 화력 = 수량 * 병과 고유 전투력
                total_combat_power += (quantity * power_val)
                
        # 지휘관 보너스 반영
        total_combat_power *= leader_bonus
        return total_combat_power, total_units_count

    a_power, a_count = evaluate_force(a_inputs, a_leader)
    b_power, b_count = evaluate_force(b_inputs, b_leader)
    
    if a_count == 0 or b_count == 0:
        st.error("⚠️ 양측 진영에 최소 1개 이상의 병과에 병력/장비를 배치해야 전투가 성립됩니다!")
    else:
        # 제대(규모) 가중치를 반영한 란체스터 제곱 법칙 계산
        # 공식: (총 병력 수 * 제대 가중치)^2 * 계산된 총 화력 지수
        a_final_force = ((a_count * scale_weight) ** 2) * a_power
        b_final_force = ((b_count * scale_weight) ** 2) * b_power
        
        st.header("📊 전장 시뮬레이션 분석 리포트")
        
        if a_final_force > b_final_force:
            # 아군 승리 시 생존율 계산
            survival_ratio = math.sqrt((a_final_force - b_final_force) / a_final_force)
            st.success("🏆 **대한민국 육군(A)의 전술적 압승입니다!**")
            st.metric(label="아군 예상 생존율", value=f"{round(survival_ratio * 100, 1)}%")
            
            st.write("### 📉 아군 잔존 병력 예측")
            for branch in a_inputs.keys():
                if a_inputs[branch] > 0:
                    remains = int(a_inputs[branch] * survival_ratio)
                    st.write(f"- {branch}: {a_inputs[branch]} ➡️ **{remains}** (손실: {a_inputs[branch] - remains})")
            st.caption("※ 적(B 진영) 부대는 전멸(전투불능) 하였습니다.")
            
        elif b_final_force > a_final_force:
            # 적군 승리 시 생존율 계산
            survival_ratio = math.sqrt((b_final_force - a_final_force) / b_final_force)
            st.error("💀 **아군이 패배하고 전선이 붕괴되었습니다...**")
            st.metric(label="적군 예상 생존율", value=f"{round(survival_ratio * 100, 1)}%")
            
            st.write("### 📈 적군 잔존 병력 예측")
            for branch in b_inputs.keys():
                if b_inputs[branch] > 0:
                    remains = int(b_inputs[branch] * survival_ratio)
                    st.write(f"- {branch}: {b_inputs[branch]} ➡️ **{remains}**")
            st.caption("※ 대한민국 육군(A 진영) 부대는 전멸(전투불능) 하였습니다.")
            
        else:
            st.warning("🤝 **무승부: 두 부대가 격렬하게 충돌하여 동귀어진했습니다.** 양측 모두 생존자가 없습니다.")
