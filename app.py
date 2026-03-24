import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px
import requests  # API 통신을 위한 필수 부품

# ==========================================
# 👑 [0] 마스터 및 황금 열쇠(API/DB) 설정 구역
# ==========================================
MASTER_ID = "[청다움]"
MASTER_PW = "150328"

# 1. 수파베이스(DB) 연결 키
SUPABASE_URL = "https://imgyafnhzrketbjfpxdt.supabase.co" 
SUPABASE_KEY = "여기에_anon_API_Key를_붙여넣으세요"         

# 2. 외부 데이터 사냥용 3대 API 키 (사전작업 3)
PUBLIC_DATA_KEY = "여기에_공공데이터_일반인증키(Encoding)를_넣으세요"
YOUTUBE_API_KEY = "여기에_유튜브_API키(AIza...)를_넣으세요"
NAVER_CLIENT_ID = "여기에_네이버_Client_ID를_넣으세요"
NAVER_CLIENT_SECRET = "여기에_네이버_Client_Secret을_넣으세요"

# --- [1] 시스템 설정 및 화이트 라벨링 ---
st.set_page_config(page_title="청다움 마스터 V41.0", page_icon="🍡", layout="wide")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden !important;}
.viewerBadge_container__1QSob {display: none !important;}
.viewerBadge_link__1S137 {display: none !important;}
[data-testid="stForm"] {margin-bottom: 2rem;}
/* 전광판 배너 디자인 */
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
        if pd.isna(val) or val == "": return "0"
        return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

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
        supabase.table("user_db").insert({"아이디": MASTER_ID, "비밀번호": MASTER_PW, "상태": "정상"}).execute()
        st.cache_data.clear()
except Exception as e:
    st.error("장부를 불러오는 데 실패했습니다.")
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
                u_id_str, u_pw_str = str(user_id).strip(), str(user_pw).strip()
                if u_id_str == MASTER_ID and u_pw_str == MASTER_PW:
                    st.session_state.logged_in, st.session_state.current_user = True, u_id_str; st.rerun()
                else:
                    match = df_users[(df_users["아이디"] == u_id_str) & (df_users["비밀번호"] == u_pw_str)]
                    if not match.empty and match.iloc[0]["상태"] == "정상":
                        st.session_state.logged_in, st.session_state.current_user = True, u_id_str; st.rerun()
                    else: st.error("로그인 실패 또는 정지된 계정입니다.")
                    
    with sign_tab:
        with st.form("signup_form"):
            new_id = st.text_input("새로운 아이디(ID)")
            new_pw = st.text_input("새로운 비밀번호(PW)", type="password")
            new_pw_check = st.text_input("비밀번호 확인", type="password")
            if st.form_submit_button("가입하기", use_container_width=True):
                nid_str, npw_str = str(new_id).strip(), str(new_pw).strip()
                if nid_str in df_users["아이디"].values or nid_str == MASTER_ID: st.warning("이미 존재하는 아이디입니다.")
                elif npw_str != str(new_pw_check).strip(): st.warning("비밀번호가 일치하지 않습니다.")
                elif len(nid_str) < 2: st.warning("아이디를 2자 이상 입력해 주세요.")
                else:
                    supabase.table("user_db").insert({"아이디": nid_str, "비밀번호": npw_str, "상태": "정상"}).execute()
                    supabase.table("quest_db").insert({"등록자": nid_str}).execute()
                    st.cache_data.clear(); st.success(f"가입 완료! '{nid_str}'로 로그인해 주세요.")
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
    if curr_m not in month_list: month_list.insert(0, curr_m)
else: month_list = [datetime.now().strftime('%Y-%m')]

if 'targets' not in st.session_state: st.session_state.targets = {'rev': 10000000, 'net': 4000000}

# --- [5] 사이드바 UI ---
with st.sidebar:
    st.title(f"👋 {current_user} 사장님" if not is_master else "👑 대표님(Master)")
    if st.button("로그아웃", use_container_width=True): st.session_state.logged_in = False; st.session_state.current_user = ""; st.rerun()
    st.divider()
    st.subheader("⚙️ 개인 설정")
    hourly_wage = st.number_input("나의 시간당 공임(원)", value=0, step=1000) 
    st.divider()
    st.title("🧮 계산기")
    if 'calc_val' not in st.session_state: st.session_state['calc_val'] = ""
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

