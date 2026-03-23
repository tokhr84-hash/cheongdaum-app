import streamlit as st
import pandas as pd
import numpy as np
import json
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V17.0", page_icon="🍡", layout="wide")

def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 보안 엔진 가동 (Secrets에서 직접 읽기) ---
try:
    # Secrets에서 ID와 열쇠를 직접 가져옵니다.
    target_id = st.secrets["gsheet_id"]
    key_info = json.loads(st.secrets["service_account"], strict=False)
    
    # 연결 주소 생성 (ID 방식)
    full_url = f"https://docs.google.com/spreadsheets/d/{target_id}/edit?usp=sharing"
    
    conn = st.connection("gsheets", type=GSheetsConnection, service_account_info=key_info)
    
    # 장부 로드 ( product_db 탭 )
    df_p = conn.read(spreadsheet=full_url, worksheet="product_db", ttl=0)
    st.success("✅ [청다움_DB] 금고와 완벽하게 연결되었습니다! 이제 입력 가능합니다.")
except Exception as e:
    st.error(f"⚠️ 연결 대기 중: {e}")
    st.info("💡 400 에러 해결을 위해 Secrets 박스 설정을 V17.0용으로 바꿔주세요.")
    # 에러가 나도 앱이 멈추지 않게 빈 데이터프레임 생성
    df_p = pd.DataFrame(columns=["상품명", "원가", "마진", "권장가"])

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

st.title("🍡 청다움 경영 관리 시스템 V17.0")

# 매출 기록 세션
if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v17_reg_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="v17_bom")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # 강제 업데이트 실행
                try:
                    conn.update(spreadsheet=full_url, worksheet="product_db", data=updated_df)
                    st.success(f"🎉 '{p_name}' 저장 성공!")
                    st.balloons()
                    st.rerun()
                except Exception as write_err:
                    st.error(f"저장 실패: {write_err}")

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 구글 시트 실시간 장부")
        disp = df_p.copy()
        for col in ["원가", "권장가"]:
            if col in disp.columns: disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, use_container_width=True)
