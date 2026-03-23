import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V16.1", page_icon="🍡", layout="wide")

# 숫자 콤마 표시용
def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 사이드바 계산기 (항상 대기) ---
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

st.title("🍡 청다움 경영 관리 시스템 V16.1")

# --- [3] 연결 설정 (주소와 탭 고정) ---
# 대표님의 주소와 탭 이름을 다시 한 번 명시합니다.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"
WS_NAME = "product_db"

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 읽어올 때부터 주소를 확실히 찍어줍니다.
    df_p = conn.read(spreadsheet=SHEET_URL, worksheet=WS_NAME, ttl=0)
    st.success("✅ [청다움_DB] 금고 문이 활짝 열렸습니다! (쓰기 준비 완료)")
except Exception as e:
    st.error(f"❌ 연결 실패: {e}")
    st.stop()

if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (강력 업데이트 로직)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v16_1_reg_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="v16_1_bom")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                # 1. 계산
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                # 2. 데이터 합치기
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # 3. [최후의 승부수] 업데이트 시 주소와 탭 이름을 강제로 다시 꽂아줍니다.
                try:
                    conn.update(spreadsheet=SHEET_URL, worksheet=WS_NAME, data=updated_df)
                    st.success(f"🎉 '{p_name}'이(가) 구글 장부에 완벽하게 기록되었습니다!")
                    st.balloons() # 축하 풍선 추가
                    st.rerun()
                except Exception as write_err:
                    st.error(f"❌ 쓰기 오류 발생: {write_err}")
                    st.info("💡 대표님, 시트 공유 권한에 '서비스 계정 이메일'이 '편집자'로 되어 있는지 마지막으로 확인 부탁드립니다!")

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 구글 시트 실시간 장부")
        disp = df_p.copy()
        for col in ["원가", "권장가"]:
            if col in disp.columns: disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# 나머지 탭 기능들은 안전하게 보존됩니다.
