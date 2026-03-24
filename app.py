대표님, 마케팅팀 카일 본부장입니다!

밤새워 고생하신 덕분에 '도돌이표' 레드박스는 완전히 사라졌고, 이제 청다움 디지털 본사 V1이 거의 완성 단계에 이르렀습니다. 대표님의 집념에 깊은 존경을 표합니다.🍡

말씀하신 **'2가지 핵심 수정 사항'**을 즉시 반영하여, 과거의 익숙한 데이터 표출 방식과 대표님의 마케팅 감각이 담긴 고정 멘트를 예쁘게 다듬은 **[청다움 마스터 V27.0 (V1 최종 완공판)]**을 보고합니다!

🏛️ V27.0 정밀 수술 및 인테리어 결과
탭 2 (목표 대비 달성 현황 복원, 첨부2 반영): 첨부해주신 사진처럼 매출과 순수익 숫자 아래에 **[목표 대비 달성액]**과 **[자동 컬러 화살표(초록/빨강)]**가 직관적으로 보이도록 Streamlit 정석 지표(Delta) 스타일로 완벽하게 복원했습니다.

탭 3 (멘트 이미지 스타일링 및 축소, 첨부4 반영): 대표님께서 보내주신 청다움 멘트.png 파일을 앱 중앙에 **적절한 크기(width=400)**로 줄여서 배치하고, 하단에 정갈하게 고정했습니다. 제목도 대표님의 따뜻한 느낌을 담아 **청다움의 따뜻한 약속**으로 전문적으로 변경했습니다.

💻 [청다움 마스터 V27.0] 전체 코드
GitHub의 app.py를 아래 코드로 마지막으로 덮어씌워 주십시오. 이제 진짜 '청다움 디지털 본사'의 완공입니다!

Python
import streamlit as st
import pandas as pd
import numpy as np
import json
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V27.0", page_icon="🍡", layout="wide")

def fmt(val): 
    try:
        if pd.isna(val) or val == "": return "0"
        return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 구글 시트 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_p = conn.read(ttl=0)
except Exception as e:
    st.error(f"연결 대기 중입니다. {e}")
    st.stop()

# --- [3] 사이드바: 계산기 ---
if 'calc_val' not in st.session_state: st.session_state['calc_val'] = ""
with st.sidebar:
    st.title("🧮 계산기")
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
    st.caption("청다움 디지털 본사 V27.0 | 카일 본부장 보고")

st.title("🍡 청다움 경영 관리 시스템 V27.0")

