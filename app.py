import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# ==========================================
# [1] 시스템 설정 및 보안 엔진 가동
# ==========================================
st.set_page_config(page_title="청다움 경영 관리 마스터", page_icon="🍡", layout="wide")

# 숫자 콤마 표시용 스마트 필터
def fmt(val): 
    try: return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# 구글 시트 마스터 키 연결 (Secrets 자동 인식)
conn = st.connection("gsheets", type=GSheetsConnection)

# 장부 읽어오기
try:
    df_p = conn.read(ttl=0)
except Exception as e:
    st.error(f"데이터 연결 오류: {e}")
    st.stop()

# ==========================================
# [2] 사이드바: 청다움 전용 스마트 계산기
# ==========================================
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

# ==========================================
# [3] 메인 화면 및 탭 구성
# ==========================================
st.title("🍡 청다움 경영 관리 시스템 V10.0")
st.success("✅ 구글 시트 금고와 완벽히 연결되었습니다! (모든 데이터 영구 저장 가동 중)")

# 임시 저장소 초기화 (매출 기록용)
if 'sales' not in st.session_state: st.session_state['sales'] = []

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ------------------------------------------
# 탭 1: 상품 정보 등록 (구글 시트 연동)
# ------------------------------------------
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("master_reg_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", use_container_width=True)
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                
                # 구글 시트 업데이트 실행
                conn.update(data=updated_df)
                st.success(f"🎉 '{p_name}' 구글 시트 영구 저장 완료!")
                st.rerun()

    st.divider()
    st.write("📋 현재 구글 시트 실시간 장부")
    if not df_p.empty:
        display_df = df_p.copy()
        if "원가" in display_df.columns: display_df["원가"] = display_df["원가"].apply(fmt)
        if "권장가" in display_df.columns: display_df["권장가"] = display_df["권장가"].apply(fmt)
        st.dataframe(display_df, use_container_width=True)

# ------------------------------------------
# 탭 2: 월간 매출 분석
# ------------------------------------------
with tabs[1]:
    st.subheader("📅 월간 매출 실적 입력")
    if not df_p.empty and "상품명" in df_p.columns:
        p_list = df_p["상품명"].dropna().unique().tolist()
        if p_list:
            sel = st.selectbox("판매 상품 선택", p_list)
            p_info = df_p[df_p["상품명"] == sel].iloc[0]
            
            ca, cb, cc = st.columns(3)
            ap = ca.number_input("실제 판매가", value=int(float(p_info["권장가"])))
            qty = cb.number_input("판매 수량", value=1, step=1)
            
            if cc.button("실적 추가", use_container_width=True):
                rev = float(ap) * qty
                net = (float(ap) - float(p_info["원가"])) * qty
                st.session_state['sales'].append({"상품명": sel, "판매가": ap, "수량": qty, "총매출": rev, "순익": net})
                st.rerun()
    else:
        st.info("먼저 [탭 1]에서 상품을 등록해 주세요.")
        
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        display_s = df_s.copy()
        display_s["판매가"] = display_s["판매가"].apply(fmt)
        display_s["총매출"] = display_s["총매출"].apply(fmt)
        display_s["순익"] = display_s["순익"].apply(fmt)
        st.dataframe(display_s, use_container_width=True)

# ------------------------------------------
# 탭 3: 상품 판매 분석 (Rank)
# ------------------------------------------
with tabs[2]:
    st.subheader("🏆 상품별 성과 랭킹")
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        rank_df = df_s.groupby("상품명")[["수량", "총매출", "순익"]].sum().sort_values(by="순익", ascending=False).reset_index()
        
        display_r = rank_df.copy()
        display_r["총매출"] = display_r["총매출"].apply(fmt)
        display_r["순익"] = display_r["순익"].apply(fmt)
        st.dataframe(display_r, use_container_width=True)
    else:
        st.info("매출 데이터가 입력되면 랭킹이 자동으로 표시됩니다.")
        
    st.divider()
    st.write("### 📣 청다움 운영 가이드")
    try: 
        st.image("청다움 멘트.png", use_container_width=True)
    except: 
        st.caption("※ GitHub 창고에 '청다움 멘트.png'를 올리면 여기에 표시됩니다.")

# ------------------------------------------
# 탭 4: 최종 결산 (명칭 완벽 적용)
# ------------------------------------------
with tabs[3]:
    st.subheader("🏭 최종 경영 결산")
    with st.expander("💸 이번달 고정 외부 비용", expanded=True):
        c1, c2, c3 = st.columns(3)
        rent = c1.number_input("월세", value=0)
        tax = c2.number_input("세금등", value=0)
        ext = c3.number_input("외부비용(기타)", value=0)
    
    total_rev = sum(float(s.get('총매출', 0)) for s in st.session_state['sales'])
    total_net = sum(float(s.get('순익', 0)) for s in st.session_state['sales'])
    total_out = float(rent + tax + ext)
    final_cash = total_net - total_out
    
    st.divider()
    st.write("### 🏁 청다움 종합 재무 지표")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 총 매출", f"{fmt(total_rev)}원")
    m2.metric("📈 영업 순수익", f"{fmt(total_net)}원")
    m3.metric("💸 합산 외부비용", f"{fmt(total_out)}원")
    m4.metric("✨ 최종 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}")
