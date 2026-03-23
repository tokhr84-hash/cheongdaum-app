import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 및 초기화 ---
st.set_page_config(page_title="청다움 경영 관리 V5.0", page_icon="🍡", layout="wide")

# 구글 시트 주소 (대표님이 주신 주소 고정)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FmTGa_9KGwHvDFLilpSAreb0F5lX1chf1zeLMsv_wYY/edit?usp=sharing"

# 숫자 포맷팅 함수 (콤마 표시 및 정수화)
def fmt(val): 
    try:
        return f"{int(float(str(val).replace(',', ''))):,}"
    except:
        return str(val)

# 데이터 초기 세션 상태 설정
if 'product_db' not in st.session_state: st.session_state['product_db'] = []
if 'sales_history' not in st.session_state: st.session_state['sales_history'] = []
if 'ext_costs' not in st.session_state:
    st.session_state['ext_costs'] = {"월세": 0, "인건비": 0, "공과금": 0, "세금등": 0, "기타비용": 0}
if 'm_goals' not in st.session_state:
    st.session_state['m_goals'] = {"매출목표": 30000000, "순수익목표": 18000000}

# --- [2] 사이드바 계산기 ---
with st.sidebar:
    st.title("🧮 퀵 계산기")
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

st.title("🍡 청다움 경영 관리 시스템 V5.0")
st.divider()

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 분석", "🎯 상품 판매 분석(Rank)", "🏭 최종 결산"])

# ==========================================
# 탭 1: 상품 정보 등록
# ==========================================
with tabs[0]:
    st.subheader("📍 상품 정보 등록")
    with st.form("p_reg"):
        c1, c2 = st.columns([2, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        st.write("🌿 **[원재료등] 입력**") 
        bom_editor = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "", "수량": 0.0, "단가": 0}]), num_rows="dynamic", use_container_width=True)
        if st.form_submit_button("✨ 상품 DB 등록 및 권장가격 산출"):
            if p_name:
                cost = float((bom_editor["수량"] * bom_editor["단가"]).sum())
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                st.session_state['product_db'].append({"상품명": p_name, "원가": cost, "목표마진": target_m, "권장가격": price})
                st.success(f"[{p_name}] 등록 완료!")

    if st.session_state['product_db']:
        st.divider()
        st.write("### 📋 등록된 상품 리스트")
        for idx, row in enumerate(st.session_state['product_db']):
            c1, c2, c3, c4 = st.columns([4, 3, 3, 1])
            c1.write(f"**{row['상품명']}**"); c2.write(f"원가: {fmt(row['원가'])}원")
            c3.success(f"권장가격: {fmt(row['권장가격'])}원")
            if c4.button("삭제", key=f"dp_{idx}"): st.session_state['product_db'].pop(idx); st.rerun()

# ==========================================
# 탭 2: 월간 매출 분석
# ==========================================
with tabs[1]:
    st.subheader("📅 월간 매출 분석")
    if st.session_state['product_db']:
        st.write("#### 🚩 이번달 목표 설정")
        cg1, cg2 = st.columns(2)
        st.session_state['m_goals']['매출목표'] = cg1.number_input("이번달 목표 매출", value=st.session_state['m_goals']['매출목표'], step=1000000)
        st.session_state['m_goals']['순수익목표'] = cg2.number_input("이번달 목표 순수익", value=st.session_state['m_goals']['순수익목표'], step=1000000)

        with st.expander("➕ 판매 데이터 추가", expanded=True):
            p_names = [p["상품명"] for p in st.session_state['product_db']]
            sel_p = st.selectbox("상품 선택", p_names)
            p_info = next(p for p in st.session_state['product_db'] if p["상품명"] == sel_p)
            ca, cb, cc = st.columns(3)
            act_p = ca.number_input("실제 판매가", value=int(p_info["권장가격"]))
            qty = cb.number_input("판매 수량", value=1, step=1)
            if cc.button("목록에 추가", use_container_width=True):
                rev, net = float(act_p)*float(qty), (float(act_p)-float(p_info["원가"]))*float(qty)
                st.session_state['sales_history'].append({"상품명": sel_p, "단가": act_p, "수량": qty, "총매출": rev, "순수익": net, "수익률": net/rev if rev>0 else 0})

        if st.session_state['sales_history']:
            st.write("#### 📋 상세 판매 현황")
            cols_h = st.columns([2, 1, 1, 1.2, 1.2, 1, 0.5])
            for i, h in enumerate(["상품명", "판매가", "수량", "총매출", "순수익", "수익률", "삭제"]): cols_h[i].write(f"**{h}**")
            for idx, item in enumerate(st.session_state['sales_history']):
                c = st.columns([2, 1, 1, 1.2, 1.2, 1, 0.5])
                c[0].write(item["상품명"]); c[1].write(f"{fmt(item['단가'])}원"); c[2].write(f"{item['수량']}개")
                c[3].write(f"**{fmt(item['총매출'])}원**"); c[4].write(f"{fmt(item['순수익'])}원"); c[5].write(f"{item['수익률']:.1%}")
                if c[6].button("🗑️", key=f"ds_{idx}"): st.session_state['sales_history'].pop(idx); st.rerun()
            st.divider()
            total_rev = sum(float(i["총매출"]) for i in st.session_state['sales_history'])
            total_prof = sum(float(i["순수익"]) for i in st.session_state['sales_history'])
            m1, m2, m3 = st.columns(3)
            m1.metric("총 합산 매출", f"{fmt(total_rev)}원", f"{fmt(total_rev - st.session_state['m_goals']['매출목표'])} (목표대비)")
            m2.metric("총 합산 순수익", f"{fmt(total_prof)}원", f"{fmt(total_prof - st.session_state['m_goals']['순수익목표'])} (목표대비)")
            m3.metric("평균 수익률", f"{(total_prof/total_rev if total_rev>0 else 0):.1%}")

