import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 👑 [0] 마스터(최고 관리자) 설정 
# ==========================================
MASTER_ID = "master"    # 대표님 원하시는 아이디로 수정 가능
MASTER_PW = "150328"        # 대표님 원하시는 비밀번호로 수정 가능

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V36.2", page_icon="🍡", layout="wide")

def fmt(val): 
    try:
        if pd.isna(val) or val == "": 
            return "0"
        return f"{int(float(str(val).replace(',', ''))):,}"
    except: 
        return str(val)

# --- [2] 구글 시트 메인 서버 4대 장부 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # [장부 1] 상품 마스터
    df_master = conn.read(ttl=15)
    
    # [장부 2] 회원 명부
    try:
        df_users = conn.read(worksheet="user_db", ttl=15)
        if df_users.empty:
            df_users = pd.DataFrame([{"아이디": MASTER_ID, "비밀번호": MASTER_PW, "상태": "정상"}])
    except Exception:
        df_users = pd.DataFrame([{"아이디": MASTER_ID, "비밀번호": MASTER_PW, "상태": "정상"}])
        
    # [장부 3] 매출 기록부
    try:
        df_sales = conn.read(worksheet="sales_db", ttl=15)
        if df_sales.empty:
            df_sales = pd.DataFrame(columns=["등록자", "날짜", "경로", "상품명", "판매가", "수량", "총매출", "순익"])
    except Exception:
        df_sales = pd.DataFrame(columns=["등록자", "날짜", "경로", "상품명", "판매가", "수량", "총매출", "순익"])

    # [장부 4] 월별 지출 기록부
    try:
        df_expenses = conn.read(worksheet="expense_db", ttl=15)
        if df_expenses.empty:
            df_expenses = pd.DataFrame(columns=["등록자", "월", "월세", "추가인건비", "공과금", "세금", "기타비용"])
    except Exception:
        df_expenses = pd.DataFrame(columns=["등록자", "월", "월세", "추가인건비", "공과금", "세금", "기타비용"])

    # 데이터 정제 (소수점 유령 및 공백 제거)
    if not df_users.empty:
        df_users.fillna("", inplace=True)
        df_users["아이디"] = df_users["아이디"].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df_users["비밀번호"] = df_users["비밀번호"].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    for df_temp in [df_master, df_sales, df_expenses]:
        if not df_temp.empty and '등록자' in df_temp.columns:
            df_temp['등록자'] = df_temp['등록자'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

except Exception as e:
    st.error("🚦 현재 구글 서버 접속이 원활하지 않습니다. 잠시 후 새로고침(F5) 해주세요.")
    st.stop()

# --- [3] 로그인 및 회원가입 로직 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🍡 청다움 경영 관리 플랫폼</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>전국의 디저트 사장님들을 위한 스마트 비서</p>", unsafe_allow_html=True)
    st.divider()
    
    log_tab, sign_tab = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with log_tab:
        with st.form("login_form"):
            user_id = st.text_input("아이디(ID)", placeholder=MASTER_ID)
            user_pw = st.text_input("비밀번호(PW)", type="password")
            submit_login = st.form_submit_button("입장하기", use_container_width=True)
            
            if submit_login:
                u_id_str = str(user_id).strip()
                u_pw_str = str(user_pw).strip()
                
                # 👑 무적의 마스터 프리패스
                if u_id_str == MASTER_ID and u_pw_str == MASTER_PW:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u_id_str
                    st.rerun()
                else:
                    match = df_users[(df_users["아이디"] == u_id_str) & (df_users["비밀번호"] == u_pw_str)]
                    if not match.empty:
                        if match.iloc[0]["상태"] == "정상":
                            st.session_state.logged_in = True
                            st.session_state.current_user = u_id_str
                            st.rerun()
                        else:
                            st.error("🚫 해당 계정은 활동이 정지되었습니다. 본사에 문의하세요.")
                    else:
                        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                    
    with sign_tab:
        with st.form("signup_form"):
            new_id = st.text_input("새로운 아이디(ID)")
            new_pw = st.text_input("새로운 비밀번호(PW)", type="password")
            new_pw_check = st.text_input("비밀번호 확인", type="password")
            submit_signup = st.form_submit_button("가입하기", use_container_width=True)
            
            if submit_signup:
                nid_str = str(new_id).strip()
                npw_str = str(new_pw).strip()
                
                if nid_str in df_users["아이디"].values or nid_str == MASTER_ID:
                    st.warning("이미 존재하는 아이디입니다.")
                elif npw_str != str(new_pw_check).strip():
                    st.warning("비밀번호가 일치하지 않습니다.")
                elif len(nid_str) < 2:
                    st.warning("아이디를 2자 이상 입력해 주세요.")
                else:
                    new_user_df = pd.DataFrame([{"아이디": nid_str, "비밀번호": npw_str, "상태": "정상"}])
                    updated_users_df = pd.concat([df_users, new_user_df], ignore_index=True)
                    try:
                        conn.update(worksheet="user_db", data=updated_users_df)
                        st.cache_data.clear()
                        st.success(f"가입 완료! 이제 '{nid_str}'로 로그인해 주세요.")
                    except Exception:
                        st.error("서버 과부하로 가입이 지연되었습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

# --- [4] 개인별 칸막이 연동 (데이터 계승 로직 포함) ---
current_user = st.session_state.current_user
is_master = (current_user == MASTER_ID)

# 1. 상품 필터링
if not df_master.empty:
    if is_master:
        df_p = df_master[(df_master['등록자'] == current_user) | (df_master['등록자'] == "cheongdaum")]
    else:
        df_p = df_master[df_master['등록자'] == current_user]
else:
    df_p = pd.DataFrame()

# 2. 매출 필터링 및 월별 리스트 생성
if not df_sales.empty:
    if is_master:
        user_sales = df_sales[(df_sales['등록자'] == current_user) | (df_sales['등록자'] == "cheongdaum")].copy()
    else:
        user_sales = df_sales[df_sales['등록자'] == current_user].copy()
        
    if not user_sales.empty:
        user_sales['월'] = pd.to_datetime(user_sales['날짜']).dt.strftime('%Y-%m')
        month_list = sorted(user_sales['월'].unique().tolist(), reverse=True)
        curr_m = datetime.now().strftime('%Y-%m')
        if curr_m not in month_list: 
            month_list.insert(0, curr_m)
    else:
        month_list = [datetime.now().strftime('%Y-%m')]
else:
    user_sales = pd.DataFrame()
    month_list = [datetime.now().strftime('%Y-%m')]

# 3. 지출 필터링
if not df_expenses.empty:
    if is_master:
        user_expenses = df_expenses[(df_expenses['등록자'] == current_user) | (df_expenses['등록자'] == "cheongdaum")].copy()
    else:
        user_expenses = df_expenses[df_expenses['등록자'] == current_user].copy()
else:
    user_expenses = pd.DataFrame()

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
    hourly_wage = st.number_input("나의 시간당 공임(원)", value=15000, step=1000)
    
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

# --- [6] 메인 화면 및 캘린더 세팅 ---
st.title(f"🍡 청다움 경영 관리 시스템 (ID: {current_user})")

c1, c2 = st.columns([3, 1])
with c2: 
    selected_month = st.selectbox("📅 장부 조회 월(Month)", month_list)

# 선택된 월별 데이터 추출
if not user_sales.empty:
    monthly_sales = user_sales[user_sales['월'] == selected_month] 
else:
    monthly_sales = pd.DataFrame()

# 권한에 따른 탭 구성
if is_master:
    tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🏆 성과 분석(Rank)", "🏭 최종 경영 결산", "👑 총괄 마스터 관리"])
else:
    tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🏆 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v36_2_reg_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진", value=0.4, step=0.1)
        make_time = c3.number_input("⏱️ 제작 소요시간(분)", value=30, step=5)
        
        st.write("🌿 **[원재료등] 입력**")
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "기본재료", "수량": 1.0, "단가": 1000}]), num_rows="dynamic")
        
        if st.form_submit_button("💾 중앙 서버에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                labor = (hourly_wage / 60) * make_time
                price = float(np.round(cost / max(0.01, (1 - target_m)), -1))
                
                new_p = pd.DataFrame([{
                    "상품명": p_name, 
                    "원가": cost, 
                    "마진": target_m, 
                    "권장가": price, 
                    "소요시간": make_time, 
                    "공임비": labor, 
                    "등록자": current_user
                }])
                
                updated_master_df = pd.concat([df_master, new_p], ignore_index=True)
                try:
                    conn.update(data=updated_master_df)
                    st.cache_data.clear()
                    st.success(f"🎉 '{p_name}' 저장 완료!")
                    st.rerun()
                except Exception:
                    st.error("서버 과부하로 저장이 지연되었습니다.")

    st.divider()
    if not df_p.empty:
        st.write("📋 내 계정에 등록된 상품 목록")
        del_p = st.selectbox("삭제할 상품", df_p["상품명"].dropna().tolist())
        
        if st.button("❌ 선택 상품 삭제", use_container_width=True):
            condition = (df_master['등록자'].isin([current_user, "cheongdaum"])) & (df_master['상품명'] == del_p)
            updated_master_df = df_master[~condition]
            conn.update(data=updated_master_df)
            st.cache_data.clear()
            st.warning("상품이 삭제되었습니다.")
            st.rerun()
            
        disp = df_p.copy().drop(columns=['등록자'], errors='ignore')
        for col in ["원가", "권장가", "공임비"]:
            if col in disp.columns: 
                disp[col] = disp[col].apply(fmt)
        st.dataframe(disp, use_container_width=True)

# ==========================================
# 탭 2: 월간 매출 실적
# ==========================================
with tabs[1]:
    with st.expander(f"🚩 {selected_month}월 목표 설정", expanded=True):
        t1, t2 = st.columns(2)
        st.session_state.targets['rev'] = t1.number_input("목표 총 매출액", value=st.session_state.targets['rev'])
        st.session_state.targets['net'] = t2.number_input("목표 영업 순수익", value=st.session_state.targets['net'])
        
    st.subheader(f"📝 {selected_month}월 판매 데이터 추가")
    if not df_p.empty:
        c1, c2, c3 = st.columns([1, 1, 2])
        s_date = c1.date_input("판매 날짜", datetime.now())
        inb = c2.selectbox("유입 경로", ["인스타그램", "네이버예약", "지인소개", "워크인", "기타"])
        sel_p = c3.selectbox("상품 선택", df_p["상품명"].tolist())
        
        p_i = df_p[df_p["상품명"] == sel_p].iloc[0]
        
        ca, cb, cc = st.columns(3)
        ap = ca.number_input("실제 판매가", value=int(float(p_i["권장가"])))
        qty = cb.number_input("판매 수량", value=1, step=1)
        
        if cc.button("영구 장부에 기록 추가", use_container_width=True):
            rev = float(ap) * qty
            net = rev - (float(p_i["원가"]) * qty) - (float(p_i.get("공임비", 0)) * qty)
            
            new_s = pd.DataFrame([{
                "등록자": current_user, 
                "날짜": s_date.strftime("%Y-%m-%d"), 
                "경로": inb, 
                "상품명": sel_p, 
                "판매가": ap, 
                "수량": qty, 
                "총매출": rev, 
                "순익": net
            }])
            
            updated_sales_df = pd.concat([df_sales, new_s], ignore_index=True)
            try:
                conn.update(worksheet="sales_db", data=updated_sales_df)
                st.cache_data.clear()
                st.success("✅ 장부에 기록되었습니다!")
                st.rerun()
            except Exception:
                st.error("서버 오류입니다. 잠시 후 시도해주세요.")
                
    if not monthly_sales.empty:
        st.divider()
        st.write(f"### 📑 {selected_month}월 상세 판매현황")
        
        with st.expander("🗑️ 기록 삭제 (원하는 항목 선택 삭제)"):
            opt = {}
            for i, r in monthly_sales.iterrows():
                opt[f"[{r['날짜']}] {r['상품명']} ({fmt(r['총매출'])}원)"] = i
                
            sel_del = st.selectbox("삭제 항목을 선택하세요", list(opt.keys()))
            
            if st.button("❌ 선택 기록 삭제", use_container_width=True):
                target_idx = opt[sel_del]
                updated_sales_df = df_sales.drop(target_idx)
                conn.update(worksheet="sales_db", data=updated_sales_df)
                st.cache_data.clear()
                st.warning("기록이 삭제되었습니다.")
                st.rerun()
                
        ds = monthly_sales.copy()
        for col in ["판매가", "총매출", "순익"]:
            ds[col] = pd.to_numeric(ds[col], errors='coerce').fillna(0)
            
        ds['수익률'] = (ds['순익'] / ds['총매출'] * 100).fillna(0).round(1).astype(str) + "%"
        for col in ["판매가", "총매출", "순익"]:
            ds[col] = ds[col].apply(lambda x: f"{fmt(x)}원")
            
        st.dataframe(ds.drop(columns=['등록자', '월'], errors='ignore'), use_container_width=True)
        
        tr = pd.to_numeric(monthly_sales['총매출'], errors='coerce').fillna(0).sum()
        tn = pd.to_numeric(monthly_sales['순익'], errors='coerce').fillna(0).sum()
        
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("💰 총 매출액", f"{fmt(tr)}원", f"{fmt(tr - st.session_state.targets['rev'])}원")
        col2.metric("📈 영업 순이익", f"{fmt(tn)}원", f"{fmt(tn - st.session_state.targets['net'])}원")
    else:
        st.info(f"선택하신 {selected_month}월의 기록이 없습니다.")

# ==========================================
# 탭 3: 성과 분석
# ==========================================
with tabs[2]:
    st.subheader(f"🏆 {selected_month}월 상품별 성과 분석")
    if not monthly_sales.empty:
        an = monthly_sales.copy()
        for col in ["수량", "총매출", "순익"]:
            an[col] = pd.to_numeric(an[col], errors='coerce').fillna(0)
            
        st.markdown(f"##### 📍 {selected_month}월 유입 경로별 매출 현황")
        st.bar_chart(an.groupby("경로")["총매출"].sum())
        
        st.divider()
        
        g = an.groupby("상품명")[["수량", "총매출", "순익"]].sum().reset_index()
        g["수익률"] = (g["순익"] / g["총매출"] * 100).round(1)
        
        c = st.columns(4)
        
        c[0].write("📊 **매출 순위**")
        c[0].dataframe(g.sort_values("총매출", ascending=False).head(3)[["상품명", "총매출"]].assign(총매출=lambda x: x['총매출'].apply(fmt)), use_container_width=True)
        
        c[1].write("💰 **순익 순위**")
        c[1].dataframe(g.sort_values("순익", ascending=False).head(3)[["상품명", "순익"]].assign(순익=lambda x: x['순익'].apply(fmt)), use_container_width=True)
        
        c[2].write("📈 **수익률**")
        c[2].dataframe(g.sort_values("수익률", ascending=False).head(3)[["상품명", "수익률"]].assign(수익률=lambda x: x['수익률'].astype(str) + "%"), use_container_width=True)
        
        c[3].write("📦 **판매 순위**")
        c[3].dataframe(g.sort_values("수량", ascending=False).head(3)[["상품명", "수량"]], use_container_width=True)
        
    try: 
        st.divider()
        st.markdown("<h3 style='text-align: center; color: #4F8BF9;'>📣 청다움의 따뜻한 조언</h3>", unsafe_allow_html=True)
        st.image("청다움 멘트.png", use_container_width=True)
    except: 
        pass

# ==========================================
# 탭 4: 최종 경영 결산
# ==========================================
with tabs[3]:
    st.subheader(f"🏭 {selected_month}월 최종 결산")
    
    if not user_expenses.empty:
        curr_exp = user_expenses[user_expenses['월'] == selected_month]
    else:
        curr_exp = pd.DataFrame()
        
    if not curr_exp.empty:
        v = curr_exp.iloc[0]
    else:
        v = {"월세": 0, "추가인건비": 0, "공과금": 0, "세금": 0, "기타비용": 0}
        
    with st.expander(f"💸 {selected_month}월 외부 지출 입력 및 저장", expanded=True):
        with st.form("exp_form"):
            c1, c2, c3, c4, c5 = st.columns(5)
            r = c1.number_input("월세", value=int(v['월세']), step=10000)
            l = c2.number_input("인건비", value=int(v['추가인건비']), step=10000)
            t = c3.number_input("공과금", value=int(v['공과금']), step=10000)
            t2 = c4.number_input("세금", value=int(v['세금']), step=10000)
            e = c5.number_input("기타", value=int(v['기타비용']), step=10000)
            
            if st.form_submit_button("💾 이 달의 고정 지출 영구 저장", use_container_width=True):
                condition = (df_expenses['등록자'].isin([current_user, "cheongdaum"])) & (df_expenses['월'] == selected_month)
                ue = df_expenses[~condition]
                
                ne = pd.DataFrame([{
                    "등록자": current_user, 
                    "월": selected_month, 
                    "월세": r, 
                    "추가인건비": l, 
                    "공과금": t, 
                    "세금": t2, 
                    "기타비용": e
                }])
                
                updated_exp_df = pd.concat([ue, ne], ignore_index=True)
                try:
                    conn.update(worksheet="expense_db", data=updated_exp_df)
                    st.cache_data.clear()
                    st.success(f"✅ {selected_month}월 지출이 저장되었습니다.")
                    st.rerun()
                except Exception:
                    st.error("서버 지연 중입니다.")
                    
    total_e = r + l + t + t2 + e
    st.write(f"**외부비용 합계:** {fmt(total_e)}원")
    
    if not monthly_sales.empty:
        tr = pd.to_numeric(monthly_sales['총매출'], errors='coerce').fillna(0).sum()
        tn = pd.to_numeric(monthly_sales['순익'], errors='coerce').fillna(0).sum()
    else:
        tr = 0
        tn = 0
        
    final_cash = tn - total_e
    
    st.divider()
    st.write(f"### 🏁 {selected_month}월 결산 대시보드")
    m = st.columns(5)
    m[0].metric("🎯 목표 (매출)", f"{fmt(st.session_state.targets['rev'])}원")
    m[1].metric("💰 매출", f"{fmt(tr)}원")
    m[2].metric("📈 순익 (공임 제외)", f"{fmt(tn)}원")
    m[3].metric("💸 외부비용", f"{fmt(total_e)}원")
    m[4].metric("✨ 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}" if final_cash > 0 else None)

# ==========================================
# 탭 5: 👑 총괄 마스터 관리
# ==========================================
if is_master:
    with tabs[4]:
        st.subheader("👑 플랫폼 사법 관리 대시보드")
        
        # 1. 회원 관리
        st.write("### 👥 회원 계정 관리")
        try:
            user_list = df_users["아이디"].tolist()
            manage_list = [u for u in user_list if u != MASTER_ID]
            
            if manage_list:
                su = st.selectbox("관리할 사장님 아이디 선택", manage_list)
                ur = df_users[df_users["아이디"] == su].iloc[0]
                
                c1, c2, c3 = st.columns(3)
                c1.info(f"아이디: {su} / 상태: {ur['상태']}")
                
                if ur['상태'] == "정상":
                    if c2.button("🚫 계정 정지", use_container_width=True):
                        df_users.loc[df_users["아이디"] == su, "상태"] = "정지"
                        conn.update(worksheet="user_db", data=df_users)
                        st.cache_data.clear()
                        st.rerun()
                else:
                    if c2.button("✅ 정지 해제", use_container_width=True):
                        df_users.loc[df_users["아이디"] == su, "상태"] = "정상"
                        conn.update(worksheet="user_db", data=df_users)
                        st.cache_data.clear()
                        st.rerun()
                        
                if c3.button("🔥 강제 탈퇴", use_container_width=True):
                    updated_users_df = df_users[df_users["아이디"] != su]
                    conn.update(worksheet="user_db", data=updated_users_df)
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.info("관리할 회원이 없습니다.")
        except Exception:
            st.warning("회원 명부 로딩 중...")

        st.divider()
        st.write("### 🗄️ 전수 조사 (전체 데이터베이스)")
        
        c = st.tabs(["📦 상품 장부", "🧾 매출 장부", "💸 지출 장부", "👥 회원 장부"])
        with c[0]:
            if not df_master.empty:
                disp_master = df_master.copy()
                for col in ["원가", "권장가", "공임비"]:
                    if col in disp_master.columns: 
                        disp_master[col] = disp_master[col].apply(fmt)
                st.dataframe(disp_master, use_container_width=True)
            else:
                st.write("데이터 없음")
                
        with c[1]:
            if not df_sales.empty:
                disp_sales_all = df_sales.copy()
                for col in ["판매가", "총매출", "순익"]:
                    if col in disp_sales_all.columns: 
                        disp_sales_all[col] = pd.to_numeric(disp_sales_all[col], errors='coerce').fillna(0).apply(fmt)
                st.dataframe(disp_sales_all, use_container_width=True)
            else:
                st.write("데이터 없음")
                
        with c[2]:
            if not df_expenses.empty:
                disp_exp_all = df_expenses.copy()
                for col in ["월세", "추가인건비", "공과금", "세금", "기타비용"]:
                    if col in disp_exp_all.columns:
                        disp_exp_all[col] = pd.to_numeric(disp_exp_all[col], errors='coerce').fillna(0).apply(fmt)
                st.dataframe(disp_exp_all, use_container_width=True)
            else:
                st.write("데이터 없음")
                
        with c[3]:
            st.dataframe(df_users, use_container_width=True)
