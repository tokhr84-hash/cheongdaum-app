import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V30.0", page_icon="🍡", layout="wide")

def fmt(val): 
    try:
        if pd.isna(val) or val == "": return "0"
        return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 구글 시트 메인 서버 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_master = conn.read(ttl=0)
    
    # 과거 데이터(대표님 혼자 쓰던 시절)에 등록자 ID가 없다면 'admin'으로 일괄 부여 (에러 방지용)
    if not df_master.empty and '등록자' not in df_master.columns:
        df_master['등록자'] = 'admin'
except Exception as e:
    st.error(f"메인 서버 연결 대기 중입니다. {e}")
    st.stop()

# --- [3] 회원가입 및 로그인 시스템 ---
# (※ 현재 회원명부는 테스트를 위해 앱 세션에 임시 저장됩니다. 추후 구글 시트로 영구 연동할 수 있습니다.)
if 'users_db' not in st.session_state:
    st.session_state.users_db = {"admin": "1234"} # 기본 관리자 계정

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = ""

# 로그인 화면 UI
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🍡 청다움 경영 관리 플랫폼</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>전국의 디저트 사장님들을 위한 스마트 비서</p>", unsafe_allow_html=True)
    st.divider()
    
    log_tab, sign_tab = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with log_tab:
        with st.form("login_form"):
            user_id = st.text_input("아이디(ID)", placeholder="admin")
            user_pw = st.text_input("비밀번호(PW)", type="password")
            submit_login = st.form_submit_button("입장하기", use_container_width=True)
            
            if submit_login:
                if user_id in st.session_state.users_db and st.session_state.users_db[user_id] == user_pw:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_id
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                    
    with sign_tab:
        with st.form("signup_form"):
            new_id = st.text_input("새로운 아이디(ID)")
            new_pw = st.text_input("새로운 비밀번호(PW)", type="password")
            new_pw_check = st.text_input("비밀번호 확인", type="password")
            submit_signup = st.form_submit_button("가입하기", use_container_width=True)
            
            if submit_signup:
                if new_id in st.session_state.users_db:
                    st.warning("이미 존재하는 아이디입니다.")
                elif new_pw != new_pw_check:
                    st.warning("비밀번호가 일치하지 않습니다.")
                elif len(new_id) < 2:
                    st.warning("아이디를 정확히 입력해 주세요.")
                else:
                    st.session_state.users_db[new_id] = new_pw
                    st.success(f"가입 환영합니다! 이제 '{new_id}' 아이디로 로그인해 주세요.")
    st.stop() # 로그인하지 않으면 아래 메인 기능으로 넘어가지 못하게 막습니다.

# --- [4] 개인별 데이터 필터링 (칸막이 기술) ---
current_user = st.session_state.current_user
if not df_master.empty and '등록자' in df_master.columns:
    # 마스터 시트에서 현재 로그인한 사람의 데이터만 걸러서 df_p 에 담습니다.
    df_p = df_master[df_master['등록자'] == current_user]
else:
    df_p = pd.DataFrame()

# 각 유저별 세션 메모리 초기화
if 'sales' not in st.session_state: st.session_state['sales'] = []
if 'targets' not in st.session_state: st.session_state.targets = {'rev': 10000000, 'net': 4000000}

# --- [5] 메인 시스템 UI (로그인 이후) ---
with st.sidebar:
    st.title(f"👋 {current_user} 사장님")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.session_state['sales'] = [] # 로그아웃 시 매출 화면 초기화
        st.rerun()
        
    st.divider()
    st.subheader("⚙️ 개인 설정")
    hourly_wage = st.number_input("나의 시간당 공임(원)", value=15000, step=1000)
    st.caption("※ 인건비가 포함된 진짜 순수익 계산용")
    
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

st.title(f"🍡 청다움 경영 관리 시스템 (ID: {current_user})")

tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🏆 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v30_reg_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        p_name = c1.text_input("📝 상품명", placeholder="예: 앙금플라워 6구")
        target_m = c2.number_input("🎯 목표 마진 (0.4 = 40%)", value=0.4, step=0.1)
        make_time = c3.number_input("⏱️ 제작 소요시간(분)", value=30, step=5)
        
        st.write("🌿 **[원재료등] 입력**") 
        bom = st.data_editor(pd.DataFrame([{"구분": "원재료", "항목": "기본재료", "수량": 1.0, "단가": 1000}]), num_rows="dynamic")
        
        if st.form_submit_button("💾 중앙 서버에 영구 저장"):
            if p_name:
                cost = float((bom["수량"] * bom["단가"]).sum())
                labor_cost = (hourly_wage / 60) * make_time
                price = float(np.round(cost / max(0.01, (1-target_m)), -1))
                
                # 저장할 때 반드시 '등록자' 꼬리표를 달아서 저장합니다.
                new_row = pd.DataFrame([{
                    "상품명": p_name, "원가": cost, "마진": target_m, 
                    "권장가": price, "소요시간": make_time, "공임비": labor_cost,
                    "등록자": current_user
                }])
                updated_master_df = pd.concat([df_master, new_row], ignore_index=True)
                conn.update(data=updated_master_df)
                st.success(f"🎉 '{p_name}' 등록 완료! (내 계정에 안전하게 귀속되었습니다)")
                st.rerun()

    st.divider()
    st.subheader("🗑️ 등록된 상품 삭제")
    if not df_p.empty and "상품명" in df_p.columns:
        del_target = st.selectbox("삭제할 상품을 선택하세요", df_p["상품명"].dropna().tolist())
        if st.button("❌ 선택한 상품 완전 삭제"):
            # 마스터 시트에서 해당 유저의 해당 상품만 정확히 삭제합니다.
            condition = (df_master['등록자'] == current_user) & (df_master['상품명'] == del_target)
            updated_master_df = df_master[~condition]
            conn.update(data=updated_master_df)
            st.warning(f"'{del_target}' 상품이 삭제되었습니다.")
            st.rerun()
            
    st.divider()
    if not df_p.empty:
        st.write("📋 내 계정에 등록된 상품 목록")
        disp = df_p.copy().drop(columns=['등록자'], errors='ignore') # 볼 때는 꼬리표를 숨겨서 깔끔하게 보여줍니다.
        for col in ["원가", "권장가", "공임비"]:
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
            c1, c2, c3 = st.columns([1, 1, 2])
            sale_date = c1.date_input("판매 날짜", datetime.now())
            inbound = c2.selectbox("유입 경로", ["인스타그램", "네이버예약", "지인소개", "워크인", "기타"])
            sel = c3.selectbox("상품 선택", p_list)
            
            p_info = df_p[df_p["상품명"] == sel].iloc[0]
            
            ca, cb, cc = st.columns(3)
            ap = ca.number_input("실제 판매가", value=int(float(p_info["권장가"])))
            qty = cb.number_input("판매 수량", value=1, step=1)
            
            if cc.button("목록에 추가", use_container_width=True):
                rev = float(ap) * qty
                pure_net = rev - (float(p_info["원가"]) * qty) - (float(p_info.get("공임비", 0)) * qty)
                st.session_state['sales'].append({
                    "날짜": sale_date.strftime("%Y-%m-%d"), 
                    "경로": inbound,
                    "상품명": sel, "판매가": ap, "수량": qty, 
                    "총매출": rev, "순익": pure_net
                })
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
        st.write("### 🏁 현재 경영 성과 합계 (공임비 차감 후 진짜 수익)")
        tot_rev = sales_df['총매출'].sum()
        tot_net = sales_df['순익'].sum()
        avg_margin = round((tot_net / tot_rev * 100), 1) if tot_rev > 0 else 0
        
        target_rev = st.session_state.targets['rev']
        target_net = st.session_state.targets['net']
        diff_rev = tot_rev - target_rev
        diff_net = tot_net - target_net
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 총 매출액 합산", f"{fmt(tot_rev)}원", f"{fmt(diff_rev)}원")
        col2.metric("📈 영업 순이익 합산", f"{fmt(tot_net)}원", f"{fmt(diff_net)}원")
        col3.metric("평균 수익률", f"{avg_margin}%")