# ==========================================
# 탭 3: 상품 판매 분석
# ==========================================
with tabs[2]:
    st.subheader("🏆 상품별 성과 랭킹 분석")
    if st.session_state['sales_history']:
        agg = pd.DataFrame(st.session_state['sales_history']).groupby('상품명').agg({'총매출':'sum', '순수익':'sum', '수량':'sum'}).reset_index()
        agg['수익률'] = agg['순수익'] / agg['총매출']
        def make_rank(df, col, label, is_pct=False):
            res = df[['상품명', col]].sort_values(by=col, ascending=False).reset_index(drop=True)
            res.index += 1
            res = res.reset_index().rename(columns={'index': label})
            res[col] = res[col].apply(lambda x: f"{x:.1%}" if is_pct else fmt(x))
            return res
        c1, c2, c3, c4 = st.columns(4)
        c1.write("📊 **매출 순위**"); c1.dataframe(make_rank(agg, '총매출', '매출 순위'), hide_index=True)
        c2.write("💰 **순수익 순위**"); c2.dataframe(make_rank(agg, '순수익', '순수익 순위'), hide_index=True)
        c3.write("📈 **수익률 순위**"); c3.dataframe(make_rank(agg, '수익률', '수익률 순위', True), hide_index=True)
        c4.write("📦 **판매 수 순위**"); c4.dataframe(make_rank(agg, '수량', '판매 수 순위'), hide_index=True)
        st.divider()
        st.write("### 📣 결과 분석 보고서")
        uploaded_img = st.file_uploader("📸 보고서 멘트 사진을 올려주세요", type=['png', 'jpg'])
        if uploaded_img: st.image(uploaded_img, use_container_width=True)
        else: st.info("👆 위 박스에 사진 파일을 끌어다 놓으세요.")

# ==========================================
# 탭 4: 최종 결산
# ==========================================
with tabs[3]:
    st.subheader("🏭 최종 결산")
    with st.expander("💸 이번달 외부 비용 입력", expanded=True):
        ec = st.session_state['ext_costs']
        c1, c2, c3, c4, c5 = st.columns(5)
        ec["월세"] = c1.number_input("월세", value=ec["월세"])
        ec["인건비"] = c2.number_input("인건비", value=ec["인건비"])
        ec["공과금"] = c3.number_input("공과금", value=ec["공과금"])
        ec["세금등"] = c4.number_input("세금등", value=ec["세금등"])
        ec["기타비용"] = c5.number_input("기타비용", value=ec["기타비용"])
        total_ec = sum(float(v) for v in ec.values())
        st.write(f"**외부비용 합계: {fmt(total_ec)}원**")
    st.divider()
    curr_rev = sum(float(i['총매출']) for i in st.session_state['sales_history'])
    curr_prof = sum(float(i['순수익']) for i in st.session_state['sales_history'])
    real_cash = curr_prof - total_ec
    st.write("### 🏁 최종 경영 결산 대시보드")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🎯 매출목표", f"{fmt(st.session_state['m_goals']['매출목표'])}원")
    m2.metric("💰 매출", f"{fmt(curr_rev)}원")
    m3.metric("📈 순수익", f"{fmt(curr_prof)}원")
    m4.metric("💸 외부비용", f"{fmt(total_ec)}원")
    m5.metric("✨ 찐수익", f"{fmt(real_cash)}원", delta=f"{fmt(real_cash)}")
