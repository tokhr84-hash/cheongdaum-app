import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 경영 관리 V8.0", page_icon="🍡", layout="wide")

# 구글 시트 주소 (대표님 주소 고정)
URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def fmt(val): # 숫자 콤마 포맷팅
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 사이드바 계산기 (완벽 복구) ---
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

st.title("🍡 청다움 경영 관리 시스템 V8.0")

# --- [3] 데이터 연결 및 자동 저장 로직 ---
try:
    df_p = conn.read(spreadsheet=URL, worksheet="product_db", ttl=0)
    st.success("✅ [청다움_DB] 금고와 실시간 연결 중입니다.")
except:
    df_p = pd.DataFrame(columns=["상품명", "원가", "마진", "권장가"])
    st.info("💡 첫 번째 상품을 등록하면 구글 시트에 자동으로 장부가 만들어집니다.")

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 분석", "🎯 성과 분석(Rank)", "🏭 최종 결산"])

# 세션 상태 초기화 (데이터 휘발 방지)
if 'sales_data' not in st.session_state: st.session_state['sales_data'] = []

# ==========================================
# 탭 1: 상품 정보 등록 (실시간 전송 기능)
# ==========================================
with tabs[0]:
    st.subheader("📍 상품 정보 등록")
    with st.form("p_reg_v8"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", use_container_width=True)
        
        if st.form_submit_button("✨ 상품 DB 등록 및 시트 전송"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_data = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                # [핵심] 구글 시트에 즉시 업데이트
                updated_df = pd.concat([df_p, new_data], ignore_index=True)
                conn.update(spreadsheet=URL, worksheet="product_db", data=updated_df)
                st.success(f"[{p_name}] 등록 완료! 구글 시트 확인해 보세요.")
                st.rerun()

    if not df_p.empty:
        st.write("### 📋 현재 등록 상품 목록")
        st.table(df_p.assign(원가=lambda x: x['원가'].map(fmt), 권장가=lambda x: x['권장가'].map(fmt)))

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
    
    # 임시 계산 (나중에 매출 데이터 연동)
    total_rev = sum(float(s.get('매출', 0)) for s in st.session_state['sales_data'])
    total_net = sum(float(s.get('순익', 0)) for s in st.session_state['sales_data'])
    total_out = float(rent + tax + ext)
    final_cash = total_net - total_out
    
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 총 매출", f"{fmt(total_rev)}원")
    m2.metric("📈 영업 순수익", f"{fmt(total_net)}원")
    m3.metric("💸 합산 외부비용", f"{fmt(total_out)}원")
    m4.metric("✨ 최종 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}")
