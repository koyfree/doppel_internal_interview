# main.py
import streamlit as st
import interview

st.set_page_config(page_title="AITwinBot 시작", page_icon="🤖")

if "phase" not in st.session_state:
    st.session_state.phase = "intro"

if st.session_state.phase == "intro":
    st.title("AITwinBot 실험 시작")

    # 1. ID 입력
    user_id = st.text_input("고유 ID (숫자 5자리)를 입력하고 enter 키를 눌러 주세요.", key="user_id_input")

    # 2. 닉네임 입력
    if user_id.strip().isdigit() and len(user_id.strip()) == 5:
        nickname = st.text_input("챗봇이 당신을 뭐라고 부르면 좋을까요? 예: 카리나님, 윈터님 등. 이 별명은 저장되지 않습니다 :)", key="nickname_input")

        if nickname.strip():
            st.markdown(f"""
            안d녕하세요 **{nickname}**님!  
            본격적인 대화를 시작하기 전에, 안내봇이 간단한 인터뷰를 진행하려고 해요.  
            **좋아하는 것, 싫어하는 것, 그리고 평소 일상**에 대해 몇 가지 여쭤볼 거예요.  
            이 인터뷰가 끝나면, 트윈봇과의 대화를 시작할 수 있어요!
            대화는 영어로 진행됩니다.
            준비되셨다면 아래 버튼을 눌러주세요.
            """)

            if st.button("다음"):
                # 세션 초기화
                st.session_state.user_id = user_id
                st.session_state.nickname = nickname
                st.session_state.phase = "interview"
                st.session_state.topic_index = 0
                st.session_state.topics = ["좋아하는 것", "싫어하는 것", "주간 활동"]
                st.session_state.messages_likes = []
                st.session_state.messages_dislikes = []
                st.session_state.messages_weekly = []
                st.session_state.messages = []
                st.rerun()
    else:
        st.warning("고유 ID는 숫자 5자리여야 해요.")

elif st.session_state.phase == "interview":
    interview.run()
