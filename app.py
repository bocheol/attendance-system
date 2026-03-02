import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="2-6 출결 보고", layout="centered")
st.title("🏫 2학년 6반 출결 보고 시스템")

# 1. 구글 스프레드시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 학생 명단 및 비밀번호 불러오기 (시트의 '학생명단' 탭 사용)
try:
    # ttl=0을 넣어야 시트 내용을 수정했을 때 바로 앱에 반영됩니다.
    student_df = conn.read(worksheet="학생명단", ttl=0)
    student_df['학번'] = student_df['학번'].astype(str)
    student_df['비밀번호'] = student_df['비밀번호'].astype(str)
    
    student_db = dict(zip(student_df['학번'], student_df['비밀번호']))
    name_db = dict(zip(student_df['학번'], student_df['이름']))
except Exception as e:
    st.error("구글 시트의 '학생명단' 탭을 읽어오지 못했습니다. 시트 이름을 확인해주세요!")
    student_db = {}

# 로그인 세션 관리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login_form"):
        st.subheader("로그인")
        user_id = st.text_input("학번 (5자리)", placeholder="예: 20601")
        password = st.text_input("비밀번호", type="password")
        login_btn = st.form_submit_button("로그인")
        
        if login_btn:
            # 입력한 학번과 비번이 시트 데이터와 일치하는지 확인
            if user_id in student_db and student_db[user_id] == password:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_name = name_db.get(user_id, "학생")
                st.rerun()
            else:
                st.error("학번 또는 비밀번호가 틀렸습니다.")
else:
    # 3. 출결 입력 화면
    st.success(f"✅ 접속: {st.session_state.user_id} {st.session_state.user_name}")
    
    with st.form("attendance_form"):
        st.subheader("출결 보고 작성")
        
        today = datetime.now().date()
        date_val = st.date_input("날짜", value=today)
        user_name = st.text_input("이름", value=st.session_state.user_name)
        
        status = st.radio("출결 종류", ["지각", "조퇴", "결석", "결과"], horizontal=True)
        reason_type = st.selectbox("출결 사유", ["미인정", "병결", "기타", "인정"])
        
        all_periods = [f"{i}교시" for i in range(1, 8)]
        # 결석 선택 시 1~7교시 자동 체크
        default_p = all_periods if status == "결석" else []
        periods = st.multiselect("교시 선택", all_periods, default=default_p)
            
        specific_reason = st.text_area("상세 사유")
        
        submit_btn = st.form_submit_button("선생님께 전송하기")
        
        if submit_btn:
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
                # 데이터는 '시트1' 탭에 저장합니다.
                existing_data = conn.read(worksheet="시트1", ttl=0)
                updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                conn.update(worksheet="시트1", data=updated_df)
                st.balloons()
                st.success("전송되었습니다!")
            except Exception as e:
                st.error(f"전송 실패! 시트의 '시트1' 탭을 확인해주세요. ({e})")
            
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()
