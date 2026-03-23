import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="청다움 경영 관리 V7.3", layout="wide")

# 대표님 시트 주소
URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🍡 청다움 경영 관리 시스템 V7.3")

# --- [연결 테스트 로직 강화] ---
try:
    # 장부를 읽어옵니다.
    df = conn.read(spreadsheet=URL, worksheet="product_db", ttl=0)
    st.success("✅ [청다움_DB] 금고와 성공적으로 연결되었습니다!")
    if not df.empty:
        st.write("📋 현재 저장된 데이터:")
        st.dataframe(df)
    else:
        st.info("💡 장부가 연결되었으나 현재 비어 있습니다. 1행에 항목 이름을 적어주세요!")
except Exception as e:
    st.error("❌ 연결 실패! 아래 에러 메시지를 본부장에게 알려주세요.")
    st.code(str(e)) # 시스템이 내뱉는 진짜 에러를 보여줍니다.

# ... (나머지 탭 기능들은 위와 동일하게 유지됩니다)
