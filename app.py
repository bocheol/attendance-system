import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="2-6 출결 보고", layout="centered")
st.title("🏫 2학년 6반 출결 보고 시스템")

# 1. 구글 스프레드시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 학생 로그인용 데이터 (비밀번호: 학번+!)
student_db = {str(20600 + i): f"{20600 + i}!" for i in range(1, 31)}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login_form"):
        st.subheader("로그인")
        user_id = st.text_input("학번 (5자리)", placeholder="20601")
        password = st.text_input("비밀번호", type="password")
        login_btn = st.form_submit_button("로그인")
        
        if login_btn:
            if user_id in student_db and student_db[user_id] == password:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("학번 또는 비밀번호가 틀렸습니다.")
else:
    # 3. 출결 입력 화면
    st.info(f"접속 학번: {st.session_state.user_id}")
    
    with st.form("attendance_form"):
        st.subheader("출결 정보 입력")
        
        # 날짜와 이름
        today = datetime.now().date()
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("날짜", value=today)
        with col2:
            user_name = st.text_input("이름", placeholder="홍길동")
        
        # 출결 종류 및 사유 (선생님 요청 반영)
        status = st.radio("출결 종류", ["지각", "조퇴", "결석", "결과"], horizontal=True)
        reason_type = st.selectbox("출결 사유", ["미인정", "병결", "기타", "인정"])
        
        # 교시 선택 (결석 시 자동 선택 로직)
        all_periods = [f"{i}교시" for i in range(1, 8)]
        if status == "결석":
            periods = st.multiselect("교시 선택", all_periods, default=all_periods)
        else:
            periods = st.multiselect("교시 선택", all_periods)
            
        specific_reason = st.text_area("상세 사유", placeholder="예: 늦잠으로 인한 지각, 감기 몸살 등")
        
        submit_btn = st.form_submit_button("전송하기")
        
        if submit_btn:
            if not user_name:
                st.error("이름을 입력해 주세요.")
            else:
                # 데이터 생성
                new_data = pd.DataFrame([{
                    "날짜": date_val.strftime("%Y-%m-%d"),
                    "학번": st.session_state.user_id,
                    "이름": user_name,
                    "출결 종류": status,
                    "출결 사유": reason_type,
                    "교시": ", ".join(periods),
                    "상세 사유": specific_reason
                }])
                
                # 시트 업데이트
                try:
                    existing_data = conn.read()
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("전송 완료! 오늘 하루도 힘내세요.")
                except:
                    st.error("구글 시트 연결에 실패했습니다. Secrets 설정을 확인해 주세요.")
            
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()
