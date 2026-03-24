import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 👑 [0] 마스터(최고 관리자) 고정 설정
# ==========================================
MASTER_ID = "cheongdaum"    # 대표님 고정 아이디
MASTER_PW = "150328"        # 대표님 고정 비밀번호

# --- [1] 시스템 설정 ---
st.set_page_config(page_title="청다움 마스터 V33.2", page_icon="🍡", layout="wide")

def fmt(val): 
    try:
        if pd.isna(val) or val == "": return "0"
        return f"{int(float(str(val).replace(',', ''))):,}"
    except: return str(val)

# --- [2] 구글 시트 메인 서버 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # [장부 1] 상품 마스터 로드 (기본 첫 번째 시트)
    df_master = conn.read(ttl=0)
    
    # [장부 2] 회원 명부 로드 (user_db 시트 영구 저장용)
    try:
        df_users = conn.read(worksheet="user_db", ttl=0)
        # 만약 시트가 비어있다면 마스터 계정 기본 생성
        if df_users.empty:
            df_users = pd.DataFrame([{"아이디": MASTER_ID, "비밀번호": MASTER_PW, "상태": "정상"}])
            conn.update(worksheet="user_db", data=df_users)
    except Exception:
        # user_db 탭이 없거나 에러가 나면 새로 생성
        df_users = pd.DataFrame([{"아이디": MASTER_ID, "비밀번호": MASTER_PW, "상태": "정상"}])
        conn.update(worksheet="user_db", data=df_users)

    # 과거 데이터 호환성 유지
    if not df_master.empty and '등록자' not in df_master.columns:
        df_master['등록자'] = MASTER_ID
except Exception as e:
    st.error(f"메인 서버 연결 대기 중입니다. {e}")
    st.stop()

# --- [3] 로그인 및 회원가입 로직 (시트 연동형 + 마스터 프리패스) ---
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
                # 👑 [긴급 마스터 프리패스]: 코드로 설정한 대표님 계정은 구글 시트 상태와 무관하게 100% 열립니다.
                if user_id == MASTER_ID and user_pw == MASTER_PW:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_id
                    st.rerun()
                else:
                    # 일반 사장님들은 구글 시트(df_users)에서 일치하는지 확인
                    match = df_users[(df_users["아이디"] == user_id) & (df_users["비밀번호"] == user_pw)]
                    if not match.empty:
                        if match.iloc[0]["상태"] == "정상":
                            st.session_state.logged_in = True
                            st.session_state.current_user = user_id
                            st.rerun()
                        else:
                            st.error("🚫 해당 계정은 관리자에 의해 활동이 정지되었습니다. 본사에 문의하세요.")
                    else:
                        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                    
    with sign_tab:
        with st.form("signup_form"):
            new_id = st.text_input("새로운 아이디(ID)")
            new_pw = st.text_input("새로운 비밀번호(PW)", type="password")
            new_pw_check = st.text_input("비밀번호 확인", type="password")
            submit_signup = st.form_submit_button("가입하기", use_container_width=True)
            
            if submit_signup:
                if new_id in df_users["아이디"].values or new_id == MASTER_ID:
                    st.warning("이미 존재하는 아이디입니다.")
                elif new_pw != new_pw_check:
                    st.warning("비밀번호가 일치하지 않습니다.")
                elif len(new_id) < 2:
                    st.warning("아이디를 정확히 입력해 주세요.")
                else:
                    # 새로운 회원을 구글 시트에 즉시 영구 저장
                    new_user_df = pd.DataFrame([{"아이디": new_id, "비밀번호": new_pw, "상태": "정상"}])
                    updated_users_df = pd.concat([df_users, new_user_df], ignore_index=True)
                    conn.update(worksheet="user_db", data=updated_users_df)
                    st.success(f"가입 환영합니다! 이제 '{new_id}' 아이디로 로그인해 주세요.")
    st.stop()

# --- [4] 데이터 필터링 (칸막이) ---
current_user = st.session_state.current_user
if not df_master.empty and '등록자' in df_master.columns:
    df_p = df_master[df_master['등록자'] == current_user]
