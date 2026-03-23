import streamlit as st
import pandas as pd
import json
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V9.2", page_icon="🍡", layout="wide")

# 비밀 금고(Secrets)에서 키를 꺼내 '부드럽게' 읽어옵니다.
try:
    if "GOOGLE_JSON_KEY" in st.secrets:
        # strict=False 옵션을 넣어 특수문자 오류를 강제로 해결합니다.
        key_info = json.loads(st.secrets["GOOGLE_JSON_KEY"], strict=False)
        conn = st.connection("gsheets", type=GSheetsConnection, service_account_info=key_info)
    else:
        st.error("금고(Secrets)에 GOOGLE_JSON_KEY를 넣어주세요!")
        st.stop()
except Exception as e:
    st.error(f"보안 키 형식 오류: {e}")
    st.info("💡 Secrets 박스에서 따옴표를 ''' (홑따옴표 3개)로 쓰셨는지 확인해 주세요!")
    st.stop()

# 대표님 구글 시트 주소
URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"

st.title("🍡 청다움 영구 저장 시스템 V9.2")

# --- [2] 데이터 읽기 ---
try:
    df = conn.read(spreadsheet=URL, worksheet="product_db", ttl=0)
    st.success("✅ 구글 시트 금고와 완벽하게 연결되었습니다!")
except:
    df = pd.DataFrame(columns=["상품명", "원가", "마진", "권장가"])

# --- [3] 실시간 영구 저장 (탭 1 기능) ---
with st.form("save_form_v92"):
    st.subheader("📝 신규 상품 영구 등록")
    c1, c2 = st.columns(2)
    p_name = c1.text_input("상품명")
    p_cost = c2.number_input("원가", value=0)
    
    if st.form_submit_button("💾 구글 시트에 영구 저장"):
        if p_name:
            # 새 줄 추가 및 전송
            new_row = pd.DataFrame([{"상품명": p_name, "원가": p_cost, "마진": 0.4, "권장가": int(p_cost*1.7)}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # 구글 시트에 즉시 업데이트 (이게 진짜 성공의 순간입니다!)
            conn.update(spreadsheet=URL, worksheet="product_db", data=updated_df)
            st.success(f"🎉 '{p_name}'이(가) 구글 장부에 기록되었습니다!")
            st.rerun()

st.divider()
st.write("📋 현재 구글 시트 연동 장부")
st.dataframe(df, use_container_width=True)
