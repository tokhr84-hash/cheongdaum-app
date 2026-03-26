import streamlit as st
import streamlit.components.v1 as components 
import pandas as pd
import numpy as np
import random
import urllib.parse
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import plotly.express as px
import requests

# 💡 클라우드 서버 시계를 한국 표준시(KST)로 영구 고정!
KST = timezone(timedelta(hours=9))

# ==========================================
# 👑 [0] 마스터 및 황금 열쇠(API/DB) 설정 구역 
# ==========================================
MASTER_ID = "[청다움]"
MASTER_PW = "150328"

SUPABASE_URL = "https://imgyafnhzrketbjfpxdt.supabase.co" 
SUPABASE_KEY = "sb_publishable_mXPEUz8UITZRpC9Q8d11og_2D1WQAYU"         

NAVER_CLIENT_ID = "IfR2VKsvWWc2ZLDivsbO"
NAVER_CLIENT_SECRET = "9TFmWDXh7w"
YOUTUBE_API_KEY = "AIzaSyD5Pn7AHtK48UagHMxNssdCXGg6BWLOSk8"
PUBLIC_DATA_KEY = "8224e0180b695871891f9b3d0299a94d5550d9cb156a6565df3f6bcc25d84a73"

# 💡 [V56.0 업데이트] 2026 실전 B2B 디저트 공방 핵심 키워드 
KEYWORD_LIST = [
    "버터떡 레시피", "두쫀쿠 유행", "속 채운 모찌", "글루텐프리 디저트", 
    "보자기 포장법", "답례품 패키징", "트루하트 선물포장", "아름드리 선물포장",
    "화과자 공방 창업", "상견례 답례품 추천", "디저트 팝업스토어", 
    "백화점 디저트 입점", "전통 디저트 현대화", 
    "디저트 공방 마케팅", "명절 선물 세트 구성", "개성주악 트렌드","앙금플라워",
    "앙금플라워쿠키","디저트 순위","급등 디저트"
]

# --- [1] 시스템 설정 및 화이트 라벨링 ---
st.set_page_config(
    page_title="청다움", 
    page_icon="🍡", 
    layout="wide"
)

# 📱 모바일 진짜 앱 강제 위장 코드 (PWA)
pwa_code = """
<script>
    const parentDoc = window.parent.document;
    parentDoc.title = '청다움';
    
    let appleTitle = parentDoc.querySelector('meta[name="apple-mobile-web-app-title"]');
    if (!appleTitle) {
        appleTitle = parentDoc.createElement('meta');
        appleTitle.name = "apple-mobile-web-app-title";
        parentDoc.head.appendChild(appleTitle);
    }
    appleTitle.content = "청다움";

    let appleCapable = parentDoc.querySelector('meta[name="apple-mobile-web-app-capable"]');
    if (!appleCapable) {
        appleCapable = parentDoc.createElement('meta');
        appleCapable.name = "apple-mobile-web-app-capable";
        parentDoc.head.appendChild(appleCapable);
    }
    appleCapable.content = "yes";

    let appleIcon = parentDoc.querySelector('link[rel="apple-touch-icon"]');
    if (!appleIcon) {
        appleIcon = parentDoc.createElement('link');
        appleIcon.rel = "apple-touch-icon";
        parentDoc.head.appendChild(appleIcon);
    }
    appleIcon.href = "https://여기에_추후_로고주소를_넣으세요.png";
</script>
"""
components.html(pwa_code, height=0, width=0)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden !important;}
.viewerBadge_container__1QSob {display: none !important;}
.viewerBadge_link__1S137 {display: none !important;}
[data-testid="stForm"] {margin-bottom: 2rem;}
.marquee-banner {
    background-color: #f0f6ff;
    padding: 10px;
    border-radius: 8px;
    border-left: 5px solid #4F8BF9;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
}
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
    st.error("데이터베이스 연결 오류입니다. URL과 KEY를 다시 확인해주세요.")
    st.stop()

@st.cache_data(ttl=5)
def load_all_data():
    u_res = supabase.table("user_db").select("*").execute()
    p_res = supabase.table("product_db").select("*").execute()
    s_res = supabase.table("sales_db").select("*").execute()
    e_res = supabase.table("expense_db").select("*").execute()
    q_res = supabase.table("quest_db").select("*").execute()
    l_res = supabase.table("link_db").select("*").execute()
    m_res = supabase.table("magazine_db").select("*").order("id", desc=True).execute()
    
    u_df = pd.DataFrame(u_res.data) if u_res.data else pd.DataFrame(columns=["아이디", "비밀번호", "상태"])
    p_df = pd.DataFrame(p_res.data) if p_res.data else pd.DataFrame(columns=["id", "등록자", "상품명", "원가", "마진", "권장가", "소요시간", "공임비"])
    s_df = pd.DataFrame(s_res.data) if s_res.data else pd.DataFrame(columns=["id", "등록자", "날짜", "월", "경로", "상품명", "판매가", "수량", "총매출", "순익"])
    e_df = pd.DataFrame(e_res.data) if e_res.data else pd.DataFrame(columns=["id", "등록자", "월", "월세", "추가인건비", "공과금", "세금", "기타비용"])
    q_df = pd.DataFrame(q_res.data) if q_res.data else pd.DataFrame(columns=["등록자", "step1", "step2", "step3", "step4", "step5", "step6", "step7", "step8"])
    l_df = pd.DataFrame(l_res.data) if l_res.data else pd.DataFrame(columns=["id", "제보자", "업체명", "링크", "추천이유", "상태"])
    m_df = pd.DataFrame(m_res.data) if m_res.data else pd.DataFrame(columns=["id", "제목", "내용", "작성일"])
    
    return u_df, p_df, s_df, e_df, q_df, l_df, m_df

