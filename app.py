import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V13.0", page_icon="🍡", layout="wide")

# 숫자 콤마 표시용 함수
def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 정석 연결 (Secrets 자동 인식) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- [3] 사이드바: 청다움 스마트 계산기 ---
if 'calc_val' not in st.session_state: st.session_state['calc_val'] = ""
with st.sidebar:
    st.title("🧮 빠른 리터")
    st.code(st.session_state['calc_val'] if st.session_state['calc_val'] else "0", language="text")
    for row in [['7', '8', '9', '/'], ['4', '5', '6', '*'], ['1', '2', '3', '-'], ['C', '0', '=', '+']]:
        cols = st.columns(4)
        for i, key in enumerate(row):
            if cols[i].button(key, key=f"btn_{key}_{row}"):
                if key == 'C': st.session_state['calc_val'] = ""
                elif key == '=':
                    try: st.session_state['calc_val'] = str(eval(st.session_state['calc_val']))
                    except: st.session_state['calc_val'] = "Error"
                else: st.session_state['calc_val'] += key
                st.rerun()

st.title("🍡 청다움 경영 관리 시스템 V13.0")

# 장부 실시간 로드 및 연결 확인
try:
    df_p = conn.read(ttl=0)
    st.success("✅ 구글 시트 금고와 완벽하게 연결되었습니다! (영구 저장 가동 중)")
except Exception as e:
    st.error(f"⚠️ 연결 오류: {e}")
    st.stop()

# 실시간 매출 기록용 세션 (앱 구동 중 유지)
if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (구글 시트 영구 저장)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("master_v13_reg"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", key="v13_bom")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # 구글 시트 업데이트
                conn.update(data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료! 구글 시트를 확인해 보세요.")
                st.rerun()

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 구글 시트 장부 현황")
        disp = df_p.copy()
        if "원가" in disp.columns: disp["원가"] = disp["원가"].apply(fmt)
        if "권장가" in disp.columns: disp["권장가"] = disp["권장가"].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# ==========================================
# 탭 2: 월간 매출 실적
# ==========================================
with tabs[1]:
    st.subheader("📅 판매 실적 입력")
    if not df_p.empty and "상품명" in df_p.columns:
        p_list = df_p["상품명"].dropna().unique().tolist()
        sel = st.selectbox("상품 선택", p_list)
        p_info = df_p[df_p["상품명"] == sel].iloc[0]
        
        ca, cb, cc = st.columns(3)
        ap = ca.number_input("실제 판매가", value=int(float(p_info["권장가"])))
        qty = cb.number_input("판매 수량", value=1, step=1)
        
        if cc.button("판매 기록 추가", use_container_width=True):
            rev = float(ap) * qty
            net = (float(ap) - float(p_info["원가"])) * qty
            st.session_state['sales'].append({"상품명": sel, "단가": ap, "수량": qty, "매출": rev, "순익": net})
            st.rerun()
            
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        st.dataframe(df_s.assign(매출=lambda x: x['매출'].map(fmt), 순익=lambda x: x['순익'].map(fmt)), use_container_width=True)

# ==========================================
# 탭 3: 성과 분석 (Ranking)
# ==========================================
with tabs[2]:
    st.subheader("🏆 상품별 성과 랭킹")
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        rank = df_s.groupby("상품명")[["수량", "매출", "순익"]].sum().sort_values(by="순익", ascending=False).reset_index()
        st.table(rank.assign(매출=lambda x: x['매출'].map(fmt), 순익=lambda x: x['순익'].map(fmt)))
    else:
        st.info("매출 실적을 입력하면 랭킹이 나타납니다.")

# ==========================================
# 탭 4: 최종 경영 결산
# ==========================================
with tabs[3]:
    st.subheader("🏭 최종 경영 결산")
    c1, c2, c3 = st.columns(3)
    rent = c1.number_input("월세", value=0)
    tax = c2.number_input("세금등", value=0)
    ext = c3.number_input("기타 비용", value=0)
    
    t_rev = sum(s['매출'] for s in st.session_state['sales'])
    t_net = sum(s['순익'] for s in st.session_state['sales'])
    final = t_net - (rent + tax + ext)
    
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 총 매출", f"{fmt(t_rev)}원")
    m2.metric("📈 영업 순익", f"{fmt(t_net)}원")
    m3.metric("✨ 최종 찐수익", f"{fmt(final)}원", delta=f"{fmt(final)}")
