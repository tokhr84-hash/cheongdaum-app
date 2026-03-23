import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V9.3", page_icon="🍡", layout="wide")

# 스트림릿이 Secrets에서 알아서 키를 찾아 연결합니다 (가장 안전하고 확실한 방법)
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🍡 청다움 영구 저장 시스템 V9.3")

# --- [2] 데이터 읽기 ---
try:
    # 설정을 다 마쳤으므로 이제 주소 없이도 읽어옵니다.
    df = conn.read(ttl=0)
    st.success("✅ 구글 시트 금고와 시스템적으로 완벽히 연결되었습니다!")
except Exception as e:
    st.error(f"연결 확인 중: {e}")
    st.info("💡 Secrets 박스에 [connections.gsheets] 설정이 잘 되었는지 확인해 주세요.")
    st.stop()

# --- [3] 실시간 영구 저장 기능 ---
with st.form("final_save_form"):
    st.subheader("📝 신규 상품 영구 등록")
    c1, c2 = st.columns(2)
    p_name = c1.text_input("상품명")
    p_cost = c2.number_input("원가", value=0)
    
    if st.form_submit_button("💾 구글 시트에 영구 저장"):
        if p_name:
            # 새 데이터 준비
            new_row = pd.DataFrame([{"상품명": p_name, "원가": p_cost, "마진": 0.4, "권장가": int(p_cost*1.7)}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # 구글 시트에 즉시 업데이트
            conn.update(data=updated_df)
            st.success(f"🎉 '{p_name}'이(가) 구글 장부에 기록되었습니다!")
            st.rerun()

st.divider()
st.write("📋 현재 구글 시트 실시간 장부")
st.dataframe(df, use_container_width=True)
