import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V26.0", page_icon="🍡", layout="wide")

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

st.title("🍡 청다움 경영 관리 시스템 V26.0")

if 'sales' not in st.session_state: st.session_state['sales'] = []
if 'targets' not in st.session_state: st.session_state.targets = {'rev': 10000000, 'net': 4000000}

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🏆 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 및 삭제
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v26_reg_form"):
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
        
        st.divider()
        tot_rev = sales_df['총매출'].sum()
        tot_net = sales_df['순익'].sum()
        avg_margin = round((tot_net / tot_rev * 100), 1) if tot_rev > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("총 합산", f"{fmt(tot_rev)}원", f"{fmt(tot_rev - st.session_state.targets['rev'])} (목표대비)")
        col2.metric("총 합산순 수익", f"{fmt(tot_net)}원", f"{fmt(tot_net - st.session_state.targets['net'])} (목표대비)")
        col3.metric("평균 수익률", f"{avg_margin}%")

# ==========================================
# 탭 3: 성과 분석 (오타 수정 완료)
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
        
        # 4. 판매순위 (오타 수정 완료)
        r_qty = grouped.sort_values(by="수량", ascending=False)[["상품명", "수량"]].head(3).reset_index(drop=True)
        r_qty.index = range(1, len(r_qty)+1)
        c4.markdown("📦 **판매순위**")
        c4.dataframe(r_qty, use_container_width=True)
    else:
        st.info("판매 데이터를 추가하시면 순위가 표시됩니다.")
        
    st.divider()
    st.write("### 📣 결과 분석")
    try:
        st.image("청다움 멘트.png", use_container_width=True)
    except:
        st.caption("※ 하단의 [이미지 업로드 가이드]를 참고하여 '청다움 멘트.png'를 업로드해 주세요.")

# ==========================================
# 탭 4: 최종 경영 결산 (라벨 수정 완료)
# ==========================================
with tabs[3]:
    st.subheader("🏭 최종 결산")
    
    with st.expander("💸 이번 달 외부 입력", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        rent = c1.number_input("월세", value=0, step=10000)
        labor = c2.number_input("인건비", value=0, step=10000)
        tax = c3.number_input("공과금", value=0, step=10000)
        etc1 = c4.number_input("세금", value=0, step=10000)  # '등'을 '세금'으로 수정 완료
        etc2 = c5.number_input("기타비용", value=0, step=10000)
    
    total_expenses = rent + labor + tax + etc1 + etc2
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