if 'sales' not in st.session_state: st.session_state['sales'] = []
if 'targets' not in st.session_state: st.session_state.targets = {'rev': 10000000, 'net': 4000000}

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🏆 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 및 삭제
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v27_reg_form"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "기본재료", "수량": 1.0, "단가": 1000}]), num_rows="dynamic")
        
        if st.form_submit_button("💾 구글 시트에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                new_row = pd.DataFrame([{"상품명": p_name, "원가": cost, "마진": target_m, "권장가": price}])
                
                updated_df = pd.concat([df_p, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 '{p_name}' 저장 완료!")
                st.rerun()

    st.divider()
    st.subheader("🗑️ 등록된 상품 삭제")
    if not df_p.empty and "상품명" in df_p.columns:
        del_target = st.selectbox("삭제할 상품을 선택하세요", df_p["상품명"].dropna().tolist())
        if st.button("❌ 선택한 상품 구글 시트에서 완전 삭제"):
            updated_df = df_p[df_p["상품명"] != del_target]
            conn.update(data=updated_df)
            st.warning(f"'{del_target}' 상품이 삭제되었습니다.")
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
    with st.expander("🚩 이번 달 목표 설정", expanded=True):
        t1, t2 = st.columns(2)
        st.session_state.targets['rev'] = t1.number_input("목표 총 매출액", value=st.session_state.targets['rev'], step=1000000)
        st.session_state.targets['net'] = t2.number_input("목표 영업 순수익", value=st.session_state.targets['net'], step=1000000)

    st.subheader("📅 판매 데이터 추가")
    if not df_p.empty and "상품명" in df_p.columns:
        p_list = df_p["상품명"].dropna().tolist()
        if p_list:
            sel = st.selectbox("상품 선택", p_list)
            p_info = df_p[df_p["상품명"] == sel].iloc[0]
            
            ca, cb, cc = st.columns(3)
            ap = ca.number_input("실제 판매가", value=int(float(p_info["권장가"])))
            qty = cb.number_input("판매 수량", value=1, step=1)
            
            if cc.button("목록에 추가", use_container_width=True):
                rev = float(ap) * qty
                net = (float(ap) - float(p_info["원가"])) * qty
                st.session_state['sales'].append({"상품명": sel, "판매가": ap, "수량": qty, "총매출": rev, "순익": net})
                st.rerun()

    if st.session_state['sales']:
        st.divider()
        c1, c2 = st.columns([4, 1])
        c1.write("### 📑 상세 판매현황")
        if c2.button("🗑️ 가장 최근 기록 1건 삭제", use_container_width=True):
            st.session_state['sales'].pop()
            st.rerun()

        sales_df = pd.DataFrame(st.session_state['sales'])
        
        disp_df = sales_df.copy()
        disp_df['수익률'] = (disp_df['순익'] / disp_df['총매출'] * 100).fillna(0).round(1).astype(str) + "%"
        for col in ["판매가", "총매출", "순익"]:
            disp_df[col] = disp_df[col].apply(lambda x: f"{fmt(x)}원")
        disp_df['수량'] = disp_df['수량'].apply(lambda x: f"{x}개")
        
        st.dataframe(disp_df, use_container_width=True)
        
        # 합계 대시보드 (첨부2 스타일로 목표대비 표시 복원)
        st.divider()
        st.write("### 🏁 현재 경영 성과 합계")
        tot_rev = sales_df['총매출'].sum()
        tot_net = sales_df['순익'].sum()
        avg_margin = round((tot_net / tot_rev * 100), 1) if tot_rev > 0 else 0
        
        # 목표 대비 달성액 계산 (Delta값)
        target_rev = st.session_state.targets['rev']
        target_net = st.session_state.targets['net']
        diff_rev = tot_rev - target_rev
        diff_net = tot_net - target_net
        
        col1, col2, col3 = st.columns(3)
        # Delta 인자에 원화 포맷팅된 차액 전달 (Streamlit 표준 스타일)
        col1.metric("💰 총 매출액 합산", f"{fmt(tot_rev)}원", f"{fmt(diff_rev)}원")
        col2.metric("📈 영업 순이익 합산", f"{fmt(tot_net)}원", f"{fmt(diff_net)}원")
        col3.metric("평균 수익률", f"{avg_margin}%")

# ==========================================
# 탭 3: 성과 분석 (오타 수정 및 멘트 이미지 스타일링)
# ==========================================
with tabs[2]:
    st.subheader("🏆 상품별 성과 및 순위 분석")
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        grouped = df_s.groupby("상품명")[["수량", "총매출", "순익"]].sum().reset_index()
        grouped["수익률"] = (grouped["순익"] / grouped["총매출"] * 100).fillna(0).round(1)
        
        c1, c2, c3, c4 = st.columns(4)
        
        # 1. 매출 순위
        r_rev = grouped.sort_values(by="총매출", ascending=False)[["상품명", "총매출"]].head(3).reset_index(drop=True)
        r_rev.index = range(1, len(r_rev)+1)
        r_rev["총매출"] = r_rev["총매출"].apply(fmt)
        c1.markdown("📊 **주요 순위 (매출)**")
        c1.dataframe(r_rev, use_container_width=True)
        
        # 2. 순수익 순위
        r_net = grouped.sort_values(by="순익", ascending=False)[["상품명", "순익"]].head(3).reset_index(drop=True)
        r_net.index = range(1, len(r_net)+1)
        r_net["순익"] = r_net["순익"].apply(fmt)
        c2.markdown("💰 **순수익 순위**")
        c2.dataframe(r_net, use_container_width=True)
        
        # 3. 수익률 순위
        r_mar = grouped.sort_values(by="수익률", ascending=False)[["상품명", "수익률"]].head(3).reset_index(drop=True)
        r_mar.index = range(1, len(r_mar)+1)
        r_mar["수익률"] = r_mar["수익률"].astype(str) + "%"
        c3.markdown("📈 **수익률**")
        c3.dataframe(r_mar, use_container_width=True)
        
        # 4. 판매순위
        r_qty = grouped.sort_values(by="수량", ascending=False)[["상품명", "수량"]].head(3).reset_index(drop=True)
        r_qty.index = range(1, len(r_qty)+1)
        c4.markdown("📦 **판매순위**")
        c4.dataframe(r_qty, use_container_width=True)
    else:
        st.info("판매 데이터를 추가하시면 순위가 표시됩니다.")
        
    st.divider()
    # 청다움 멘트 이미지 스타일링 (중앙 배치, 크기 축소)
    sc1, sc2, sc3 = st.columns([1, 2, 1])
    with sc2:
        st.markdown("<h3 style='text-align: center; color: #4F8BF9;'>📣 청다움의 따뜻한 약속</h3>", unsafe_allow_html=True)
        try:
            # width=400으로 줄여서 중앙 sc2 컬럼에 배치
            st.image("청다움 멘트.png", width=400, caption="고객과 함께하는 따 치유")
        except:
            st.caption("※ GitHub 창고에 '청다움 멘트.png' 파일을 업로드하시면 여기에 표시됩니다.")

# ==========================================
# 탭 4: 최종 경영 결산
# ==========================================
with tabs[3]:
    st.subheader("🏭 최종 결산")
    
    with st.expander("💸 이번 달 외부 입력 (세금 포함)", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        rent = c1.number_input("월세", value=0, step=10000)
        labor = c2.number_input("인건비", value=0, step=10000)
        tax = c3.number_input("공과금", value=0, step=10000)
        tax2 = c4.number_input("세금", value=0, step=10000)
        etc2 = c5.number_input("기타비용", value=0, step=10000)
    
    total_expenses = rent + labor + tax + tax2 + etc2
    st.write(f"**외부비용 합계:** {fmt(total_expenses)}원")
    
    total_rev = sum(s['총매출'] for s in st.session_state['sales']) if st.session_state['sales'] else 0
    total_net = sum(s['순익'] for s in st.session_state['sales']) if st.session_state['sales'] else 0
    final_cash = total_net - total_expenses
    
    st.divider()
    st.write("### 🏁 최종 경영 결산 대시보드")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    m1.metric("🎯 목표 (매출기준)", f"{fmt(st.session_state.targets['rev'])}원")
    m2.metric("💰 매출", f"{fmt(total_rev)}원")
    m3.metric("📈 순수익", f"{fmt(total_net)}원")
    m4.metric("💸 외부비용", f"{fmt(total_expenses)}원")
    m5.metric("✨ 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}" if final_cash > 0 else None)
    
    # 목표 달성 시 축하 풍선
    if diff_net >= 0 and total_net > 0:
        st.balloons()
