import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="청다움 경영 관리 V7.4", layout="wide")

# 대표님 시트 주소 (가장 깔끔한 주소로 고정)
URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🍡 청다움 경영 관리 시스템 V7.4")

try:
    # 에러 방지를 위해 아주 단순하게 읽어옵니다.
    df = conn.read(spreadsheet=URL, worksheet="product_db")
    st.success("✅ [청다움_DB] 금고와 성공적으로 연결되었습니다!")
    st.write("📋 현재 장부 상태:")
    st.dataframe(df)
except Exception as e:
    st.error("❌ 아직 구글 시트 1행이 비어있거나 연결이 불안정합니다.")
    st.info("💡 구글 시트 1행에 '상품명', '원가', '마진', '권장가'라고 적으셨나요?")