# ==========================================
# 탭 3: 성과 분석 
# ==========================================
with tabs[2]:
    st.subheader("🏆 상품별 성과 및 마케팅 분석")
    if st.session_state['sales']:
        df_s = pd.DataFrame(st.session_state['sales'])
        
        st.markdown("##### 📍 유입 경로별 매출 현황")
        channel_rank = df_s.groupby("경로")[["총매출"]].sum().sort_values(by="총매출", ascending=False)
        st.bar_chart(channel_rank)

        st.divider()
        
        grouped = df_s.groupby("상품명")[["수량", "총매출", "순익"]].sum().reset_index()
        grouped["수익률"] = (grouped["순익"] / grouped["총매출"] * 100).fillna(0).round(1)
        
        c1, c2, c3, c4 = st.columns(4)
        
        r_rev = grouped.sort_values(by="총매출", ascending=False)[["상품명", "총매출"]].head(3).reset_index(drop=True)
        r_rev.index = range(1, len(r_rev)+1)
        r_rev["총매출"] = r_rev["총매출"].apply(fmt)
        c1.markdown("📊 **주요 순위 (매출)**")
        c1.dataframe(r_rev, use_container_width=True)
        
        r_net = grouped.sort_values(by="순익", ascending=False)[["상품명", "순익"]].head(3).reset_index(drop=True)
        r_net.index = range(1, len(r_net)+1)
        r_net["순익"] = r_net["순익"].apply(fmt)
        c2.markdown("💰 **순수익 순위**")
        c2.dataframe(r_net, use_container_width=True)
        
        r_mar = grouped.sort_values(by="수익률", ascending=False)[["상품명", "수익률"]].head(3).reset_index(drop=True)
        r_mar.index = range(1, len(r_mar)+1)
        r_mar["수익률"] = r_mar["수익률"].astype(str) + "%"
        c3.markdown("📈 **수익률**")
        c3.dataframe(r_mar, use_container_width=True)
        
        r_qty = grouped.sort_values(by="수량", ascending=False)[["상품명", "수량"]].head(3).reset_index(drop=True)
        r_qty.index = range(1, len(r_qty)+1)
        c4.markdown("📦 **판매순위**")
        c4.dataframe(r_qty, use_container_width=True)
    else:
        st.info("판매 데이터를 추가하시면 순위와 마케팅 그래프가 표시됩니다.")
        
    st.divider()
    sc1, sc2, sc3 = st.columns([1, 4, 1])
    with sc2:
        st.markdown("<h3 style='text-align: center; color: #4F8BF9;'>📣 청다움의 따뜻한 조언</h3>", unsafe_allow_html=True)
        try:
            st.image("청다움 멘트.png", use_container_width=True, caption="고객과 함께하는 따뜻한 치유")
        except:
            st.caption("※ GitHub 창고에 '청다움 멘트.png' 파일을 업로드하시면 여기에 표시됩니다.")

# ==========================================
# 탭 4: 최종 경영 결산
# ==========================================
with tabs[3]:
    st.subheader("🏭 최종 경영 결산")
    
    with st.expander("💸 이번 달 외부 입력 (세금 포함)", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        rent = c1.number_input("월세", value=0, step=10000)
        labor = c2.number_input("추가 인건비 (알바 등)", value=0, step=10000)
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
    m3.metric("📈 순수익(대표공임 제외)", f"{fmt(total_net)}원")
    m4.metric("💸 외부비용", f"{fmt(total_expenses)}원")
    m5.metric("✨ 최종 찐수익", f"{fmt(final_cash)}원", delta=f"{fmt(final_cash)}" if final_cash > 0 else None)
