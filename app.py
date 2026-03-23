import streamlit as st
import pandas as pd
import numpy as np
import json
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V20.0", page_icon="🍡", layout="wide")

def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 보안 엔진 강제 가동 (편집자 권한 획득) ---
try:
    # Secrets에서 열쇠(JSON)를 꺼내서 연결 시 강제로 주입합니다.
    conf = st.secrets["connections"]["gsheets"]
    key_info = json.loads(conf["service_account"], strict=False)
    
    # [핵심] service_account_info를 직접 전달하여 '공용'이 아닌 '편집자' 모드로 접속합니다.
    conn = st.connection("gsheets", type=GSheetsConnection, service_account_info=key_info)
    
    SHEET_URL = conf["spreadsheet"]
    df_p = conn.read(spreadsheet=SHEET_URL, worksheet="product_db", ttl=0)
    st.success("✅ [청다움_DB] 편집자 권한으로 완벽하게 접속되었습니다!")
except Exception as e:
    st.error(f"연결 설정 확인 중: {e}")
    st.stop()

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

st.title("🍡 청다움 경영 관리 시스템 V20.0")

if 'sales' not in st.session_state: st.session_state['sales'] = []
tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 분석", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (성공의 풍선이 터지는 곳)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("final_v20_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 청다움 a세트")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="v20_bom")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # [여기가 성공의 포인트] 편집자 권한으로 밀어넣습니다!
                conn.update(spreadsheet=SHEET_URL, worksheet="product_db", data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료! 드디어 해냈습니다!")
                st.balloons()
                st.rerun()

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 영구 저장된 상품 목록")
        disp = df_p.copy()
        if "원가" in disp.columns: disp["원가"] = disp["원가"].apply(fmt)
        if "권장가" in disp.columns: disp["권장가"] = disp["권장가"].apply(fmt)
        st.dataframe(disp, use_container_width=True)
