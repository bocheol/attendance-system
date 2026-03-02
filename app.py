import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="2-6 출결 보고", layout="centered")
st.title("🏫 2학년 6반 출결 보고 시스템")

# 1. 구글 스프레드시트 연결 (Streamlit 공식 연결 사용)
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 학생 데이터 설정 (비밀번호는 예시로 '학번+!'로 설정)
# 실제 운영시에는 별도의 시트에서 불러오도록 수정 가능합니다.
student_db = {str(20600 + i): f"{20600 + i}!" for i in range(1, 31)}

# 3. 로그인 세션 관리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login_form"):
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
    # 4. 출결 입력 화면
    st.info(f"접속 중인 학번: {st.session_state.user_id}")
    
    with st.form("attendance_form"):
        today = datetime.now().date()
        date_val = st.date_input("날짜", value=today)
        
        status = st.radio("출결 상황", ["지각", "조퇴", "결과", "결석"], horizontal=True)
        reason_type = st.selectbox("사유 구분", ["미인정", "병결", "기타", "인정"])
        
        # '결석' 선택 시 1~7교시 자동 선택 로직
        all_periods = [f"{i}교시" for i in range(1, 8)]
        if status == "결석":
            periods = st.multiselect("교시 선택", all_periods, default=all_periods)
        else:
            periods = st.multiselect("교시 선택", all_periods)
            
        specific_reason = st.text_input("상세 사유 (예: 늦잠, 감기 등)")
        
        submit_btn = st.form_submit_button("전송하기")
        
        if submit_btn:
            # 구글 시트에 데이터 추가 (실제 배포 시 시트 URL 필요)
            new_data = pd.DataFrame([{
                "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "학번": st.session_state.user_id,
                "상태": status,
                "구분": reason_type,
                "교시": ", ".join(periods),
                "상세사유": specific_reason
            }])
            
            # 구글 시트 업데이트 로직 (st.connection 활용)
            existing_data = conn.read()
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("보고가 완료되었습니다! 선생님께 전송되었습니다.")
            
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()
