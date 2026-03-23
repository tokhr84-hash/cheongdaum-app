import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 경영 관리 V7.2", page_icon="🍡", layout="wide")

# 대표님의 구글 시트 주소 (직통 연결)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"

# 연결 엔진 가동
conn = st.connection("gsheets", type=GSheetsConnection)

def fmt(val): # 숫자 콤마 표시용
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 사이드바 계산기 (대표님 요청 기능) ---
with st.sidebar:
    st.title("🧮 빠른 리터")
    if 'calc_val' not in st.session_state: st.session_state['calc_val'] = ""
    st.code(st.session_state['calc_val'] if st.session_state['calc_val'] else "0", language="text")
    for row in [['7', '8', '9', '/'], ['4', '5', '6', '*'], ['1', '2', '3', '-'], ['C', '0', '=', '+']]:
        cols = st.columns(4)
        for i, key in enumerate(row):
            if cols[i].button(key, key=f"c_{key}_{row}"):
                if key == 'C': st.session_state['calc_val'] = ""
                elif key == '=':
                    try: st.session_state['calc_val'] = str(eval(st.session_state['calc_val']))
                    except: st.session_state['calc_val'] = "Error"
                else: st.session_state['calc_val'] += key
                st.rerun()

st.title("🍡 청다움 경영 관리 시스템 V7.2")

# --- [3] 데이터 연결 확인 (강제 연결 로직) ---
try:
    # Secrets가 없어도 주소로 직접 읽어옵니다.
    df_test = conn.read(spreadsheet=SHEET_URL, worksheet="product_db", ttl=5)
    st.success("✅ [청다움_DB] 금고와 실시간으로 연결되었습니다!")
except Exception as e:
    st.error(f"❌ 시트 연결에 문제가 있습니다. 시트 하단 탭 이름을 'product_db'로 만들어주세요!")
    # 에러 메시지가 너무 복잡하면 무시하시라고 간략히 표시합니다.

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 분석", "🎯 상품 판매 분석(Rank)", "🏭 최종 결산"])

if 'p_db' not in st.session_state: st.session_state['p_db'] = []
if 'sales' not in st.session_state: st.session_state['sales'] = []

# ==========================================
# 탭 1: 상품 정보 등록 (기능 복구)
# ==========================================
with tabs[0]:
    st.subheader("📍 상품 정보 등록")
    with st.form("p_reg_final"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", use_container_width=True)
        if st.form_submit_button("✨ 상품 DB 등록"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                st.session_state['p_db'].append({"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price})
                st.success(f"[{p_name}] 등록 완료!")

# ==========================================
# 탭 4: 최종 결산 (명칭 완벽 고정)
# ==========================================
with tabs[3]:
    st.subheader("🏭 최종 경영 결산")
    with st.expander("💸 이번달 고정 외부 비용", expanded=True):
        c1, c2, c3 = st.columns(3)
        rent = c1.number_input("월세", value=0)
        tax = c2.number_input("세금등", value=0)
        ext = c3.number_input("외부비용(기타)", value=0)
    
    # 계산 오류 방지를 위한 정밀 연산
    total_rev = sum(float(s.get('매출', 0)) for s in st.session_state['sales'])
    total_net = sum(float(s.get('순익', 0)) for s in st.session_state['sales'])
    total_out = float(rent + tax + ext)
    final_cash = total_net - total_out
    
    st.divider()
    st.write("### 🏁 청다움 경영 지표")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 총 매출", f"{fmt(total_rev)}원")
    m2.metric("📈 영업 순수익", f"{fmt(total_net)}원")
    m3.metric("💸 합산 외부비용", f"{fmt(total_out)}원")
    m4.metric("✨ 최종 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}")
