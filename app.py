import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V14.0", page_icon="🍡", layout="wide")

def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 정석 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- [3] 사이드바 계산기 ---
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

st.title("🍡 청다움 경영 관리 시스템 V14.0")

# 구글 시트 주소 (Secrets에서 안전하게 가져옴)
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
    df_p = conn.read(spreadsheet=SHEET_URL, worksheet="product_db", ttl=0)
    st.success("✅ [청다움_DB] 금고와 완벽하게 연결되었습니다!")
except Exception as e:
    st.error(f"⚠️ 연결 오류: {e}")
    st.stop()

if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (강제 주소 주입 저장)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v14_master_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="v14_bom_editor")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                
                # 새 데이터 생성
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # [여기가 핵심!] 주소와 워크시트를 다시 한 번 명시적으로 꽂아줍니다.
                conn.update(spreadsheet=SHEET_URL, worksheet="product_db", data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료!")
                st.rerun()

    if not df_p.empty:
        st.write("📋 현재 구글 시트 장부 현황")
        disp = df_p.copy()
        if "원가" in disp.columns: disp["원가"] = disp["원가"].apply(fmt)
        if "권장가" in disp.columns: disp["권장가"] = disp["권장가"].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# ... (탭 2, 3, 4 코드는 V13.0과 동일하게 유지)
