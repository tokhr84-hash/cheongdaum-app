import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 및 보안 엔진 ---
st.set_page_config(page_title="청다움 마스터 V22.0", page_icon="🍡", layout="wide")

def fmt(val): # 숫자 콤마 포맷팅
    try:
        if pd.isna(val) or val == "": return "0"
        return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# 구글 시트 연결 (Secrets 설정을 기반으로 자동 인식)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_p = conn.read(ttl=0)
    st.success("✅ [청다움_DB] 금고가 활짝 열려 있습니다. 실시간 영구 저장 가동 중!")
except Exception as e:
    st.error(f"연결 대기 중입니다. Secrets 설정을 확인해 주세요: {e}")
    st.stop()

# --- [2] 사이드바: 24시간 대기 스마트 계산기 ---
if 'calc_val' not in st.session_state: st.session_state['calc_val'] = ""
with st.sidebar:
    st.title("🧮 빠른 리터")
    st.code(st.session_state['calc_val'] if st.session_state['calc_val'] else "0", language="text")
    for row in [['7', '8', '9', '/'], ['4', '5', '6', '*'], ['1', '2', '3', '-'], ['C', '0', '=', '+']]:
        cols = st.columns(4)
        for i, key in enumerate(row):
            if cols[i].button(key, key=f"sidebar_calc_{key}_{row}"):
                if key == 'C': st.session_state['calc_val'] = ""
                elif key == '=':
                    try: st.session_state['calc_val'] = str(eval(st.session_state['calc_val']))
                    except: st.session_state['calc_val'] = "Error"
                else: st.session_state['calc_val'] += key
                st.rerun()
    st.divider()
    st.caption("청다움 디지털 본사 v22.0 | Kyle 본부장 보고")

st.title("🍡 청다움 경영 관리 시스템 V22.0")

# 매출 기록 세션 (앱 구동 중 유지)
if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 (구글 시트 영구 저장)
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v22_reg_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"항목": "기본재료", "수량": 1.0, "단가": 1000}]), 
                             num_rows="dynamic", key="v22_bom_editor")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                # 시트 업데이트
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료! 경영 장부에 기록되었습니다.")
                st.balloons()
                st.rerun()

    st.divider()
    if not df_p.empty:
        st.write("📋 현재 영구 저장된 상품 목록")
        disp = df_p.copy()
        for col in ["원가", "권장가"]:
            if col in disp.columns: disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# ==========================================
# 탭 2: 월간 매출 실적
# ==========================================
with tabs[1]:
    st.subheader("📅 실제 판매 실적 입력")
    if not df_p.empty:
        p_list = df_p["상품명"].tolist()
        sel = st.selectbox("판매된 상품을 선택하세요", p_list)
        p_info = df_p[df_p["상품명"] == sel].iloc[0]
        
        ca, cb, cc = st.columns(3)
        ap = ca.number_input("실제 판매가", value=int(float(p_info["권장가"])))
        qty = cb.number_input("판매 수량", value=1, step=1)
        
        if cc.button("실적 기록 추가", use_container_width=True):
            rev = float(ap) * qty
            net = (float(ap) - float(p_info["원가"])) * qty
            st.session_state['sales'].append({"상품명": sel, "매출": rev, "순익": net, "수량": qty})
            st.success(f"✅ {sel} 판매 기록이 추가되었습니다.")
            st.rerun()
            
    if st.session_state['sales']:
        st.write("### 📝 이번 달 판매 내역")
        sales_df = pd.DataFrame(st.session_state['sales'])
        st.table(sales_df.assign(매출=lambda x: x['매출'].map(fmt), 순익=lambda x: x['순익'].map(fmt)))

# ==========================================
# 탭 3: 성과 분석 (Rank)
# ==========================================
with tabs[2]:
    st.subheader("🏆 상품별 성과 랭킹")
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        # 상품별로 합계 계산
        rank = df_s.groupby("상품명")[["수량", "매출", "순익"]].sum().sort_values(by="순익", ascending=False).reset_index()
        st.write("💡 **영업 순이익이 가장 높은 효자 상품 순서입니다.**")
        st.table(rank.assign(매출=lambda x: x['매출'].map(fmt), 순익=lambda x: x['순익'].map(fmt)))
    else:
        st.info("매출 실적을 입력하면 랭킹이 자동으로 집계됩니다.")

# ==========================================
# 탭 4: 최종 경영 결산
# ==========================================
with tabs[3]:
    st.subheader("🏭 청다움 최종 경영 결산")
    with st.expander("💸 이번 달 고정 지출 (월세, 세금 등)", expanded=True):
        c1, c2, c3 = st.columns(3)
        rent = c1.number_input("월세", value=0)
        tax = c2.number_input("세금/공과금", value=0)
        ext = c3.number_input("기타 운영비", value=0)
    
    total_rev = sum(s['매출'] for s in st.session_state['sales'])
    total_net = sum(s['순익'] for s in st.session_state['sales'])
    final_cash = total_net - (rent + tax + ext)
    
    st.divider()
    st.write("### 🏁 청다움 종합 재무 지표")
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 총 매출액", f"{fmt(total_rev)}원")
    m2.metric("📈 영업 순이익", f"{fmt(total_net)}원")
    m3.metric("✨ 최종 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}")
    
    if final_cash > 0:
        st.balloons()
        st.write("🎉 **대표님, 이번 달도 흑자 달성을 축하드립니다!**")