try:
    df_users, df_master, df_sales, df_expenses, df_quest, df_link, df_magazine = load_all_data()
    
    if df_users.empty or MASTER_ID not in df_users['아이디'].values:
        supabase.table("user_db").insert({
            "아이디": MASTER_ID, 
            "비밀번호": MASTER_PW, 
            "상태": "정상"
        }).execute()
        st.cache_data.clear()
        
except Exception as e:
    st.error("장부를 불러오는 데 실패했습니다. 서버 상태를 확인해주세요.")
    st.stop()

# --- [3] 로그인 및 회원가입 로직 (VIP 마스터 승인 시스템 유지) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🍡 청다움 경영 관리 플랫폼 (VIP)</h1>", unsafe_allow_html=True)
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
                    if not match.empty:
                        user_status = match.iloc[0]["상태"]
                        if user_status == "정상":
                            st.session_state.logged_in = True
                            st.session_state.current_user = u_id_str
                            st.rerun()
                        elif user_status == "대기":
                            st.warning("⏳ 마스터의 가입 승인을 기다리고 있습니다. 승인 후 다시 시도해 주세요!")
                        else: 
                            st.error("🚫 이용이 정지된 계정입니다.")
                    else:
                        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                    
    with sign_tab:
        with st.form("signup_form"):
            new_id = st.text_input("새로운 아이디(ID)")
            new_pw = st.text_input("새로운 비밀번호(PW)", type="password")
            new_pw_check = st.text_input("비밀번호 확인", type="password")
            
            if st.form_submit_button("가입 신청하기", use_container_width=True):
                nid_str = str(new_id).strip()
                npw_str = str(new_pw).strip()
                
                if nid_str in df_users["아이디"].values or nid_str == MASTER_ID: 
                    st.warning("이미 존재하는 아이디입니다.")
                elif npw_str != str(new_pw_check).strip(): 
                    st.warning("비밀번호가 일치하지 않습니다.")
                elif len(nid_str) < 2: 
                    st.warning("아이디를 2자 이상 입력해 주세요.")
                else:
                    supabase.table("user_db").insert({
                        "아이디": nid_str, 
                        "비밀번호": npw_str, 
                        "상태": "대기"
                    }).execute()
                    
                    supabase.table("quest_db").insert({
                        "등록자": nid_str
                    }).execute()
                    
                    st.cache_data.clear()
                    st.success(f"🎉 가입 신청 완료! 마스터의 승인 후 '{nid_str}' 계정으로 로그인 가능합니다.")
    st.stop()

# --- [4] 개인별 데이터 연동 및 필터링 ---
current_user = st.session_state.current_user
is_master = (current_user == MASTER_ID)
legacy_ids = ["[청다움]", "cheongdaum"]

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
    curr_m = datetime.now(KST).strftime('%Y-%m') 
    if curr_m not in month_list: 
        month_list.insert(0, curr_m)
else: 
    month_list = [datetime.now(KST).strftime('%Y-%m')]

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
    hourly_wage = st.number_input("나의 시간당 공임(원)", value=0, step=1000) 
    
    st.divider()
    
    st.subheader("📅 스케줄 및 발주 관리")
    selected_date = st.date_input("날짜를 선택하세요", datetime.now(KST).date())
    
    if 'memo' not in st.session_state: 
        st.session_state.memo = ""
        
    st.session_state.memo = st.text_area(
        "오늘의 메모 / 할 일 (자유롭게 적으세요)", 
        value=st.session_state.memo, 
        height=300, 
        placeholder="예시:\n- 백앙금 10kg 발주하기\n- 오후 2시 답례품 50구 픽업\n- 보자기 포장재 재고 확인"
    )
    
    st.divider()
    
    st.title("🧮 빠른 계산기")
    if 'calc_val' not in st.session_state: 
        st.session_state['calc_val'] = ""
        
    st.code(st.session_state['calc_val'] if st.session_state['calc_val'] else "0", language="text")
    
    calc_rows = [
        ['7', '8', '9', '/'], 
        ['4', '5', '6', '*'], 
        ['1', '2', '3', '-'], 
        ['C', '0', '=', '+']
    ]
    
    for row in calc_rows:
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

