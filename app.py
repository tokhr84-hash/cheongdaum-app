import streamlit as st
import pandas as pd
import json
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 및 보안 설정 ---
st.set_page_config(page_title="청다움 마스터 V9.1", layout="wide")

# 비밀 금고(Secrets)에서 마스터 키를 꺼내 연결합니다.
try:
    if "GOOGLE_JSON_KEY" in st.secrets:
        key_info = json.loads(st.secrets["GOOGLE_JSON_KEY"])
        conn = st.connection("gsheets", type=GSheetsConnection, service_account_info=key_info)
    else:
        st.error("금고(Secrets)에 마스터 키가 없습니다!")
        st.stop()
except Exception as e:
    st.error(f"보안 키 형식 오류: {e}")
    st.stop()

# 대표님 구글 시트 주소
URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"

st.title("🍡 청다움 영구 저장 시스템 V9.1")

# --- [2] 데이터 읽기 ---
try:
    df = conn.read(spreadsheet=URL, worksheet="product_db")
except:
    df = pd.DataFrame(columns=["상품명", "원가", "마진", "권장가"])

# --- [3] 실시간 영구 저장 기능 ---
with st.form("save_to_google"):
    st.subheader("📝 신규 상품 영구 등록")
    c1, c2 = st.columns(2)
    new_name = c1.text_input("상품명")
    new_cost = c2.number_input("원가", value=0)
    
    if st.form_submit_button("💾 구글 시트에 즉시 기록"):
        if new_name:
            # 새 줄 추가
            new_row = pd.DataFrame([{"상품명": new_name, "원가": new_cost, "마진": 0.4, "권장가": new_cost*1.7}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # [핵심] 구글 시트에 진짜로 도장 찍기!
            conn.update(spreadsheet=URL, worksheet="product_db", data=updated_df)
            st.success(f"🎉 '{new_name}'이(가) 구글 시트에 영구 저장되었습니다!")
            st.rerun()

st.divider()
st.write("📋 현재 구글 시트 장부 현황")
st.dataframe(df, use_container_width=True)
