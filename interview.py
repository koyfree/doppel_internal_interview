# interview.py
import streamlit as st
from openai import OpenAI

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def run():
    st.title("🧠 AITwinBot 인터뷰 세션")

    # 클라이언트 설정
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])

    # 인터뷰 단계 초기화
    if "interview_phase" not in st.session_state:
        st.session_state.interview_phase = "likes"  # "likes" → "dislikes" → "next_button" → "weekly" → "done"
        st.session_state.messages = []

    # 종료 조건 메시지
    LIKE_END = "Thank you for sharing all these details."
    DISLIKE_END = "Thank you so much for your detailed answers. This really helps Twinbot understand you better!"
    WEEKLY_END = "Thank you for your detailed answers. Now I have a good picture of your past week. This will really help Twinbot understand you better!"

    # 프롬프트 로딩
    if st.session_state.interview_phase in ["likes", "dislikes"]:
        prompt = load_prompt("prompts/preferences.txt")
    elif st.session_state.interview_phase == "weekly":
        prompt = load_prompt("prompts/weekly.txt")
    else:
        prompt = ""

    # 시스템 메시지 없으면 삽입
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "system", "content": prompt})

    # 채팅 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 입력
    user_input = st.chat_input("메시지를 입력해주세요.")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=st.session_state.messages,
            temperature=1,
            max_tokens=2048
        )
        bot_reply = response.choices[0].message.content.strip()
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        # 종료 감지
        if st.session_state.interview_phase == "likes" and LIKE_END in bot_reply:
            st.session_state.messages_likes = st.session_state.messages.copy()
            st.session_state.messages = [{"role": "system", "content": prompt}]
            st.session_state.interview_phase = "dislikes"

        elif st.session_state.interview_phase == "dislikes" and DISLIKE_END in bot_reply:
            st.session_state.messages_dislikes = st.session_state.messages.copy()
            st.session_state.interview_phase = "next_button"

        elif st.session_state.interview_phase == "weekly" and WEEKLY_END in bot_reply:
            st.session_state.messages_weekly = st.session_state.messages.copy()
            st.session_state.interview_phase = "done"

    # 싫어하는 것 다음 → 다음 주제로 버튼
    if st.session_state.interview_phase == "next_button":
        if st.button("다음 주제로"):
            st.session_state.interview_phase = "weekly"
            st.session_state.messages = [{"role": "system", "content": load_prompt("prompts/weekly.txt")}]
            st.experimental_rerun()

    # 주간 활동 끝났으면 링크 안내 메시지 출력
    if st.session_state.interview_phase == "done":
        with st.chat_message("assistant"):
            st.markdown("이제 도플갱어 챗봇과의 대화를 시작할 수 있어요!  
            👉 [다음 실험 단계로 이동](#)")

        # 말풍선 출력 (3개)
        st.header("📦 인터뷰 결과 확인")
        for label, key in [
            ("좋아하는 것", "messages_likes"),
            ("싫어하는 것", "messages_dislikes"),
            ("주간 활동", "messages_weekly")
        ]:
            st.subheader(f"🟢 {label}")
            for msg in st.session_state.get(key, []):
                role = "🧍‍♀️" if msg["role"] == "user" else "🤖"
                st.markdown(f"{role} **{msg['role']}**: {msg['content']}")

        st.stop()
