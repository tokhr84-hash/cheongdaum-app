import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# ==========================================
# 👑 [0] 마스터 및 데이터베이스(Supabase) 설정
# ==========================================
MASTER_ID = "[청다움]"
MASTER_PW = "150328"

# 🔑 아까 복사해두신 주소와 키를 아래의 따옴표 안에 붙여넣어 주세요!
SUPABASE_URL = "https://imgyafnhzrketbjfpxdt.supabase.co" 
SUPABASE_KEY = "여기에_anon_API_Key를_붙여넣으세요"         

# --- [1] 시스템 설정 및 화이트 라벨링 ---
st.set_page_config(page_title="청다움 마스터 V39.1", page_icon="🍡", layout="wide")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden !important;}
.viewerBadge_container__1QSob {display: none !important;}
.viewerBadge_link__1S137 {display: none !important;}
/* 모바일 키보드 가림 방지를 위한 폼 하단 여백 확보 */
[data-testid="stForm"] {margin-bottom: 2rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def fmt(val): 
    try:
        if pd.isna(val) or val == "": 
            return "0"
        return f"{int(float(str(val).replace(',', ''))):,}"
    except: 
        return str(val)

# --- [2] 수파베이스(Supabase) 엔진 가동 ---
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error("데이터베이스 엔진 시동 중 오류가 발생했습니다. URL과 KEY를 다시 확인해주세요.")
    st.stop()

@st.cache_data(ttl=5)
def load_all_data():
    u_res = supabase.table("user_db").select("*").execute()
    p_res = supabase.table("product_db").select("*").execute()
    s_res = supabase.table("sales_db").select("*").execute()
    e_res = supabase.table("expense_db").select("*").execute()
    
    u_df = pd.DataFrame(u_res.data) if u_res.data else pd.DataFrame(columns=["아이디", "비밀번호", "상태"])
    p_df = pd.DataFrame(p_res.data) if p_res.data else pd.DataFrame(columns=["id", "등록자", "상품명", "원가", "마진", "권장가", "소요시간", "공임비"])
    s_df = pd.DataFrame(s_res.data) if s_res.data else pd.DataFrame(columns=["id", "등록자", "날짜", "월", "경로", "상품명", "판매가", "수량", "총매출", "순익"])
    e_df = pd.DataFrame(e_res.data) if e_res.data else pd.DataFrame(columns=["id", "등록자", "월", "월세", "추가인건비", "공과금", "세금", "기타비용"])
    
    return u_df, p_df, s_df, e_df

try:
    df_users, df_master, df_sales, df_expenses = load_all_data()
    # 마스터 계정이 DB에 없다면 최초 1회 강제 생성
    if df_users.empty or MASTER_ID not in df_users['아이디'].values:
        supabase.table("user_db").insert({"아이디": MASTER_ID, "비밀번호": MASTER_PW, "상태": "정상"}).execute()
        st.cache_data.clear()
except Exception as e:
    st.error("장부를 불러오는 데 실패했습니다. 서버 상태를 확인해주세요.")
    st.stop()

# --- [3] 로그인 및 회원가입 로직 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🍡 청다움 경영 관리 플랫폼</h1>", unsafe_allow_html=True)
    st.divider()
    
    log_tab, sign_tab = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with log_tab:
        with st.form("login_form"):
            user_id = st.text_input("아이디(ID)", placeholder=MASTER_ID)
            user_pw = st.text_input("비밀번호(PW)", type="password")
            
            if st.form_submit_button("입장하기", use_container_width=True):
                u_id_str = str(user_id).strip()
                u_pw_str = str(user_pw).strip()
                
                if u_id_str == MASTER_ID and u_pw_str == MASTER_PW:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u_id_str
                    st.rerun()
                else:
                    match = df_users[(df_users["아이디"] == u_id_str) & (df_users["비밀번호"] == u_pw_str)]
                    if not match.empty and match.iloc[0]["상태"] == "정상":
                        st.session_state.logged_in = True
                        st.session_state.current_user = u_id_str
                        st.rerun()
                    else:
                        st.error("로그인 실패 또는 정지된 계정입니다.")
                    
    with sign_tab:
        with st.form("signup_form"):
            new_id = st.text_input("새로운 아이디(ID)")
            new_pw = st.text_input("새로운 비밀번호(PW)", type="password")
            new_pw_check = st.text_input("비밀번호 확인", type="password")
            
            if st.form_submit_button("가입하기", use_container_width=True):
                nid_str = str(new_id).strip()
                npw_str = str(new_pw).strip()
                
                if nid_str in df_users["아이디"].values or nid_str == MASTER_ID:
                    st.warning("이미 존재하는 아이디입니다.")
                elif npw_str != str(new_pw_check).strip():
                    st.warning("비밀번호가 일치하지 않습니다.")
                elif len(nid_str) < 2:
                    st.warning("아이디를 2자 이상 입력해 주세요.")
                else:
                    supabase.table("user_db").insert({"아이디": nid_str, "비밀번호": npw_str, "상태": "정상"}).execute()
                    st.cache_data.clear()
                    st.success(f"가입 완료! '{nid_str}'로 로그인해 주세요.")
    st.stop()

# --- [4] 개인별 데이터 연동 ---
current_user = st.session_state.current_user
is_master = (current_user == MASTER_ID)
legacy_ids = ["cheongdaum", "[cheongdaum]"]

if is_master:
    df_p = df_master[(df_master['등록자'] == current_user) | (df_master['등록자'].isin(legacy_ids))]
    user_sales = df_sales[(df_sales['등록자'] == current_user) | (df_sales['등록자'].isin(legacy_ids))].copy()
    user_expenses = df_expenses[(df_expenses['등록자'] == current_user) | (df_expenses['등록자'].isin(legacy_ids))].copy()
else:
    df_p = df_master[df_master['등록자'] == current_user]
    user_sales = df_sales[df_sales['등록자'] == current_user].copy()
    user_expenses = df_expenses[df_expenses['등록자'] == current_user].copy()

if not user_sales.empty:
    month_list = sorted(user_sales['월'].unique().tolist(), reverse=True)
    curr_m = datetime.now().strftime('%Y-%m')
    if curr_m not in month_list: 
        month_list.insert(0, curr_m)
else:
    month_list = [datetime.now().strftime('%Y-%m')]

if 'targets' not in st.session_state: 
    st.session_state.targets = {'rev': 10000000, 'net': 4000000}

# --- [5] 사이드바 UI ---
with st.sidebar:
    st.title(f"👋 {current_user} 사장님" if not is_master else "👑 대표님(Master)")
    
    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()
        
    st.divider()
    st.subheader("⚙️ 개인 설정")
    # 💡 지시하신 대로 공임 초기값을 0으로 완벽 변경했습니다.
    hourly_wage = st.number_input("나의 시간당 공임(원)", value=0, step=1000) 
    
    st.divider()
    st.title("🧮 계산기")
    
    if 'calc_val' not in st.session_state: 
        st.session_state['calc_val'] = ""
        
    st.code(st.session_state['calc_val'] if st.session_state['calc_val'] else "0", language="text")
    
    for row in [['7', '8', '9', '/'], ['4', '5', '6', '*'], ['1', '2', '3', '-'], ['C', '0', '=', '+']]:
        cols = st.columns(4)
        for i, key in enumerate(row):
            if cols[i].button(key, key=f"sidebar_calc_{key}_{row}"):
                if key == 'C': 
                    st.session_state['calc_val'] = ""
                elif key == '=':
                    try: 
                        st.session_state['calc_val'] = str(eval(st.session_state['calc_val']))
                    except: 
                        st.session_state['calc_val'] = "Error"
                else: 
                    st.session_state['calc_val'] += key
                st.rerun()

# --- [6] 메인 화면 ---
st.title(f"🍡 청다움 경영 관리 시스템 (ID: {current_user})")

c1, c2 = st.columns([3, 1])
with c2: 
    selected_month = st.selectbox("📅 장부 조회 월(Month)", month_list)

if not user_sales.empty:
    monthly_sales = user_sales[user_sales['월'] == selected_month]
else:
    monthly_sales = pd.DataFrame()

if is_master:
    tabs = st.tabs(["📊 상품 정보 등록", "📈 실전 매출 입력", "🏆 성과 시각화", "🏭 경영 결산", "👑 마스터 관리"])
else:
    tabs = st.tabs(["📊 상품 정보 등록", "📈 실전 매출 입력", "🏆 성과 시각화", "🏭 경영 결산"])

# ==========================================
# 탭 1: 상품 등록 (키친코스트형 원가계산 & 모바일 UI 개선)
# ==========================================
with tabs[0]:
    # 모바일 키보드 가림 현상을 막기 위해 폼을 화면 최상단에 Expander로 고정 배치
    with st.expander("📍 신규 상품 영구 등록 (스마트 원가 계산기)", expanded=True):
        with st.form("v39_1_reg_form"):
            c1, c2, c3 = st.columns([2, 1, 1])
            p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
            target_m = c2.number_input("🎯 목표 마진", value=0.4, step=0.1)
            make_time = c3.number_input("⏱️ 제작 소요시간(분)", value=30, step=5)
            
            st.info("💡 [키친코스트 방식] 대용량 구매가격과 실제 레시피 투입량을 적어주시면 원가가 자동 계산됩니다.")
            bom_init = pd.DataFrame([{"항목": "백앙금", "총용량(g,ml)": 5000, "총가격(원)": 15000, "레시피 투입량(g,ml)": 300}])
            bom = st.data_editor(bom_init, num_rows="dynamic", use_container_width=True)
            
            if st.form_submit_button("💾 자동 계산 및 중앙 DB 영구 저장", use_container_width=True):
                if p_name:
                    # 1g당 단가를 도출하여 투입량과 곱하는 '키친코스트' 방식 로직 적용
                    bom["단가계산"] = (pd.to_numeric(bom["총가격(원)"], errors='coerce').fillna(0) / 
                                  pd.to_numeric(bom["총용량(g,ml)"], errors='coerce').replace(0, 1)) * \
                                  pd.to_numeric(bom["레시피 투입량(g,ml)"], errors='coerce').fillna(0)
                    cost = float(bom["단가계산"].sum())
                    labor = (hourly_wage / 60) * make_time
                    price = float(np.round(cost / max(0.01, (1 - target_m)), -1))
                    
                    try:
                        supabase.table("product_db").insert({
                            "등록자": current_user, 
                            "상품명": p_name, 
                            "원가": cost,
                            "마진": target_m, 
                            "권장가": price, 
                            "소요시간": make_time, 
                            "공임비": labor
                        }).execute()
                        st.cache_data.clear()
                        st.success(f"🎉 '{p_name}' (자동계산 원가: {fmt(cost)}원) 저장 완료!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다. (상품명이 중복되었을 수 있습니다)")

    st.divider()
    if not df_p.empty:
        st.write("📋 내 계정에 등록된 상품 목록")
        del_p = st.selectbox("삭제할 상품", df_p["상품명"].dropna().tolist())
        
        if st.button("❌ 선택 상품 삭제", use_container_width=True):
            supabase.table("product_db").delete().eq("등록자", current_user).eq("상품명", del_p).execute()
            st.cache_data.clear()
            st.warning("상품이 삭제되었습니다.")
            st.rerun()
            
        disp = df_p.copy().drop(columns=['id', '등록자'], errors='ignore')
        for col in ["원가", "권장가", "공임비"]:
            if col in disp.columns: 
                disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# ==========================================
# 탭 2: 실전 매출 입력 (모바일 최적화 고정 입력 패널)
# ==========================================
with tabs[1]:
    st.subheader("⚡ 쾌속 매출 입력 패널")
    
    if not df_p.empty:
        with st.container():
            c1, c2 = st.columns([1, 1])
            s_date = c1.date_input("판매 날짜", datetime.now())
            inb = c2.selectbox("유입 경로", ["인스타그램", "네이버예약", "지인소개", "워크인", "기타"])
            
            sel_p = st.selectbox("상품 선택", df_p["상품명"].tolist())
            p_i = df_p[df_p["상품명"] == sel_p].iloc[0]
            
            ca, cb, cc = st.columns([2, 1, 2])
            ap = ca.number_input("실제 판매가", value=int(float(p_i["권장가"])))
            qty = cb.number_input("판매 수량", value=1, step=1)
            
            if cc.button("🚀 장부 기록 (1초 저장)", use_container_width=True):
                rev = float(ap) * qty
                net = rev - (float(p_i["원가"]) * qty) - (float(p_i.get("공임비", 0)) * qty)
                target_m = s_date.strftime("%Y-%m")
                
                try:
                    supabase.table("sales_db").insert({
                        "등록자": current_user, 
                        "날짜": s_date.strftime("%Y-%m-%d"), 
                        "월": target_m,
                        "경로": inb, 
                        "상품명": sel_p, 
                        "판매가": ap, 
                        "수량": qty, 
                        "총매출": rev, 
                        "순익": net
                    }).execute()
                    st.cache_data.clear()
                    st.success("✅ 매출이 등록되었습니다!")
                    st.rerun()
                except Exception:
                    st.error("오류가 발생했습니다.")
    
    st.divider()
    with st.expander(f"🚩 {selected_month}월 목표 세팅 (클릭하여 열기)"):
        t1, t2 = st.columns(2)
        st.session_state.targets['rev'] = t1.number_input("목표 총 매출액", value=st.session_state.targets['rev'])
        st.session_state.targets['net'] = t2.number_input("목표 영업 순수익", value=st.session_state.targets['net'])

    if not monthly_sales.empty:
        st.write(f"### 📑 {selected_month}월 매출 장부")
        
        with st.expander("🗑️ 기록 삭제 (오입력 수정)"):
            opt = {}
            for i, r in monthly_sales.iterrows():
                opt[f"[{r['날짜']}] {r['상품명']} ({fmt(r['총매출'])}원)"] = r['id']
                
            sel_del = st.selectbox("삭제 항목을 선택하세요", list(opt.keys()))
            
            if st.button("❌ 선택 기록 삭제", use_container_width=True):
                target_id = opt[sel_del]
                supabase.table("sales_db").delete().eq("id", int(target_id)).execute()
                st.cache_data.clear()
                st.warning("기록이 삭제되었습니다.")
                st.rerun()
                
        ds = monthly_sales.copy()
        for col in ["판매가", "총매출", "순익"]: 
            ds[col] = pd.to_numeric(ds[col], errors='coerce').fillna(0)
            
        ds['수익률'] = (ds['순익'] / ds['총매출'] * 100).fillna(0).round(1).astype(str) + "%"
        
        for col in ["판매가", "총매출", "순익"]: 
            ds[col] = ds[col].apply(lambda x: f"{fmt(x)}원")
            
        st.dataframe(ds.drop(columns=['id', '등록자', '월'], errors='ignore'), use_container_width=True)

# ==========================================
# 탭 3: 성과 시각화 (Plotly 전문가용 차트 탑재)
# ==========================================
with tabs[2]:
    st.subheader(f"🏆 {selected_month}월 심층 데이터 시각화")
    if not monthly_sales.empty:
        an = monthly_sales.copy()
        for col in ["수량", "총매출", "순익"]: 
            an[col] = pd.to_numeric(an[col], errors='coerce').fillna(0)
            
        c1, c2 = st.columns(2)
        
        # 1. 유입 경로 도넛 차트
        path_data = an.groupby("경로")["총매출"].sum().reset_index()
        fig1 = px.pie(path_data, values='총매출', names='경로', hole=0.4, title="📍 유입 경로별 매출 비중")
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        c1.plotly_chart(fig1, use_container_width=True)
        
        # 2. 상품별 매출 순위 가로형 바 차트
        prod_data = an.groupby("상품명")["총매출"].sum().reset_index().sort_values("총매출", ascending=True)
        fig2 = px.bar(prod_data, x='총매출', y='상품명', orientation='h', title="🏆 상품별 매출 순위", text_auto='.2s')
        c2.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        g = an.groupby("상품명")[["수량", "총매출", "순익"]].sum().reset_index()
        g["수익률"] = (g["순익"] / g["총매출"] * 100).round(1)
        
        c = st.columns(4)
        c[0].write("📊 **매출 Top 3**")
        c[0].dataframe(g.sort_values("총매출", ascending=False).head(3)[["상품명", "총매출"]].assign(총매출=lambda x: x['총매출'].apply(fmt)), use_container_width=True)
        
        c[1].write("💰 **순익 Top 3**")
        c[1].dataframe(g.sort_values("순익", ascending=False).head(3)[["상품명", "순익"]].assign(순익=lambda x: x['순익'].apply(fmt)), use_container_width=True)
        
        c[2].write("📈 **효자상품 (수익률)**")
        c[2].dataframe(g.sort_values("수익률", ascending=False).head(3)[["상품명", "수익률"]].assign(수익률=lambda x: x['수익률'].astype(str) + "%"), use_container_width=True)
        
        c[3].write("📦 **인기상품 (수량)**")
        c[3].dataframe(g.sort_values("수량", ascending=False).head(3)[["상품명", "수량"]], use_container_width=True)
    else:
        st.info("데이터가 충분하지 않아 차트를 그릴 수 없습니다.")

# ==========================================
# 탭 4: 최종 경영 결산 (군더더기 이펙트 완전 배제)
# ==========================================
with tabs[3]:
    st.subheader(f"🏭 {selected_month}월 현금 흐름 결산")
    
    if not user_expenses.empty:
        curr_exp = user_expenses[user_expenses['월'] == selected_month]
    else:
        curr_exp = pd.DataFrame()
        
    if not curr_exp.empty:
        v = curr_exp.iloc[0]
    else:
        v = {"월세": 0, "추가인건비": 0, "공과금": 0, "세금": 0, "기타비용": 0}
        
    with st.expander(f"💸 {selected_month}월 외부 고정 지출 입력", expanded=True):
        with st.form("exp_form"):
            c1, c2, c3, c4, c5 = st.columns(5)
            r = c1.number_input("월세", value=int(v.get('월세',0)), step=10000)
            l = c2.number_input("인건비", value=int(v.get('추가인건비',0)), step=10000)
            t = c3.number_input("공과금", value=int(v.get('공과금',0)), step=10000)
            t2 = c4.number_input("세금", value=int(v.get('세금',0)), step=10000)
            e = c5.number_input("기타", value=int(v.get('기타비용',0)), step=10000)
            
            if st.form_submit_button("💾 지출 내역 확정", use_container_width=True):
                try:
                    supabase.table("expense_db").delete().eq("등록자", current_user).eq("월", selected_month).execute()
                    supabase.table("expense_db").insert({
                        "등록자": current_user, 
                        "월": selected_month, 
                        "월세": r, 
                        "추가인건비": l, 
                        "공과금": t, 
                        "세금": t2, 
                        "기타비용": e
                    }).execute()
                    st.cache_data.clear()
                    st.success(f"✅ {selected_month}월 지출이 저장되었습니다.")
                    st.rerun()
                except Exception: 
                    st.error("서버 지연 중입니다.")
                    
    total_e = r + l + t + t2 + e
    
    if not monthly_sales.empty:
        tr = pd.to_numeric(monthly_sales['총매출'], errors='coerce').fillna(0).sum()
        tn = pd.to_numeric(monthly_sales['순익'], errors='coerce').fillna(0).sum()
    else:
        tr = 0
        tn = 0
        
    final_cash = tn - total_e
    
    st.divider()
    st.write("### 🏁 최종 손익 대시보드")
    m = st.columns(5)
    m[0].metric("🎯 목표 (매출)", f"{fmt(st.session_state.targets['rev'])}원")
    m[1].metric("💰 총 매출액", f"{fmt(tr)}원")
    m[2].metric("📈 영업 순익 (공임 제외)", f"{fmt(tn)}원")
    m[3].metric("💸 외부 지출액", f"{fmt(total_e)}원")
    m[4].metric("✨ 통장 입금액 (찐수익)", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}" if final_cash > 0 else None)

# ==========================================
# 탭 5: 👑 마스터 관리
# ==========================================
if is_master:
    with tabs[4]:
        st.subheader("👑 최고 관리자 대시보드")
        st.write("### 👥 회원 계정 관리")
        try:
            manage_list = [u for u in df_users["아이디"].tolist() if u != MASTER_ID]
            if manage_list:
                su = st.selectbox("관리할 사장님 아이디 선택", manage_list)
                ur = df_users[df_users["아이디"] == su].iloc[0]
                
                c1, c2, c3 = st.columns(3)
                c1.info(f"아이디: {su} / 상태: {ur['상태']}")
                
                if ur['상태'] == "정상":
                    if c2.button("🚫 계정 정지", use_container_width=True):
                        supabase.table("user_db").update({"상태": "정지"}).eq("아이디", su).execute()
                        st.cache_data.clear()
                        st.rerun()
                else:
                    if c2.button("✅ 정지 해제", use_container_width=True):
                        supabase.table("user_db").update({"상태": "정상"}).eq("아이디", su).execute()
                        st.cache_data.clear()
                        st.rerun()
                        
                if c3.button("🔥 강제 탈퇴", use_container_width=True):
                    supabase.table("user_db").delete().eq("아이디", su).execute()
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.info("관리할 회원이 없습니다.")
        except Exception: 
            st.warning("회원 명부 로딩 중...")

        st.divider()
        st.write("### 🗄️ 데이터베이스 전수 조사")
        
        c = st.tabs(["📦 상품 장부", "🧾 매출 장부", "💸 지출 장부", "👥 회원 장부"])
        with c[0]: 
            st.dataframe(df_master.drop(columns=['id'], errors='ignore'), use_container_width=True)
        with c[1]: 
            st.dataframe(df_sales.drop(columns=['id'], errors='ignore'), use_container_width=True)
        with c[2]: 
            st.dataframe(df_expenses.drop(columns=['id'], errors='ignore'), use_container_width=True)
        with c[3]: 
            st.dataframe(df_users, use_container_width=True)