# --- [6] 메인 화면 & 🚨 최상단 전광판 배너 ---
st.title(f"🍡 청다움 경영 관리 시스템 (ID: {current_user})")

# 전광판 배너 (가장 최근 매거진 제목을 불러와서 은밀하게 유혹합니다)
latest_news = df_magazine.iloc[0]['제목'] if not df_magazine.empty else "청다움 라운지에 새로운 디저트 트렌드와 꿀 거래처가 업데이트되었습니다!"
st.markdown(f"""
<div class="marquee-banner">
    <marquee scrollamount="8">📣 [오늘의 청다움 라운지] {latest_news} ➡️ 5번 탭 '청다움 라운지'에서 확인하세요!</marquee>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([3, 1])
with c2: selected_month = st.selectbox("📅 장부 조회 월(Month)", month_list)

monthly_sales = user_sales[user_sales['월'] == selected_month] if not user_sales.empty else pd.DataFrame()

# 💡 탭 배열 확정! (라운지 5번, 퀘스트 6번)
tab_names = ["📊 상품 정보 등록", "📈 실전 매출 입력", "🏆 성과 시각화", "🏭 경영 결산", "🎓 청다움 라운지", "🚀 창업 퀘스트"]
if is_master: tab_names.append("👑 마스터 관리")
tabs = st.tabs(tab_names)

# ==========================================
# 탭 1: 상품 등록 (원재료 + 부자재 분리)
# ==========================================
with tabs[0]:
    with st.expander("📍 신규 상품 영구 등록 (스마트 원가 계산기)", expanded=True):
        with st.form("v41_reg_form"):
            c1, c2, c3 = st.columns([2, 1, 1])
            p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
            target_m = c2.number_input("🎯 목표 마진", value=0.4, step=0.1)
            make_time = c3.number_input("⏱️ 제작 소요시간(분)", value=30, step=5)
            
            st.write("🌿 **1. [원재료] 투입량 입력 (키친코스트 방식)**")
            bom_recipe_init = pd.DataFrame([{"항목": "백앙금", "총용량(g,ml)": 5000, "총가격(원)": 15000, "레시피 투입량(g,ml)": 300}])
            bom_recipe = st.data_editor(bom_recipe_init, num_rows="dynamic", use_container_width=True, key="bom_r")
            
            st.write("🎀 **2. [부자재] 단품 입력 (포장지, 상자 등)**")
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
                            "등록자": current_user, "상품명": p_name, "원가": cost,
                            "마진": target_m, "권장가": price, "소요시간": make_time, "공임비": labor
                        }).execute()
                        st.cache_data.clear(); st.success(f"🎉 '{p_name}' 저장 완료! (원가: {fmt(cost)}원)"); st.rerun()
                    except Exception as e: st.error("저장 오류 (상품명 중복)")

    st.divider()
    if not df_p.empty:
        st.write("📋 내 계정에 등록된 상품 목록")
        del_p = st.selectbox("삭제할 상품", df_p["상품명"].dropna().tolist())
        if st.button("❌ 선택 상품 삭제", use_container_width=True):
            supabase.table("product_db").delete().eq("등록자", current_user).eq("상품명", del_p).execute()
            st.cache_data.clear(); st.rerun()
            
        disp = df_p.copy().drop(columns=['id', '등록자'], errors='ignore')
        for col in ["원가", "권장가", "공임비"]:
            if col in disp.columns: disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, hide_index=True, use_container_width=True)

# ==========================================
# 탭 2: 매출 입력 
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
                        "등록자": current_user, "날짜": s_date.strftime("%Y-%m-%d"), "월": target_m,
                        "경로": inb, "상품명": sel_p, "판매가": ap, "수량": qty, "총매출": rev, "순익": net
                    }).execute()
                    st.cache_data.clear(); st.success("✅ 매출이 등록되었습니다!"); st.rerun()
                except Exception: st.error("오류가 발생했습니다.")
    
    st.divider()
    st.markdown("### 🚩 이번 달 목표 세팅")
    t1, t2 = st.columns(2)
    st.session_state.targets['rev'] = t1.number_input("목표 총 매출액", value=st.session_state.targets['rev'])
    st.session_state.targets['net'] = t2.number_input("목표 영업 순수익", value=st.session_state.targets['net'])

    if not monthly_sales.empty:
        st.write(f"### 📑 {selected_month}월 매출 장부")
        with st.expander("🗑️ 기록 삭제 (오입력 수정)"):
            opt = {f"[{r['날짜']}] {r['상품명']} ({fmt(r['총매출'])}원)": r['id'] for i, r in monthly_sales.iterrows()}
            sel_del = st.selectbox("삭제 항목을 선택하세요", list(opt.keys()))
            if st.button("❌ 선택 기록 삭제", use_container_width=True):
                supabase.table("sales_db").delete().eq("id", int(opt[sel_del])).execute()
                st.cache_data.clear(); st.rerun()
                
        ds = monthly_sales.copy()
        for col in ["판매가", "총매출", "순익"]: ds[col] = pd.to_numeric(ds[col], errors='coerce').fillna(0)
        ds['수익률'] = (ds['순익'] / ds['총매출'] * 100).fillna(0).round(1).astype(str) + "%"
        for col in ["판매가", "총매출", "순익"]: ds[col] = ds[col].apply(lambda x: f"{fmt(x)}원")
        st.dataframe(ds.drop(columns=['id', '등록자', '월'], errors='ignore'), hide_index=True, use_container_width=True)
        
        tr_tab2 = pd.to_numeric(monthly_sales['총매출'], errors='coerce').fillna(0).sum()
        tn_tab2 = pd.to_numeric(monthly_sales['순익'], errors='coerce').fillna(0).sum()
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("💰 총 매출액", f"{fmt(tr_tab2)}원", f"{fmt(tr_tab2 - st.session_state.targets['rev'])}원")
        col2.metric("📈 영업 순이익", f"{fmt(tn_tab2)}원", f"{fmt(tn_tab2 - st.session_state.targets['net'])}원")

# ==========================================
# 탭 3: 성과 시각화 
# ==========================================
with tabs[2]:
    st.subheader(f"🏆 {selected_month}월 심층 데이터 시각화")
    if not monthly_sales.empty:
        an = monthly_sales.copy()
        for col in ["수량", "총매출", "순익"]: an[col] = pd.to_numeric(an[col], errors='coerce').fillna(0)
            
        c1, c2 = st.columns(2)
        path_data = an.groupby("경로")["총매출"].sum().reset_index()
        fig1 = px.pie(path_data, values='총매출', names='경로', hole=0.4, title="📍 유입 경로별 매출 비중")
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        c1.plotly_chart(fig1, use_container_width=True)
        
        prod_data = an.groupby("상품명")["총매출"].sum().reset_index().sort_values("총매출", ascending=True)
        fig2 = px.bar(prod_data, x='총매출', y='상품명', color='상품명', orientation='h', title="🏆 상품별 매출 순위", text_auto='.2s')
        fig2.update_layout(showlegend=False)
        c2.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        g = an.groupby("상품명")[["수량", "총매출", "순익"]].sum().reset_index()
        g["수익률"] = (g["순익"] / g["총매출"] * 100).round(1)
        
        c = st.columns(4)
        c[0].write("📊 **매출 Top 3**"); c[0].dataframe(g.sort_values("총매출", ascending=False).head(3)[["상품명", "총매출"]].assign(총매출=lambda x: x['총매출'].apply(fmt)), hide_index=True, use_container_width=True)
        c[1].write("💰 **순익 Top 3**"); c[1].dataframe(g.sort_values("순익", ascending=False).head(3)[["상품명", "순익"]].assign(순익=lambda x: x['순익'].apply(fmt)), hide_index=True, use_container_width=True)
        c[2].write("📈 **효자상품 (수익률)**"); c[2].dataframe(g.sort_values("수익률", ascending=False).head(3)[["상품명", "수익률"]].assign(수익률=lambda x: x['수익률'].astype(str) + "%"), hide_index=True, use_container_width=True)
        c[3].write("📦 **인기상품 (수량)**"); c[3].dataframe(g.sort_values("수량", ascending=False).head(3)[["상품명", "수량"]], hide_index=True, use_container_width=True)
        
    try: 
        st.divider()
        st.markdown("<h3 style='text-align: center; color: #4F8BF9;'>📣 청다움의 따뜻한 조언</h3>", unsafe_allow_html=True)
        st.image("청다움 멘트.png", use_container_width=True)
    except: pass

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
                try:
                    supabase.table("expense_db").delete().eq("등록자", current_user).eq("월", selected_month).execute()
                    supabase.table("expense_db").insert({
                        "등록자": current_user, "월": selected_month, 
                        "월세": r, "추가인건비": l, "공과금": t, "세금": t2, "기타비용": e
                    }).execute()
                    st.cache_data.clear(); st.rerun()
                except Exception: st.error("서버 지연 중입니다.")
                    
    total_e = r + l + t + t2 + e
    tr = pd.to_numeric(monthly_sales['총매출'], errors='coerce').fillna(0).sum() if not monthly_sales.empty else 0
    tn = pd.to_numeric(monthly_sales['순익'], errors='coerce').fillna(0).sum() if not monthly_sales.empty else 0
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
# 탭 5: 🎓 청다움 라운지 (매거진 + 비밀 창고)
# ==========================================
with tabs[4]:
    st.markdown("### 📰 청다움 트렌드 매거진")
    st.caption("나외치 경제팀과 치유팀이 API를 통해 매일 아침 엄선하는 디저트 인사이트입니다.")
    if not df_magazine.empty:
        for idx, row in df_magazine.iterrows():
            with st.expander(f"📌 [{row['작성일']}] {row['제목']}", expanded=(idx==0)):
                st.write(row['내용'])
    else:
        st.info("아직 발행된 매거진이 없습니다. 마스터 탭에서 API 로봇을 가동해 주세요!")
    
    st.divider()
    
    st.markdown("### 🤝 사장님들의 비밀 창고 (도매처 공유)")
    st.caption("전국 사장님들이 공유한 꿀 거래처입니다. (마스터 승인 건만 노출됩니다)")
    approved_links = df_link[df_link['상태'] == '승인']
    if not approved_links.empty:
        st.dataframe(approved_links[['업체명', '링크', '추천이유']], hide_index=True, use_container_width=True)
    else:
        st.info("아직 승인된 도매처가 없습니다. 첫 번째 꿀통을 공유해 보세요!")
        
    with st.expander("✨ 나만의 꿀 거래처 제보하기"):
        with st.form("link_form"):
            l_name = st.text_input("업체명 (예: 방산시장 OO패키지)")
            l_url = st.text_input("링크 (URL)")
            l_reason = st.text_input("추천 이유")
            if st.form_submit_button("제보하기"):
                if l_name and l_url:
                    supabase.table("link_db").insert({
                        "제보자": current_user, "업체명": l_name, "링크": l_url, "추천이유": l_reason, "상태": "대기"
                    }).execute()
                    st.cache_data.clear(); st.success("제보 완료! 마스터 승인 후 노출됩니다.")
                else: st.warning("업체명과 링크를 입력해주세요.")

# ==========================================
# 탭 6: 🚀 창업 퀘스트 (8단계 도장깨기 & 생존 계산기)
# ==========================================
with tabs[5]:
    # 💰 [중앙] 청다움 생존 계산기
    st.markdown("### 💰 청다움 생존 계산기 (초기 예산 검증기)")
    with st.container(border=True):
        budget = st.number_input("💵 1. 초기 예산 (가용 자금 총액)", value=0, step=1000000)
        st.caption("💸 **2. 방어벽 세팅 (지출 예상)**")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        dep = col_c1.number_input("보증금", value=0, step=1000000)
        rent = col_c2.number_input("월세 (안전빵 3~6개월치)", value=0, step=100000)
        interior = col_c3.number_input("인테리어 예상 비용", value=0, step=1000000)
        misc = col_c4.number_input("집기, 재료 및 기타", value=0, step=1000000)
        
        reserve = budget - (dep + rent + interior + misc)
        st.divider()
        st.metric("✨ 3. 최종 여유 자금 (비상금)", f"{fmt(reserve)}원")
        
        if reserve < 0:
            st.error("🚨 경고: 예산이 초과되었습니다! 무리한 대출이나 투자를 진행하기 전 다시 점검해 보세요!")
        elif reserve > 0 and budget > 0:
            st.success("✅ 안정적인 자금 흐름입니다! 오픈 후 버틸 수 있는 훌륭한 런웨이(Runway)를 확보하셨습니다.")
            
    st.divider()
    
    # 🚀 [상단] 8단계 퀘스트
    st.markdown("### 🚀 청다움 사관학교 8단계 퀘스트")
    user_quest = df_quest[df_quest['등록자'] == current_user]
    
    if user_quest.empty:
        supabase.table("quest_db").insert({"등록자": current_user}).execute()
        st.cache_data.clear(); st.rerun()
    else:
        uq = user_quest.iloc[0]
        quest_steps = [uq.get('step1', False), uq.get('step2', False), uq.get('step3', False), uq.get('step4', False), 
                       uq.get('step5', False), uq.get('step6', False), uq.get('step7', False), uq.get('step8', False)]
        progress = int((sum(quest_steps) / 8) * 100)
        
        st.progress(progress)
        st.write(f"**현재 창업 준비 {progress}% 완료!**")
        
        with st.form("quest_form"):
            s1 = st.checkbox("1단계: 보건증(건강진단결과서) 발급 완료", value=bool(uq.get('step1', False)))
            st.caption("💡 노하우: 신분증을 꼭 챙겨서 관할 보건소를 방문하세요! 검사 후 발급까지 약 5일(주말 제외)이 소요되니, 매장 계약 후 가장 먼저 움직이셔야 하는 1순위입니다.")
            
            s2 = st.checkbox("2단계: 식품위생교육 수료 완료", value=bool(uq.get('step2', False)))
            st.caption("💡 노하우: 한국휴게음식업중앙회 등에서 온라인 이수 가능합니다. 나중에 구청에 제출해야 하니 수료증은 반드시 출력하거나 PDF로 저장해 두세요!")
            
            s3 = st.checkbox("3단계: 영업신고증 발급 완료", value=bool(uq.get('step3', False)))
            st.caption("💡 노하우: 가장 떨리는 순간입니다! 확정일자 받은 임대차계약서, 보건증, 위생교육수료증, 신분증을 모두 챙겨서 관할 구청 위생과를 방문하세요.")
            
            s4 = st.checkbox("4단계: 사업자등록증 신청 및 사업자 통장 개설", value=bool(uq.get('step4', False)))
            st.caption("💡 노하우: 사업자등록증이 나오면 그 길로 바로 은행에 가서 '사업자 전용 통장'과 카드를 만드세요! 모든 매입/매출은 이 통장 하나로만 관리하셔야 세금 신고 때 피눈물을 흘리지 않습니다.")
            
            s5 = st.checkbox("5단계: 필수 집기 세팅 및 인테리어 마감", value=bool(uq.get('step5', False)))
            st.caption("💡 노하우: 화과자 제작에 필수적인 오븐과 찜기, 반죽기의 전력량(와트수)을 꼭 확인하시고, 사장님의 손목 피로도를 낮출 수 있는 최적의 작업 동선으로 가구를 배치하세요!")
            
            s6 = st.checkbox("6단계: 필요한 상품 재료 및 부자재 미리 확보", value=bool(uq.get('step6', False)))
            st.caption("💡 노하우: 포장 상자, 스티커, 기본 앙금 등은 배송 기간이 은근히 깁니다. 미리 발주해 두시되, 첫 초도 물량은 절대 너무 많이 잡지 마시고 시장 반응을 보며 늘려가는 것이 핵심입니다!")
            
            s7 = st.checkbox("7단계: 블로그, 인스타그램 등 SNS 계정 개설", value=bool(uq.get('step7', False)))
            st.caption("💡 노하우: 완벽하게 세팅된 다음 올리려 하지 마세요! 텅 빈 매장에 페인트칠하는 모습, 화과자 빚는 연습 과정 등 매장 오픈과정을 기록하는 것도 큰 도움이 됩니다. 성장 스토리에 기꺼이 지갑을 엽니다!")
            
            s8 = st.checkbox("8단계: 통신판매업 신고 및 온라인 판매 채널 오픈", value=bool(uq.get('step8', False)))
            st.caption("💡 노하우: 온라인 택배 판매를 하시려면 구청(또는 정부24)에서 '통신판매업 신고'가 필수입니다! (구매안전서비스 이용확인증 필요). 네이버 스마트스토어, 아이디어스 등은 입점 심사 기간이 있으니 오픈 전 미리 가입해 두세요.")
            
            if st.form_submit_button("✅ 퀘스트 진행 상황 영구 저장", use_container_width=True):
                supabase.table("quest_db").update({
                    "step1": s1, "step2": s2, "step3": s3, "step4": s4, "step5": s5, "step6": s6, "step7": s7, "step8": s8
                }).eq("등록자", current_user).execute()
                st.cache_data.clear(); st.success("진행 상황이 저장되었습니다!"); st.rerun()
                
    st.divider()
    st.markdown("### 🏢 전국 지원금 레이더 (API 연동 대기 중)")
    st.info("마스터가 공공데이터포털 API를 가동하면 여기에 지역별 지원금 목록이 표시됩니다.")

# ==========================================
# 탭 7: 👑 마스터 관리 (API 통제실 신설)
# ==========================================
if is_master:
    with tabs[6]:
        st.subheader("👑 최고 관리자 대시보드 및 API 통제실")
        
        # 🤖 [새로운 기능] 나외치 봇 API 가동실
        st.write("### 🤖 나외치 봇(Bot) 데이터 수집실")
        with st.expander("📡 외부 API 데이터 수동/자동 수집", expanded=True):
            st.caption("사전작업 3번에서 입력하신 API 키를 사용하여 데이터를 긁어옵니다.")
            api_c1, api_c2 = st.columns(2)
            
            if api_c1.button("🎥 유튜브 최신 디저트 트렌드 긁어오기 (테스트)"):
                if YOUTUBE_API_KEY != "여기에_유튜브_API키(AIza...)를_넣으세요":
                    st.success("유튜브 API가 정상적으로 연결되었습니다! (다음 버전에 치유풍 변환 로직이 추가됩니다)")
                else:
                    st.error("코드 상단에 유튜브 API 키를 먼저 입력해주세요!")
                    
            if api_c2.button("🏢 전국 소상공인 지원금 공고 긁어오기 (테스트)"):
                if PUBLIC_DATA_KEY != "여기에_공공데이터_일반인증키(Encoding)를_넣으세요":
                    st.success("공공데이터 API가 정상적으로 연결되었습니다! (다음 버전에 화면 출력 로직이 추가됩니다)")
                else:
                    st.error("코드 상단에 공공데이터 API 키를 먼저 입력해주세요!")

        st.divider()
        st.write("### 📰 매거진 수동 발행기 (나외치팀 전용)")
        with st.form("magazine_form"):
            m_title = st.text_input("매거진 제목 (전광판에 뜹니다!)")
            m_content = st.text_area("매거진 내용 (치유풍 텍스트)")
            if st.form_submit_button("🚀 매거진 전국 송출"):
                if m_title and m_content:
                    supabase.table("magazine_db").insert({
                        "제목": m_title, "내용": m_content, "작성일": datetime.now().strftime("%Y-%m-%d")
                    }).execute()
                    st.cache_data.clear(); st.success("성공적으로 발행되었습니다!"); st.rerun()

        st.divider()
        st.write("### 🤝 도매처 제보 승인 관리")
        pending_links = df_link[df_link['상태'] == '대기']
        if not pending_links.empty:
            st.dataframe(pending_links[['id', '제보자', '업체명', '링크', '추천이유']], hide_index=True, use_container_width=True)
            with st.form("approve_form"):
                target_id = st.number_input("승인/반려할 ID 번호를 입력하세요", min_value=0, step=1)
                c1, c2 = st.columns(2)
                if c1.form_submit_button("✅ 노출 승인", use_container_width=True):
                    supabase.table("link_db").update({"상태": "승인"}).eq("id", target_id).execute()
                    st.cache_data.clear(); st.rerun()
                if c2.form_submit_button("❌ 영구 삭제", use_container_width=True):
                    supabase.table("link_db").delete().eq("id", target_id).execute()
                    st.cache_data.clear(); st.rerun()
        else:
            st.info("현재 대기 중인 제보가 없습니다.")
