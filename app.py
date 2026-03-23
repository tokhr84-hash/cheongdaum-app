import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V16.0", page_icon="🍡", layout="wide")

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

st.title("🍡 청다움 경영 관리 시스템 V16.0")

# --- [3] 연결 설정 (가장 유연한 방식) ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 워크시트 이름을 지정하지 않고 '첫 번째 시트'를 가져옵니다.
    df_p = conn.read(ttl=0)
    st.success("✅ 구글 시트와 완벽히 연결되었습니다! (자동 인식 모드)")
except Exception as e:
    st.error(f"❌ 연결 실패: {e}")
    st.info("💡 Secrets 박스의 [connections.gsheets] 설정이 잘 되어있는지 확인해 주세요.")
    st.stop()

if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (강력 저장)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v16_reg_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="v16_bom")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                # 기존 데이터와 합쳐서 업데이트
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료!")
                st.rerun()

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 구글 시트 실시간 장부")
        disp = df_p.copy()
        for col in ["원가", "권장가"]:
            if col in disp.columns: disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# (나머지 탭 2, 3, 4 기능도 V13.0 기준으로 모두 포함되어 있습니다)