else:
    df_p = pd.DataFrame()

if 'sales' not in st.session_state: st.session_state['sales'] = []
if 'targets' not in st.session_state: st.session_state.targets = {'rev': 10000000, 'net': 4000000}

# --- [5] 사이드바 UI ---
with st.sidebar:
    st.title(f"👋 {current_user} 사장님" if current_user != MASTER_ID else "👑 대표님(Master)")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.session_state['sales'] = [] 
        st.rerun()
    
    st.divider()
    st.subheader("⚙️ 개인 설정")
    hourly_wage = st.number_input("나의 시간당 공임(원)", value=15000, step=1000)
    
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

# 마스터 권한에 따른 탭 구성
if current_user == MASTER_ID:
    tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🏆 성과 분석(Rank)", "🏭 최종 경영 결산", "👑 총괄 마스터 관리"])
else:
    tabs = st.tabs(["📊 상품 정보 등록", "📈 월간 매출 실적", "🏆 성과 분석(Rank)", "🏭 최종 경영 결산"])

# ==========================================
# 탭 1: 상품 정보 등록
# ==========================================
with tabs[0]:
    st.subheader("📍 신규 상품 영구 등록")
    with st.form("v33_reg_form"):
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
            condition = (df_master['등록자'] == current_user) & (df_master['상품명'] == del_target)
            updated_master_df = df_master[~condition]
            conn.update(data=updated_master_df)
            st.warning(f"'{del_target}' 상품이 삭제되었습니다.")
            st.rerun()
            
    st.divider()
    if not df_p.empty:
        st.write("📋 내 계정에 등록된 상품 목록")
        disp = df_p.copy().drop(columns=['등록자'], errors='ignore') 
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

# ==========================================
# 탭 5: 👑 총괄 마스터 관리
# ==========================================
if current_user == MASTER_ID:
    with tabs[4]:
        st.subheader("👑 플랫폼 사법 관리 대시보드")
        
        # 1. 회원 목록 및 상태 관리
        st.write("### 👥 회원 계정 관리")
        user_list = df_users["아이디"].tolist()
        manage_list = [u for u in user_list if u != MASTER_ID]
        
        if manage_list:
            selected_user = st.selectbox("관리할 사장님 아이디를 선택하세요", manage_list)
            u_row = df_users[df_users["아이디"] == selected_user].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            col1.info(f"아이디: {selected_user}")
            col2.info(f"현재 상태: {u_row['상태']}")
            
            # 버튼 영역
            b1, b2, b3 = st.columns(3)
            if u_row['상태'] == "정상":
                if b1.button("🚫 계정 정지시키기", use_container_width=True):
                    df_users.loc[df_users["아이디"] == selected_user, "상태"] = "정지"
                    conn.update(worksheet="user_db", data=df_users)
                    st.warning(f"'{selected_user}' 계정이 정지되었습니다.")
                    st.rerun()
            else:
                if b1.button("✅ 정지 해제하기", use_container_width=True):
                    df_users.loc[df_users["아이디"] == selected_user, "상태"] = "정상"
                    conn.update(worksheet="user_db", data=df_users)
                    st.success(f"'{selected_user}' 계정이 정상 복구되었습니다.")
                    st.rerun()
            
            if b2.button("🔥 강제 탈퇴 (영구 삭제)", use_container_width=True):
                df_users = df_users[df_users["아이디"] != selected_user]
                conn.update(worksheet="user_db", data=df_users)
                st.error(f"'{selected_user}' 계정이 영구 삭제되었습니다.")
                st.rerun()

        else:
            st.info("관리할 신규 회원이 아직 없습니다.")

        st.divider()
        st.write("### 🗄️ 플랫폼 데이터 전수 조사 (전체 회원 상품 DB)")
        if not df_master.empty:
            disp_master = df_master.copy()
            for col in ["원가", "권장가", "공임비"]:
                if col in disp_master.columns: disp_master[col] = disp_master[col].apply(fmt)
            st.dataframe(disp_master, use_container_width=True)
        else:
            st.write("등록된 전체 데이터가 없습니다.")
