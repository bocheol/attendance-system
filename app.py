import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="2-6 출결 보고", layout="centered")
st.title("🏫 2학년 6반 출결 보고 시스템")

# 1. 구글 스프레드시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 학생 명단 및 비밀번호 불러오기
# '학생명단'이라는 이름의 워크시트에서 데이터를 읽어옵니다.
try:
    student_df = conn.read(worksheet="학생명단")
    # 학번을 키로, 비밀번호를 값으로 하는 딕셔너리 생성
    student_db = dict(zip(student_df['학번'].astype(str), student_df['비밀번호'].astype(str)))
    # 학번을 키로, 이름을 값으로 하는 딕셔너리 생성 (자동 입력용)
    name_db = dict(zip(student_df['학번'].astype(str), student_df['이름'].astype(str)))
except:
    st.error("구글 시트에서 '학생명단' 시트를 찾을 수 없습니다.")
    student_db = {}

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
                st.session_state.user_name = name_db.get(user_id, "")
                st.rerun()
            else:
                st.error("학번 또는 비밀번호가 틀렸습니다.")
else:
    # 3. 출결 입력 화면
    st.info(f"접속: {st.session_state.user_id} {st.session_state.user_name}")
    
    with st.form("attendance_form"):
        st.subheader("출결 정보 입력")
        
        today = datetime.now().date()
        date_val = st.date_input("날짜", value=today)
        
        # 이름은 로그인 정보를 바탕으로 자동 입력
        user_name = st.text_input("이름", value=st.session_state.user_name)
        
        status = st.radio("출결 종류", ["지각", "조퇴", "결석", "결과"], horizontal=True)
        reason_type = st.selectbox("출결 사유", ["미인정", "병결", "기타", "인정"])
        
        all_periods = [f"{i}교시" for i in range(1, 8)]
        if status == "결석":
            periods = st.multiselect("교시 선택", all_periods, default=all_periods)
        else:
            periods = st.multiselect("교시 선택", all_periods)
            
        specific_reason = st.text_area("상세 사유")
        
        submit_btn = st.form_submit_button("전송하기")
        
        if submit_btn:
            # 첫 번째 시트(출결데이터)에 저장 (worksheet를 명시하지 않으면 첫 번째 시트에 저장됨)
            new_data = pd.DataFrame([{
                "날짜": date_val.strftime("%Y-%m-%d"),
                "학번": st.session_state.user_id,
                "이름": user_name,
                "출결 종류": status,
                "출결 사유": reason_type,
                "교시": ", ".join(periods),
                "상세 사유": specific_reason
            }])
            
            try:
                existing_data = conn.read(worksheet="시트1") # 출결 데이터가 쌓이는 시트 이름 확인 필요
                updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                conn.update(worksheet="시트1", data=updated_df)
                st.success("선생님께 전송되었습니다!")
            except:
                st.error("데이터 저장 시트 이름을 확인해 주세요.")
            
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()
