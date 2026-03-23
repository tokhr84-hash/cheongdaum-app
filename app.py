import streamlit as st
import pandas as pd
import numpy as np
import json
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V19.0", page_icon="🍡", layout="wide")

def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 연결 설정 및 이메일 확인 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# 보안 키에서 이메일 주소만 추출하여 대표님께 보여드림
try:
    key_info = json.loads(st.secrets["connections"]["gsheets"]["service_account"], strict=False)
    bot_email = key_info.get("client_email")
    st.info(f"📍 [공유 필수] 아래 이메일을 구글 시트 공유(편집자)에 추가해 주세요:\n\n`{bot_email}`")
except:
    st.error("보안 키를 읽을 수 없습니다. Secrets 설정을 확인해 주세요.")

st.title("🍡 청다움 경영 관리 시스템 V19.0")

# 장부 실시간 로드
try:
    df_p = conn.read(ttl=0)
    st.success("✅ [청다움_DB] 금고 연결 성공! (편집 권한 부여 후 저장을 눌러주세요)")
except Exception as e:
    st.error(f"❌ 연결 실패: {e}")
    st.stop()

if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (권한 확인 후 저장)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v19_master_form"):
        p_name = st.text_input("📝 상품명", placeholder="예: 최종테스트")
        target_m = st.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"항목": "테스트", "수량": 1.0, "단가": 1000}]), num_rows="dynamic", key="v19_bom")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # 편집 권한이 없으면 여기서 에러가 납니다.
                try:
                    conn.update(data=updated_df)
                    st.success(f"🎉 '{p_name}' 저장 완료! 드디어 해냈습니다!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 저장 실패: {e}")
                    st.warning("위의 파란 박스 속 이메일을 구글 시트에 '편집자'로 추가하셨는지 확인해 주세요!")

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 구글 시트 실시간 장부")
        disp = df_p.copy()
        if "원가" in disp.columns: disp["원가"] = disp[col].apply(fmt)
        st.dataframe(disp, use_container_width=True)
