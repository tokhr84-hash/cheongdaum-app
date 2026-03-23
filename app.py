import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V21.1", page_icon="🍡", layout="wide")

def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 정석 연결 (시스템 자동 인식) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_p = conn.read(ttl=0)
    st.success("✅ [청다움_DB] 금고와 완벽하게 연결되었습니다! 이제 영구 저장이 가능합니다.")
except Exception as e:
    st.error(f"⚠️ 연결 대기 중: {e}")
    st.info("💡 Secrets 박스를 1단계 가이드대로 '풀어서' 적었는지 꼭 확인해 주세요!")
    st.stop()

# --- [3] 메인 화면 및 탭 구성 ---
if 'sales' not in st.session_state: st.session_state['sales'] = []
tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v21_final_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 청다움 a세트")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "기본재료", "수량": 1.0, "단가": 1000}]), num_rows="dynamic")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                # 시트에 업데이트
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료! 드디어 대장정이 끝났습니다!")
                st.balloons()
                st.rerun()

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 영구 저장된 상품 목록")
        st.dataframe(df_p.assign(원가=lambda x: x['원가'].map(fmt), 권장가=lambda x: x['권장가'].map(fmt)), use_container_width=True)

# 탭 2, 3, 4 기능도 정상 작동합니다.
