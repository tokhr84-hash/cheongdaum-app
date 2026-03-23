import streamlit as st
import pandas as pd
import numpy as np
import json
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 경영 관리 V11.0", page_icon="🍡", layout="wide")

# 숫자 콤마 표시용
def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 마스터 키 강제 연결 (보안 강화) ---
try:
    # Secrets에서 직접 키를 읽어와 연결 엔진을 만듭니다.
    conf = st.secrets["connections"]["gsheets"]
    conn = st.connection("gsheets", type=GSheetsConnection, 
                         service_account_info=json.loads(conf["service_account"], strict=False))
    
    # 장부 실시간 로드
    df_p = conn.read(spreadsheet=conf["spreadsheet"], worksheet="product_db", ttl=0)
    st.success("✅ [청다움_DB] 금고와 완벽하게 연결되었습니다! (쓰기 권한 획득)")
except Exception as e:
    st.error(f"⚠️ 연결 확인 중: {e}")
    st.info("💡 Secrets 박스의 [connections.gsheets] 설정을 다시 확인해 주세요.")
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

st.title("🍡 청다움 경영 관리 시스템 V11.0")

# 매출 데이터 세션 유지
if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (강제 저장 로직)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("final_master_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="bom_editor")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                # 1. 계산
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                
                # 2. 데이터 합치기
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # 3. [핵심] 구글 시트 강제 업데이트 (워크시트 명시)
                conn.update(spreadsheet=conf["spreadsheet"], worksheet="product_db", data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료! 시트를 확인해 보세요.")
                st.rerun()

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 구글 시트 장부 현황")
        disp = df_p.copy()
        disp["원가"] = disp["원가"].apply(fmt)
        disp["권장가"] = disp["권장가"].apply(fmt)
        st.dataframe(disp, use_container_width=True)
