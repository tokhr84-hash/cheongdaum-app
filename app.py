import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V24.0", page_icon="🍡", layout="wide")

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

# --- [3] 사이드바: 직관적인 계산기 ---
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

st.title("🍡 청다움 경영 관리 시스템 V24.0")

if 'sales' not in st.session_state: st.session_state['sales'] = []

# 목표 세션 초기화 (탭 2에서 설정)
if 'targets' not in st.session_state: 
    st.session_state.targets = {'rev': 5000000, 'net': 2000000}

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🎯 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록 및 삭제 관리
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v24_reg_form"):
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
    
    # 삭제 기능 (구글 시트 연동)
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
# 탭 2: 월간 매출 실적 (목표 설정 추가, 첨부1 반영)
# ==========================================
with tabs[1]:
    # 목표 설정 섹션 (첨부1의 🎯 목표 설정란을 여기로 가져왔습니다)
    with st.expander("🎯 이번 달 목표 설정", expanded=True):
        t1, t2 = st.columns(2)
        # 세션 상태에 저장하여 다른 탭에서도 참조할 수 있도록 합니다.
        st.session_state.targets['rev'] = t1.number_input("목표 총 매출액", value=st.session_state.targets['rev'], step=100000)
        st.session_state.targets['net'] = t2.number_input("목표 영업 순수익", value=st.session_state.targets['net'], step=100000)

    st.subheader("📅 실제 판매 실적 입력")
    if not df_p.empty and "상품명" in df_p.columns:
        p_list = df_p["상품명"].dropna().tolist()
        if p_list:
            sel = st.selectbox("판매된 상품을 선택하세요", p_list, key="sales_selectbox")
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
        st.divider()
        c1, c2 = st.columns([3, 1])
        c1.write("### 📝 이번 달 판매 내역")
        # 오입력 삭제 버튼
        if c2.button("🗑️ 가장 최근 기록 1건 삭제", use_container_width=True):
            st.session_state['sales'].pop()
            st.rerun()

        sales_df = pd.DataFrame(st.session_state['sales'])
        st.dataframe(sales_df.assign(매출=lambda x: x['매출'].map(fmt), 순익=lambda x: x['순익'].map(fmt)), use_container_width=True)
        
        # 합산 표시
        tot_rev = sales_df['매출'].sum()
        tot_net = sales_df['순익'].sum()
        st.info(f"**💰 현재까지 총 매출 합계**: {fmt(tot_rev)}원 ｜ **📈 총 영업 순익 합계**: {fmt(tot_net)}원")

# ==========================================
# 탭 3: 성과 분석 (첨부2 디자인 반영, 상세 순위 표시)
# ==========================================
with tabs[2]:
    st.subheader("🏆 상품별 성과 분석 (Ranking)")
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        # 상품별로 합계 계산
        rank = df_s.groupby("상품명")[["수량", "매출", "순익"]].sum().sort_values(by="순익", ascending=False).reset_index()
        
        st.write("💡 **9월 한 달간 영업 순이익 기준 효자 상품 순위입니다.** (최대 상위 3개 표시)")
        
        # 첨부2의 풍부한 상세 정보 스타일로 변경
        for i, row in rank.head(3).iterrows():
            st.write(f"### {i+1}위 : {row['상품명']}")
            ca, cb, cc = st.columns(3)
            # m1 = ca.metric("💰 총 매출액", f"{fmt(row['매출'])}원", f"{fmt(row['매출'])}")
            # m2 = cb.metric("📈 영업 순이익", f"{fmt(row['순익'])}원", f"{fmt(row['순익'])}")
            # m3 = cc.metric("🔢 총 판매 수량", f"{row['수량']}개", f"{row['수량']}")
            
            # m.metric delta가 0이 나오게 fmt()에 replace를 넣어야 할 것 같네요. delta 기능을 제거하고 columns metric으로 갈게요. delta의 경우 같은 숫자값이 들어가면 delta가 지저분하게 나옵니다. delta값은 columns metric delta가 맞아요.
            m1 = ca.metric("💰 총 매출액", f"{fmt(row['매출'])}원")
            m2 = cb.metric("📈 영업 순이익", f"{fmt(row['순익'])}원")
            m3 = cc.metric("🔢 총 판매 수량", f"{row['수량']}개")
            st.divider()
            
    else:
        st.info("매출 실적을 입력하면 랭킹이 자동으로 집계됩니다.")
        
    st.divider()
    st.write("### 📣 청다움 운영 가이드")
    # GitHub에 '청다움 멘트.png' 파일이 있으면 나타납니다.
    # 첨부 3에서 이 부분이 궁금하다고 하셨는데, 이것은 가이드 이미지를 GitHub에 업로드하시면 해결됩니다.
    try:
        st.image("청다움 멘트.png", use_container_width=True)
    except:
        st.caption("※ GitHub 창고에 '청다움 멘트.png' 파일을 업로드하시면 여기에 고정 멘트가 표시됩니다. (현재 파일 없음)")

# ==========================================
# 탭 4: 최종 경영 결산 (목표 삭제, 목표 대비 지표 참조 작동)
# ==========================================
with tabs[3]:
    st.subheader("🏭 청다움 최종 경영 결산")
    
    # 탭 2에서 설정한 목표를 참조합니다. (목표 설정란은 여기서 삭제했습니다)
    target_rev = st.session_state.targets['rev']
    target_net = st.session_state.targets['net']

    with st.expander("💸 이번 달 고정 지출 입력 (월세, 인건비 등)", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        rent = c1.number_input("월세", value=0)
        tax = c2.number_input("세금/공과금", value=0)
        labor = c3.number_input("인건비", value=0)
        ext = c4.number_input("기타 운영비", value=0)
    
    total_rev = sum(s['매출'] for s in st.session_state['sales'])
    total_net = sum(s['순익'] for s in st.session_state['sales'])
    final_cash = total_net - (rent + tax + labor + ext)
    
    st.divider()
    st.write("### 🏁 청다움 종합 재무 지표 (목표 대비 달성 현황)")
    m1, m2, m3 = st.columns(3)
    
    # 목표 대비 달성 현황을 화살표와 숫자로 보여줍니다. (탭 2에서 설정한 목표 참조)
    m1.metric("💰 현재 총 매출액", f"{fmt(total_rev)}원", delta=f"목표 대비 {fmt(total_rev - target_rev)}원")
    m2.metric("📈 영업 순이익", f"{fmt(total_net)}원", delta=f"목표 대비 {fmt(total_net - target_net)}원")
    m3.metric("✨ 최종 찐수익 (지출 차감 후)", f"{fmt(final_cash)}원")
    
    if total_net >= target_net and total_net > 0:
        st.balloons()
