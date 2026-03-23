import streamlit as st
import pandas as pd
import json
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="청다움 마스터 V9.0", layout="wide")

# Secrets에서 JSON 키를 읽어와 임시 파일로 만듭니다 (보안 연결용)
if "GOOGLE_JSON_KEY" in st.secrets:
    key_dict = json.loads(st.secrets["GOOGLE_JSON_KEY"])
    # 이 부분은 시스템 내부에서 보안 연결을 처리합니다.
    conn = st.connection("gsheets", type=GSheetsConnection, 
                         service_account_info=key_dict)
else:
    st.error("Secrets에 GOOGLE_JSON_KEY를 등록해 주세요!")
    st.stop()

URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"

st.title("🍡 청다움 최종 마스터 시스템 V9.0")

# 데이터 읽기
df = conn.read(spreadsheet=URL, worksheet="product_db")

with st.form("final_save"):
    st.subheader("📝 상품 실시간 영구 등록")
    name = st.text_input("상품명")
    cost = st.number_input("원가", value=0)
    if st.form_submit_button("💾 구글 시트에 영구 저장"):
        new_row = pd.DataFrame([{"상품명": name, "원가": cost}])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        # 진짜로 시트에 글을 씁니다!
        conn.update(spreadsheet=URL, worksheet="product_db", data=updated_df)
        st.success("🎉 구글 시트에 데이터가 영구 기록되었습니다!")
        st.rerun()

st.write("📋 현재 장부 (구글 시트 연동):")
st.dataframe(df)