latest_news = df_magazine.iloc[0]['제목'] if not df_magazine.empty else "청다움 라운지에 새로운 디저트 트렌드가 업데이트되었습니다!"
st.markdown(f"""
<div class="marquee-banner">
    <marquee scrollamount="8">📣 [오늘의 청다움 라운지] {latest_news} ➡️ 5번 탭 '청다움 라운지'에서 확인하세요!</marquee>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([3, 1])
with c2: 
    selected_month = st.selectbox("📅 장부 조회 월(Month)", month_list)

monthly_sales = user_sales[user_sales['월'] == selected_month] if not user_sales.empty else pd.DataFrame()

tab_names = ["📊 상품 정보 등록", "📈 실전 매출 입력", "🏆 성과 시각화", "🏭 경영 결산", "🎓 청다움 라운지", "🚀 창업 퀘스트"]
if is_master: 
    tab_names.append("👑 마스터 관리")
    
tabs = st.tabs(tab_names)

# ==========================================
# 탭 1: 상품 정보 등록
# ==========================================
with tabs[0]:
    with st.expander("📍 신규 상품 영구 등록 (스마트 원가 계산기)", expanded=True):
        with st.form("v55_reg_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            p_name = col1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
            target_m = col2.number_input("🎯 목표 마진", value=0.4, step=0.1)
            make_time = col3.number_input("⏱️ 제작 소요시간(분)", value=30, step=5)
            
            st.write("🌿 **1. [원재료] 투입량 입력**")
            bom_recipe_init = pd.DataFrame([{"항목": "백앙금", "총용량(g,ml)": 5000, "총가격(원)": 15000, "레시피 투입량(g,ml)": 300}])
            bom_recipe = st.data_editor(bom_recipe_init, num_rows="dynamic", use_container_width=True, key="bom_r")
            
            st.write("🎀 **2. [부자재] 단품 입력**")
            bom_sub_init = pd.DataFrame([{"항목": "화과자 6구 케이스", "수량(개)": 1, "단가(원)": 800}])
            bom_sub = st.data_editor(bom_sub_init, num_rows="dynamic", use_container_width=True, key="bom_s")
            
            if st.form_submit_button("💾 자동 계산 및 중앙 DB 영구 저장", use_container_width=True):
                if p_name:
                    rc = pd.to_numeric(bom_recipe["총가격(원)"], errors='coerce').fillna(0)
                    rv = pd.to_numeric(bom_recipe["총용량(g,ml)"], errors='coerce').replace(0, 1)
                    rt = pd.to_numeric(bom_recipe["레시피 투입량(g,ml)"], errors='coerce').fillna(0)
                    recipe_cost = (rc / rv) * rt
                    
                    sq = pd.to_numeric(bom_sub["수량(개)"], errors='coerce').fillna(0)
                    sp = pd.to_numeric(bom_sub["단가(원)"], errors='coerce').fillna(0)
                    sub_cost = sq * sp
                    
                    cost = float(recipe_cost.sum() + sub_cost.sum())
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
                        st.success(f"🎉 '{p_name}' 저장 완료! (원가: {fmt(cost)}원)")
                        st.rerun()
                    except Exception as e: 
                        st.error("저장 오류 (상품명이 이미 존재하거나 DB 연결 오류입니다.)")

    st.divider()
    
    if not df_p.empty:
        st.write("📋 내 계정에 등록된 상품 목록")
        del_p = st.selectbox("삭제할 상품을 선택하세요", df_p["상품명"].dropna().tolist())
        
        if st.button("❌ 선택 상품 영구 삭제", use_container_width=True):
            supabase.table("product_db").delete().eq("등록자", current_user).eq("상품명", del_p).execute()
            st.cache_data.clear()
            st.rerun()
            
        disp = df_p.copy().drop(columns=['id', '등록자'], errors='ignore')
        for col in ["원가", "권장가", "공임비"]:
            if col in disp.columns: 
                disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, hide_index=True, use_container_width=True)

# ==========================================
# 탭 2: 실전 매출 입력 
# ==========================================
with tabs[1]:
    st.subheader("⚡ 매출 입력 패널")
    if not df_p.empty:
        with st.container():
            col_a, col_b = st.columns([1, 1])
            s_date = col_a.date_input("판매 날짜", datetime.now(KST).date()) 
            inb = col_b.selectbox("유입 경로", ["인스타그램", "네이버예약", "지인소개", "워크인", "기타"])
            
            sel_p = st.selectbox("판매된 상품 선택", df_p["상품명"].tolist())
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
                    st.success("✅ 매출이 정상적으로 등록되었습니다!")
                    st.rerun()
                except Exception: 
                    st.error("매출 기록 중 오류가 발생했습니다.")
    
    st.divider()
    
    st.markdown("### 🚩 이번 달 목표 세팅")
    t1, t2 = st.columns(2)
    st.session_state.targets['rev'] = t1.number_input("목표 총 매출액", value=st.session_state.targets['rev'])
    st.session_state.targets['net'] = t2.number_input("목표 영업 순수익", value=st.session_state.targets['net'])

    if not monthly_sales.empty:
        st.write(f"### 📑 {selected_month}월 상세 매출 장부")
        
        with st.expander("🗑️ 매출 기록 삭제 (오입력 수정)"):
            opt = {f"[{r['날짜']}] {r['상품명']} ({fmt(r['총매출'])}원)": r['id'] for i, r in monthly_sales.iterrows()}
            sel_del = st.selectbox("삭제할 항목을 선택하세요", list(opt.keys()))
            
            if st.button("❌ 선택 기록 완전 삭제", use_container_width=True):
                supabase.table("sales_db").delete().eq("id", int(opt[sel_del])).execute()
                st.cache_data.clear()
                st.rerun()
                
        ds = monthly_sales.copy()
        for c in ["판매가", "총매출", "순익"]: 
            ds[c] = pd.to_numeric(ds[c], errors='coerce').fillna(0)
            
        ds['수익률'] = (ds['순익'] / ds['총매출'] * 100).fillna(0).round(1).astype(str) + "%"
        
        for c in ["판매가", "총매출", "순익"]: 
            ds[c] = ds[c].apply(lambda x: f"{fmt(x)}원")
            
        st.dataframe(ds.drop(columns=['id', '등록자', '월'], errors='ignore'), hide_index=True, use_container_width=True)
        
        tr_tab2 = pd.to_numeric(monthly_sales['총매출'], errors='coerce').fillna(0).sum()
        tn_tab2 = pd.to_numeric(monthly_sales['순익'], errors='coerce').fillna(0).sum()
        
        st.divider()
        m_c1, m_c2 = st.columns(2)
        m_c1.metric("💰 총 매출액", f"{fmt(tr_tab2)}원", f"{fmt(tr_tab2 - st.session_state.targets['rev'])}원")
        m_c2.metric("📈 영업 순이익", f"{fmt(tn_tab2)}원", f"{fmt(tn_tab2 - st.session_state.targets['net'])}원")

# ==========================================
# 탭 3: 성과 시각화 
# ==========================================
with tabs[2]:
    st.subheader(f"🏆 {selected_month}월 심층 데이터 시각화")
    
    if not monthly_sales.empty:
        an = monthly_sales.copy()
        for col in ["수량", "총매출", "순익"]: 
            an[col] = pd.to_numeric(an[col], errors='coerce').fillna(0)
            
        c_chart1, c_chart2 = st.columns(2)
        path_data = an.groupby("경로")["총매출"].sum().reset_index()
        fig1 = px.pie(path_data, values='총매출', names='경로', hole=0.4, title="📍 유입 경로별 매출 비중")
        c_chart1.plotly_chart(fig1, use_container_width=True)
        
        prod_data = an.groupby("상품명")["총매출"].sum().reset_index().sort_values("총매출", ascending=True)
        fig2 = px.bar(prod_data, x='총매출', y='상품명', color='상품명', orientation='h', title="🏆 상품별 매출 순위", text_auto='.2s')
        c_chart2.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        g = an.groupby("상품명")[["수량", "총매출", "순익"]].sum().reset_index()
        g["수익률"] = (g["순익"] / g["총매출"] * 100).round(1)
        
        cr = st.columns(4)
        cr[0].write("📊 **매출 Top 3**")
        cr[0].dataframe(g.sort_values("총매출", ascending=False).head(3)[["상품명", "총매출"]].assign(총매출=lambda x: x['총매출'].apply(fmt)), hide_index=True, use_container_width=True)
        
        cr[1].write("💰 **순익 Top 3**")
        cr[1].dataframe(g.sort_values("순익", ascending=False).head(3)[["상품명", "순익"]].assign(순익=lambda x: x['순익'].apply(fmt)), hide_index=True, use_container_width=True)
        
        cr[2].write("📈 **효자상품 (수익률)**")
        cr[2].dataframe(g.sort_values("수익률", ascending=False).head(3)[["상품명", "수익률"]].assign(수익률=lambda x: x['수익률'].astype(str) + "%"), hide_index=True, use_container_width=True)
        
        cr[3].write("📦 **인기상품 (수량)**")
        cr[3].dataframe(g.sort_values("수량", ascending=False).head(3)[["상품명", "수량"]], hide_index=True, use_container_width=True)
        
    try: 
        st.divider()
        st.markdown("<h3 style='text-align: center; color: #4F8BF9;'>📣 청다움의 따뜻한 조언</h3>", unsafe_allow_html=True)
        c_img1, c_img2, c_img3 = st.columns([1, 2, 1])
        with c_img2: 
            st.image("청다움 멘트.png", use_container_width=True)
    except: 
        pass

# ==========================================
# 탭 4: 최종 경영 결산 
# ==========================================
with tabs[3]:
    st.subheader(f"🏭 {selected_month}월 현금 흐름 결산")
    curr_exp = user_expenses[user_expenses['월'] == selected_month] if not user_expenses.empty else pd.DataFrame()
    v = curr_exp.iloc[0] if not curr_exp.empty else {"월세": 0, "추가인건비": 0, "공과금": 0, "세금": 0, "기타비용": 0}
        
    with st.expander(f"💸 {selected_month}월 외부 고정 지출 입력", expanded=True):
        with st.form("exp_form"):
            c1, c2, c3, c4, c5 = st.columns(5)
            r = c1.number_input("월세", value=int(v.get('월세',0)), step=10000)
            l = c2.number_input("인건비", value=int(v.get('추가인건비',0)), step=10000)
            t = c3.number_input("공과금", value=int(v.get('공과금',0)), step=10000)
            t2 = c4.number_input("세금", value=int(v.get('세금',0)), step=10000)
            e = c5.number_input("기타", value=int(v.get('기타비용',0)), step=10000)
            
            if st.form_submit_button("💾 지출 내역 확정", use_container_width=True):
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
                st.rerun()
                    
    total_e = r + l + t + t2 + e
    tr = pd.to_numeric(monthly_sales['총매출'], errors='coerce').fillna(0).sum() if not monthly_sales.empty else 0
    tn = pd.to_numeric(monthly_sales['순익'], errors='coerce').fillna(0).sum() if not monthly_sales.empty else 0
    final_cash = tn - total_e
    
    st.divider()
    st.write("### 🏁 최종 손익 대시보드")
    m = st.columns(5)
    m[0].metric("🎯 목표 (매출)", f"{fmt(st.session_state.targets['rev'])}원")
    m[1].metric("💰 총 매출액", f"{fmt(tr)}원")
    m[2].metric("📈 영업 순익", f"{fmt(tn)}원")
    m[3].metric("💸 지출액", f"{fmt(total_e)}원")
    m[4].metric("✨ 통장 입금액", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}" if final_cash > 0 else None)

# ==========================================
# 탭 5: 🎓 청다움 라운지 
# ==========================================
with tabs[4]:
    st.markdown("### 👑 VIP 글로벌 트렌드 데이터베이스")
    st.caption("대한민국 상위 1% 디저트 CEO를 위한 국내외 1티어 B2B 정보망입니다. 버튼을 누르면 즉시 연결됩니다.")
    
    st.write("##### 🌍 글로벌 & 산업 통계망")
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
    col_btn1.link_button("🇺🇸 Pastry Arts Magazine", "https://pastryartsmag.com/", use_container_width=True)
    col_btn2.link_button("💡 Mintel 글로벌 트렌드", "https://www.mintel.com/", use_container_width=True)
    col_btn3.link_button("📊 FIS 식품산업통계", "https://www.atfis.or.kr/", use_container_width=True)
    col_btn4.link_button("🌍 KATI 농식품수출정보", "https://www.kati.net/", use_container_width=True)
    
    st.write("##### 🇯🇵 일본 화과자 & 디저트 정밀 타격망")
    col_j1, col_j2, col_j3 = st.columns(3)
    col_j1.link_button("🍡 일본 전국화과자협회", "https://www.wagashi.or.jp/", use_container_width=True)
    col_j2.link_button("📖 월간 제과제빵 (B2B)", "https://www.seikaseipan.com/", use_container_width=True)
    col_j3.link_button("⚡ PR TIMES (일본 실시간 신상)", "https://prtimes.jp/category/sweets", use_container_width=True)
    
    st.divider()

    st.markdown("### 📰 청다움 트렌드 매거진 (AI 자동 수집)")
    st.caption("마스터 로봇이 B2B 전문지(식품외식경제, 파티시에 등)에서만 엄선하여 매일 긁어오는 핵심 브리핑입니다.")
    
    if not df_magazine.empty:
        for idx, row in df_magazine.iterrows():
            with st.expander(f"📌 [{row['작성일']}] {row['제목']}", expanded=(idx==0)):
                st.write(row['내용'])
    else: 
        st.info("아직 발행된 매거진이 없습니다.")
    
    st.divider()
    
    st.markdown("### 🤝 사장님들의 비밀 창고 (도매처)")
    approved_links = df_link[df_link['상태'] == '승인']
    
    if not approved_links.empty:
        disp_links = approved_links[['업체명', '추천이유', '링크']].copy()
        st.dataframe(
            disp_links, 
            column_config={
                "링크": st.column_config.LinkColumn("사이트 (클릭하여 이동)")
            }, 
            hide_index=True, 
            use_container_width=True
        )
    else: 
        st.info("승인된 도매처가 없습니다.")
        
    with st.expander("✨ 나만의 꿀 거래처 제보하기"):
        with st.form("link_form"):
            st.caption("사장님만 알고 있는 꿀 거래처 정보를 상세히 적어주세요!")
            col_l1, col_l2 = st.columns(2)
            l_name = col_l1.text_input("상호명 (필수)", placeholder="예: 새로피앤엘")
            l_phone = col_l2.text_input("전화번호", placeholder="예: 1899-0715")
            l_addr = st.text_input("주소", placeholder="예: 서울 중구 동호로 379")
            l_url = st.text_input("사이트 (URL 필수)", placeholder="https://www.saeropnl.com")
            l_reason = st.text_input("추천 이유", placeholder="방산시장에서 가장 큰 규모의 패키지 매장 중 하나로...")
            
            if st.form_submit_button("제보하기", use_container_width=True):
                if l_name and l_url:
                    combined_name = f"{l_name} (☎ {l_phone if l_phone else '없음'} / 📍 {l_addr if l_addr else '미기재'})"
                    supabase.table("link_db").insert({
                        "제보자": current_user, 
                        "업체명": combined_name, 
                        "링크": l_url, 
                        "추천이유": l_reason, 
                        "상태": "대기"
                    }).execute()
                    st.cache_data.clear()
                    st.success("제보 완료! 마스터 승인 후 노출됩니다.")
                else:
                    st.error("상호명과 사이트(URL)는 필수 입력 사항입니다.")

# ==========================================
# 탭 6: 🚀 창업 퀘스트 
# ==========================================
with tabs[5]:
    st.markdown("### 💰 청다움 창업 계산기")
    with st.container(border=True):
        budget = st.number_input("💵 1. 초기 예산", value=0, step=1000000)
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        dep = col_c1.number_input("보증금", value=0, step=1000000)
        rent = col_c2.number_input("월세(6개월치)", value=0, step=100000)
        interior = col_c3.number_input("인테리어 비용", value=0, step=1000000)
        misc = col_c4.number_input("집기/기타", value=0, step=1000000)
        
        reserve = budget - (dep + rent + interior + misc)
        st.metric("✨ 3. 최종 여유 자금", f"{fmt(reserve)}원")
            
    st.divider()
    
    st.markdown("### 🚀 창업 8단계 퀘스트")
    user_quest = df_quest[df_quest['등록자'] == current_user]
    
    if user_quest.empty:
        supabase.table("quest_db").insert({"등록자": current_user}).execute()
        st.cache_data.clear()
        st.rerun()
    else:
        uq = user_quest.iloc[0]
        quest_status = [
            uq.get('step1', False), uq.get('step2', False), uq.get('step3', False), uq.get('step4', False),
            uq.get('step5', False), uq.get('step6', False), uq.get('step7', False), uq.get('step8', False)
        ]
        progress_pct = sum(quest_status) / 8.0
        
        st.progress(progress_pct)
        st.write(f"**현재 창업 준비 {int(progress_pct * 100)}% 완료!**")
        
        with st.form("quest_form"):
            s1 = st.checkbox("1단계: 보건증(건강진단결과서) 발급", value=bool(uq.get('step1', False)))
            st.caption("💡 노하우: 신분증을 챙겨 보건소에 방문하세요! 검사 후 발급까지 주말 제외 약 5일이 소요되니 매장 계약 직후 1순위로 움직이셔야 합니다.")
            
            s2 = st.checkbox("2단계: 식품위생교육 수료", value=bool(uq.get('step2', False)))
            st.markdown("<p style='font-size: 0.8em; color: gray;'>💡 노하우: 한국휴게음식업중앙회에서 이수 가능합니다. <span style='color: red; font-weight: bold;'>(주의: 신규 창업자는 온라인 교육이 불가하고 오프라인 집합 교육만 가능할 수 있으니 반드시 사전에 관할 기관에 확인하세요!)</span></p>", unsafe_allow_html=True)
            
            s3 = st.checkbox("3단계: 영업신고증 발급", value=bool(uq.get('step3', False)))
            st.caption("💡 노하우: 확정일자를 받은 임대차계약서, 보건증, 위생교육수료증, 신분증을 챙겨 관할 구청 위생과에 방문하세요. 면허세 납부 후 즉시 발급됩니다.")
            
            s4 = st.checkbox("4단계: 사업자등록 및 사업자 통장 개설", value=bool(uq.get('step4', False)))
            st.caption("💡 노하우: 구청에서 영업신고증을 받자마자 세무서로 가서 사업자등록을 하시고, 곧바로 은행에 들러 사업자 전용 통장과 카드를 개설하세요! 개인 가계부와 섞이면 세금 신고 때 큰일 납니다.")
            
            s5 = st.checkbox("5단계: 필수 집기 세팅 및 인테리어 마감", value=bool(uq.get('step5', False)))
            st.caption("💡 노하우: 오븐, 찜기, 냉장고 등 핵심 기기의 전력량을 반드시 확인하여 승압 공사 여부를 결정하세요. 작업대의 높이와 동선은 사장님의 손목/허리 피로도를 좌우합니다.")
            
            s6 = st.checkbox("6단계: 부자재 및 초도 물량 확보", value=bool(uq.get('step6', False)))
            st.caption("💡 노하우: 포장 상자, 쇼핑백, 스티커 등은 배송 기간을 고려하여 넉넉히 미리 발주하세요. 단, 첫 초도 물량은 너무 많이 잡지 말고 반응을 보며 늘려가는 것이 안전합니다.")
            
            s7 = st.checkbox("7단계: SNS 계정 개설 및 기록 시작", value=bool(uq.get('step7', False)))
            st.caption("💡 노하우: 빈 매장에 페인트칠을 하고 간판을 다는 모든 오픈 준비 과정을 피드에 기록하세요. 고객은 완제품뿐만 아니라 사장님의 땀방울과 스토리에 지갑을 엽니다.")
            
            s8 = st.checkbox("8단계: 통신판매업 신고 및 온라인 판매 준비", value=bool(uq.get('step8', False)))
            st.caption("💡 노하우: 택배 배송을 통한 전국 판매를 기획 중이라면 통신판매업 신고가 필수입니다. 아이디어스나 스마트스토어 등은 입점 심사 기간이 있으니 미리 가입해두세요.")
            
            if st.form_submit_button("✅ 진행 상황 영구 저장", use_container_width=True):
                supabase.table("quest_db").update({
                    "step1": s1, 
                    "step2": s2, 
                    "step3": s3, 
                    "step4": s4, 
                    "step5": s5, 
                    "step6": s6, 
                    "step7": s7, 
                    "step8": s8
                }).eq("등록자", current_user).execute()
                st.cache_data.clear()
                st.rerun()

    st.divider()
    
    st.markdown("### 🏢 전국 소상공인 지원금 실시간 레이더")
    loc_sel = st.selectbox("조회할 지역", ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"])
    
    if st.button(f"🔍 {loc_sel} 지역 지원금 사냥", use_container_width=True):
        if PUBLIC_DATA_KEY == "여기에_공공데이터_인증키(Encoding)를_넣으세요": 
            st.warning("⚠️ 공공데이터 API 인증키가 입력되지 않았습니다.")
        else:
            with st.spinner("정부 서버에서 실시간 공고를 긁어오고 있습니다..."):
                try:
                    decoded_key = urllib.parse.unquote(PUBLIC_DATA_KEY)
                    url = "http://apis.data.go.kr/B552735/dgSstIdvSupportService/getDgSstIdvSupportList"
                    params = {
                        "serviceKey": decoded_key, 
                        "type": "json", 
                        "numOfRows": 15, 
                        "pageNo": 1, 
                        "areaNm": loc_sel
                    }
                    res = requests.get(url, params=params, timeout=5)
                    
                    try:
                        data = res.json()
                        items = data.get('response', {}).get('body', {}).get('items', [])
                        if items: 
                            st.success(f"🎉 성공! 총 {len(items)}건의 최신 공고를 발견했습니다!")
                            st.dataframe(pd.DataFrame(items)[['title', 'registDate', 'pblancUrl']], hide_index=True, use_container_width=True)
                        else: 
                            st.info("현재 해당 지역에 진행 중인 공고가 없습니다.")
                    except:
                        st.warning("⚠️ 정부 서버 통신 오류 (또는 API 키 미승인 상태) - 화면 디자인 확인용 가짜(Mock) 데이터를 표시합니다.")
                        mock_data = [
                            {"공고명": f"[{loc_sel}] 2026년 소상공인 경영환경개선 지원사업", "등록일": datetime.now(KST).strftime("%Y-%m-%d"), "링크": "https://www.bizinfo.go.kr"},
                            {"공고명": f"[{loc_sel}] 창업기업 마케팅 지원금(최대 300만원)", "등록일": (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d"), "링크": "https://www.bizinfo.go.kr"},
                            {"공고명": f"[{loc_sel}] 청년 사장님 월세 지원 및 대출 이자 보전", "등록일": (datetime.now(KST) - timedelta(days=2)).strftime("%Y-%m-%d"), "링크": "https://www.bizinfo.go.kr"}
                        ]
                        st.dataframe(
                            pd.DataFrame(mock_data), 
                            column_config={"링크": st.column_config.LinkColumn("사이트 이동")}, 
                            hide_index=True, 
                            use_container_width=True
                        )
                except Exception as e: 
                    st.error(f"정부 서버와의 연결이 완전히 끊어졌습니다. (에러: {e})")

# ==========================================
# 탭 7: 👑 마스터 관리 
# ==========================================
if is_master:
    with tabs[6]:
        st.subheader("👑 최고 관리자 대시보드 및 API 통제실")
        
        st.write("### 🤖 청다움 전용 매거진 3단 자동 발행 로봇 (B2B 모드)")
        st.caption("국내 최고 권위의 B2B 매거진과 논-먹방 유튜브 채널만 저격합니다.")
        
        if st.button("🚀 최상위 트렌드(3개 주제) 사냥 및 발행", use_container_width=True):
            if NAVER_CLIENT_ID == "여기에_네이버_Client_ID를_넣으세요":
                st.error("API 키를 입력해주세요!")
            else:
                with st.spinner("로봇이 전문 매체 기사 2개, 비즈니스 유튜브 1개 주제를 사냥 중입니다..."):
                    today_str = datetime.now(KST).strftime("%Y-%m-%d")
                    k1, k2, k3 = random.sample(KEYWORD_LIST, 3)
                    
                    try:
                        smart_query1 = f"{k1} 식품외식경제|파티시에|베이커리|배민트렌드|트렌드|비즈니스"
                        n_res1 = requests.get(
                            "https://openapi.naver.com/v1/search/news.json", 
                            headers={"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}, 
                            params={"query": smart_query1, "display": 3}
                        ).json()
                        items1 = n_res1.get('items', [])
                        news_txt1 = "\n".join([f"- [{i['title'].replace('<b>','').replace('</b>','').replace('&quot;','')}]( {i['link']} )" for i in items1]) if items1 else "- 🔍 관련된 최신 B2B 기사가 없습니다. 내일 다시 시도해 주세요."
                    except: 
                        news_txt1 = "- 수집 실패"

                    try:
                        smart_query2 = f"{k2} 식품외식경제|파티시에|베이커리|시장|매출|노하우"
                        n_res2 = requests.get(
                            "https://openapi.naver.com/v1/search/news.json", 
                            headers={"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}, 
                            params={"query": smart_query2, "display": 3}
                        ).json()
                        items2 = n_res2.get('items', [])
                        news_txt2 = "\n".join([f"- [{i['title'].replace('<b>','').replace('</b>','').replace('&quot;','')}]( {i['link']} )" for i in items2]) if items2 else "- 🔍 관련된 최신 B2B 기사가 없습니다. 내일 다시 시도해 주세요."
                    except: 
                        news_txt2 = "- 수집 실패"

                    try:
                        smart_yt_query = f"{k3} 노하우|창업|만들기|포장 -먹방 -ASMR -vlog -브이로그"
                        y_res = requests.get(
                            "https://www.googleapis.com/youtube/v3/search", 
                            params={"part": "snippet", "q": smart_yt_query, "type": "video", "maxResults": 3, "key": YOUTUBE_API_KEY}
                        ).json()
                        items_yt = y_res.get('items', [])
                        yt_txt = "\n".join([f"- 📺 [{i['snippet']['title'].replace('&quot;','').replace('&#39;','') }](https://www.youtube.com/watch?v={i['id']['videoId']})" for i in items_yt]) if items_yt else "- 🔍 해당되는 전문 영상이 없습니다."
                    except: 
                        yt_txt = "- 수집 실패"
                    
                    m_title = f"🌸 {today_str} 청다움 인사이트: [{k1}], [{k2}], [{k3}]"
                    m_content = f"""
안녕하세요, 사장님! **[청다움 B2B 라운지]**입니다. 🍡
상위 1% 전문 매체에서 추출한 오늘의 핵심 트렌드 3가지를 전해드립니다.

### 📰 비즈니스 트렌드: {k1}
{news_txt1}

### 📰 시장 및 노하우: {k2}
{news_txt2}

### 🎥 전문 노하우 영상: {k3}
{yt_txt}

---
💡 **청다움의 따뜻한 조언**
"유행은 빠르게 변하지만, 사장님의 정성은 변하지 않습니다."
"""
                    supabase.table("magazine_db").insert({
                        "제목": m_title, 
                        "내용": m_content.strip(), 
                        "작성일": today_str
                    }).execute()
                    st.cache_data.clear()
                    st.success("🎉 작전 성공! 전광판을 확인하세요.")
                    st.rerun()

        st.divider()
        
        # 💡 [V56.3 신규 탑재] 발행된 매거진 삭제 (QA 권한)
        st.write("### 🗑️ 발행된 매거진 영구 삭제")
        st.caption("마음에 들지 않거나 오류가 난 과거 매거진을 삭제할 수 있습니다.")
        
        if not df_magazine.empty:
            with st.form("delete_mag_form"):
                # 매거진 목록을 딕셔너리로 만듭니다 (표시용 이름: 실제 ID)
                mag_options = {f"[{r['작성일']}] {r['제목']}": r['id'] for i, r in df_magazine.iterrows()}
                mag_to_del = st.selectbox("삭제할 매거진을 선택하세요", list(mag_options.keys()))
                
                if st.form_submit_button("❌ 선택 매거진 영구 삭제", use_container_width=True):
                    target_mag_id = mag_options[mag_to_del]
                    supabase.table("magazine_db").delete().eq("id", target_mag_id).execute()
                    st.cache_data.clear()
                    st.success("🗑️ 선택하신 매거진이 영구 삭제되었습니다!")
                    st.rerun()
        else:
            st.info("현재 삭제할 매거진이 없습니다.")

        st.divider()
        
        st.write("### 🤝 도매처 제보 승인 관리")
        pending_links = df_link[df_link['상태'] == '대기']
        
        if not pending_links.empty:
            st.dataframe(pending_links[['id', '제보자', '업체명', '링크', '추천이유']], hide_index=True, use_container_width=True)
            with st.form("approve_form"):
                target_id = st.number_input("승인/반려할 ID 번호를 입력하세요", min_value=0, step=1)
                c_btn1, c_btn2 = st.columns(2)
                
                if c_btn1.form_submit_button("✅ 노출 승인 (라운지로 송출)", use_container_width=True):
                    supabase.table("link_db").update({"상태": "승인"}).eq("id", target_id).execute()
                    st.cache_data.clear()
                    st.rerun()
                    
                if c_btn2.form_submit_button("❌ 영구 삭제 (반려)", use_container_width=True):
                    supabase.table("link_db").delete().eq("id", target_id).execute()
                    st.cache_data.clear()
                    st.rerun()
        else: 
            st.info("현재 대기 중인 제보가 없습니다.")

        st.divider()
        
        st.write("### 👥 회원 명부 관리 (가입 승인)")
        
        pending_users = df_users[df_users['상태'] == '대기']
        if not pending_users.empty:
            st.warning(f"🚨 승인 대기 중인 신규 가입자가 {len(pending_users)}명 있습니다! 권한을 부여해 주세요.")
            
        st.dataframe(df_users, hide_index=True, use_container_width=True)
        
        with st.form("u_man"):
            tid = st.text_input("상태를 변경할 아이디를 입력하세요")
            act = st.selectbox("작업 선택", ["정상 (승인/복구)", "대기 (보류)", "정지 (차단)", "삭제 (영구제거)"])
            
            if st.form_submit_button("실행"):
                if "삭제" in act: 
                    supabase.table("user_db").delete().eq("아이디", tid).execute()
                else: 
                    new_status = act.split(" ")[0] 
                    supabase.table("user_db").update({"상태": new_status}).eq("아이디", tid).execute()
                st.cache_data.clear()
                st.rerun()
