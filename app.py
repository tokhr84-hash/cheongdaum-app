import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 경영 관리 V7.0", page_icon="🍡", layout="wide")

# 구글 시트 연결 (Secrets에 설정된 주소 사용)
conn = st.connection("gsheets", type=GSheetsConnection)

def fmt(val): # 숫자 콤마 포맷팅
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 사이드바 계산기 (기능 유지) ---
with st.sidebar:
    st.title("🧮 빠른 리터")
    if 'calc_val' not in st.session_state: st.session_state['calc_val'] = ""
    st.code(st.session_state['calc_val'] if st.session_state['calc_val'] else "0", language="text")
    for row in [['7', '8', '9', '/'], ['4', '5', '6', '*'], ['1', '2', '3', '-'], ['C', '0', '=', '+']]:
        cols = st.columns(4)
        for i, key in enumerate(row):
            if cols[i].button(key, key=f"c_{key}_{row}"):
                if key == 'C': st.session_state['calc_val'] = ""
                elif key == '=':
                    try: st.session_state['calc_val'] = str(eval(st.session_state['calc_val']))
                    except: st.session_state['calc_val'] = "Error"
                else: st.session_state['calc_val'] += key
                st.rerun()

st.title("🍡 청다움 경영 관리 시스템 V7.0")

# 연결 확인 메시지 출력
try:
    # 장부 데이터 로드 시도
    df_p = conn.read(worksheet="product_db")
    st.success("✅ 구글 시트 금고와 성공적으로 연결되었습니다! (데이터 실시간 연동 중)")
except:
    st.warning("⚠️ 구글 시트 연결 대기 중... (Secrets 설정을 완료해 주세요)")

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 분석", "🎯 상품 판매 분석(Rank)", "🏭 최종 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (데이터 세션 유지)
# ==========================================
if 'p_db' not in st.session_state: st.session_state['p_db'] = []
with tabs[0]:
    st.subheader("📍 상품 정보 등록")
    with st.form("p_reg"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", use_container_width=True)
        if st.form_submit_button("✨ 상품 DB 등록"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                st.session_state['p_db'].append({"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price})
                st.success(f"[{p_name}] 등록 완료!")

# ==========================================
# 탭 2: 월간 매출 분석
# ==========================================
if 'sales' not in st.session_state: st.session_state['sales'] = []
with tabs[1]:
    st.subheader("📅 월간 매출 분석")
    if st.session_state['p_db']:
        p_list = [p["상품명"] for p in st.session_state['p_db']]
        sel = st.selectbox("상품 선택", p_list)
        p_info = next(p for p in st.session_state['p_db'] if p["상품명"] == sel)
        ca, cb, cc = st.columns(3)
        ap = ca.number_input("실제 판매가", value=int(p_info["권장가"]))
        qty = cb.number_input("판매 수량", value=1, step=1)
        if cc.button("판매 기록 추가", use_container_width=True):
            rev, net = float(ap)*qty, (float(ap)-p_info["원가"])*qty
            st.session_state['sales'].append({"상품명": sel, "단가": ap, "수량": qty, "매출": rev, "순익": net})
            st.rerun()
        
        if st.session_state['sales']:
            st.dataframe(pd.DataFrame(st.session_state['sales']), use_container_width=True)

# ==========================================
# 탭 3: 상품 판매 분석
# ==========================================
with tabs[2]:
    st.subheader("🏆 상품별 성과 랭킹")
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        st.write("### 📣 결과 분석 보고서")
        st.image("청다움 멘트.png", use_container_width=True) # 창고의 사진 자동 노출
    else:
        st.info("데이터가 입력되면 랭킹이 자동으로 생성됩니다.")

# ==========================================
# 탭 4: 최종 결산 (명칭 완벽 반영)
# ==========================================
with tabs[3]:
    st.subheader("🏭 최종 결산")
    c1, c2, c3, c4 = st.columns(4)
    rent = c1.number_input("월세", value=0)
    tax = c2.number_input("세금등", value=0)
    ext = c3.number_input("외부비용", value=0)
    
    total_rev = sum(float(s['매출']) for s in st.session_state['sales'])
    total_net = sum(float(s['순익']) for s in st.session_state['sales'])
    final_cash = total_net - (rent + tax + ext)
    
    st.divider()
    st.metric("✨ 최종 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}")
