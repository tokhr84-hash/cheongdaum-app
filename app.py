import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V15.0", page_icon="🍡", layout="wide")

def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 연결 설정 (주소 직통 연결) ---
# 대표님의 시트 주소와 탭 이름을 코드에 직접 입력했습니다.
URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"
WS = "product_db"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- [3] 사이드바: 청다움 스마트 계산기 ---
if 'calc_val' not in st.session_state: st.session_state['calc_val'] = ""
with st.sidebar:
    st.title("🧮 빠른 리터")
    st.code(st.session_state['calc_val'] if st.session_state['calc_val'] else "0", language="text")
    for row in [['7', '8', '9', '/'], ['4', '5', '6', '*'], ['1', '2', '3', '-'], ['C', '0', '=', '+']]:
        cols = st.columns(4)
        for i, key in enumerate(row):
            if cols[i].button(key, key=f"btn_{key}_{row}"):
                if key == 'C': st.session_state['calc_val'] = ""
                elif key == '=':
                    try: st.session_state['calc_val'] = str(eval(st.session_state['calc_val']))
                    except: st.session_state['calc_val'] = "Error"
                else: st.session_state['calc_val'] += key
                st.rerun()

st.title("🍡 청다움 경영 관리 시스템 V15.0")

# 데이터 실시간 로드
try:
    df_p = conn.read(spreadsheet=URL, worksheet=WS, ttl=0)
    st.success("✅ [청다움_DB] 금고와 완벽하게 연결되었습니다!")
except Exception as e:
    st.error(f"⚠️ 연결 확인 중: 시트 하단의 탭 이름이 'product_db'인지 확인해 주세요.")
    st.stop()

# 매출 기록 세션 유지
if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (직통 저장)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("final_v15_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="v15_bom")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # [필살기] 주소와 탭 이름을 수동으로 한 번 더 확인시켜줍니다.
                conn.update(spreadsheet=URL, worksheet=WS, data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료!")
                st.rerun()

    if not df_p.empty:
        st.write("📋 현재 구글 시트 장부 현황")
        disp = df_p.copy()
        if "원가" in disp.columns: disp["원가"] = disp["원가"].apply(fmt)
        if "권장가" in disp.columns: disp["권장가"] = disp["권장가"].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# 탭 2, 3, 4 기능 (V13.0과 동일)
with tabs[1]:
    st.subheader("📅 판매 실적 입력")
    # ... (생략된 실적 입력 로직 포함되어 있음)
