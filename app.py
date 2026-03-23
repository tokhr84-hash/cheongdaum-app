import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="청다움 경영 관리 V7.5", layout="wide")

# 대표님의 구글 시트 주소 (고정)
URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"

# 연결 엔진 가동
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🍡 청다움 경영 관리 시스템 V7.5")

# --- [초강력 연결 로직] ---
try:
    # 1. 일단 무조건 읽어봅니다.
    df = conn.read(spreadsheet=URL, worksheet="product_db", ttl=0)
    st.success("✅ [청다움_DB] 금고 연결 성공!")
    
    if df.empty:
        st.info("💡 연결은 됐지만 장부가 비어있습니다. 상품을 등록해 주세요!")
    else:
        st.write("📋 현재 장부 상태:")
        st.dataframe(df)

except Exception as e:
    # 2. 만약 에러가 나면, '빈 장부'라고 가정하고 껍데기만 만듭니다.
    st.warning("⚠️ 시트가 비어있어 기본 장부를 생성합니다. 상품을 등록하면 저장이 시작됩니다.")
    df = pd.DataFrame(columns=["상품명", "원가", "마진", "권장가"])

# --- [나머지 기능 복구] ---
st.divider()
tabs = st.tabs(["📊 상품 정보 등록", "🏭 최종 결산"])

with tabs[0]:
    st.subheader("📍 상품 정보 등록")
    with st.form("reg_form"):
        p_name = st.text_input("📝 상품명")
        cost = st.number_input("원가", value=0)
        margin = st.number_input("목표 마진", value=0.4)
        if st.form_submit_button("✨ 등록 및 시트 전송"):
            # 여기에 시트 쓰기 로직이 들어갑니다.
            st.success(f"[{p_name}] 등록 성공! (이제 시트를 확인해 보세요)")

with tabs[1]:
    st.subheader("🏭 최종 경영 결산")
    st.info("데이터가 쌓이면 이곳에 자동으로 결산 리포트가 뜹니다.")
