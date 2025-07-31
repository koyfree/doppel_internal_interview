import streamlit as st
from openai import OpenAI
import time

LIKE_END = "Thank you for sharing all these details."
DISLIKE_END = "Thank you so much for your detailed answers. This really helps Twinbot understand you better!"
WEEKLY_END = "Thank you for your detailed answers. Now I have a good picture of your past week. This will really help Twinbot understand you better!"

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def run():
    st.title("🧠 AITwinBot 인터뷰")

    client = OpenAI(api_key=st.secrets["openai"]["api_key"])

    if "interview_phase" not in st.session_state:
        st.session_state.interview_phase = "likes"
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.intro_done = False
        st.session_state.awaiting_response = False
        st.session_state.pending_user_input = None

    # ✅ 인트로 메시지 + GPT 첫 응답
    if st.session_state.interview_phase == "likes" and not st.session_state.intro_done:
        nickname = st.session_state.get("nickname", "there")
        intro_messages = [
            f"Nice to meet you, {nickname}!",
            "Great, now I’d love to know more about your preferences!",
            "There are no specific rules, so feel free to write casually, just like you’re chatting with a friend.",
            "Anything is fine—adjectives, objects, people, food, behaviors, hobbies, etc. It would be great if you could be as specific as possible!",
            "For example, instead of saying ‘I like music,’ say something like ‘I love rock ballads.’ The more details you give, the better Twinbot can understand you."
        ]
        for msg in intro_messages:
            st.session_state.chat_history.append(("🤖", msg))
            with st.chat_message("assistant"):
                st.markdown(msg)
            time.sleep(0.3)

        st.session_state.messages.append({"role": "system", "content": load_prompt("prompts/preferences.txt")})

        with st.spinner("🤖 Twinbot is typing now..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=st.session_state.messages,
                    temperature=1,
                    max_tokens=2048
                )
                first_reply = response.choices[0].message.content
            except Exception as e:
                first_reply = f"[ERROR] Fail to respond: {e}"

        st.session_state.chat_history.append(("🤖", first_reply))
        st.session_state.messages.append({"role": "assistant", "content": first_reply})
        with st.chat_message("assistant"):
            st.markdown(first_reply)

        st.session_state.intro_done = True
        st.rerun()

    # ✅ 기존 메시지 출력
    for speaker, msg in st.session_state.chat_history:
        with st.chat_message("user" if speaker == "👤" else "assistant"):
            st.markdown(msg)

    # ✅ 사용자 입력 감지
    user_input = st.chat_input("Enter your message")
    if user_input:
        st.session_state.pending_user_input = user_input
        st.rerun()

    # ✅ 사용자 입력 처리
    if st.session_state.pending_user_input and not st.session_state.awaiting_response:
        msg = st.session_state.pending_user_input
        st.session_state.chat_history.append(("👤", msg))
        st.session_state.messages.append({"role": "user", "content": msg})
        st.session_state.pending_user_input = None
        st.session_state.awaiting_response = True
        st.rerun()

    # ✅ 챗봇 응답 처리
    if st.session_state.awaiting_response:
        with st.spinner("🤖 Twinbot is typing now..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=st.session_state.messages,
                    temperature=1,
                    max_tokens=2048
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"[ERROR] Fail to respond: {e}"

        st.session_state.chat_history.append(("🤖", reply))
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.awaiting_response = False
        st.rerun()

    # ✅ 단계 전환 감지 및 처리
    if st.session_state.interview_phase == "likes":
        if any(LIKE_END in m["content"] for m in st.session_state.messages if m["role"] == "assistant"):
            st.session_state.messages_likes = st.session_state.messages.copy()
            st.session_state.messages = [{"role": "system", "content": load_prompt("prompts/preferences.txt")}]
            st.session_state.chat_history.append(("🤖", "Now let’s move on to things you dislike."))
            st.session_state.interview_phase = "dislikes"
            st.rerun()

    elif st.session_state.interview_phase == "dislikes":
        if any(DISLIKE_END in m["content"] for m in st.session_state.messages if m["role"] == "assistant"):
            st.session_state.messages_dislikes = st.session_state.messages.copy()
            st.session_state.interview_phase = "next_button"
            st.rerun()

    elif st.session_state.interview_phase == "next_button":
        if st.button("다음 주제로"):
            st.session_state.interview_phase = "weekly"
            st.session_state.messages = [{"role": "system", "content": load_prompt("prompts/weekly.txt")}]
            st.session_state.chat_history.append(("🤖", "Great! Let’s talk about your weekly activities."))
            st.rerun()

    elif st.session_state.interview_phase == "weekly":
        if any(WEEKLY_END in m["content"] for m in st.session_state.messages if m["role"] == "assistant"):
            st.session_state.messages_weekly = st.session_state.messages.copy()
            st.session_state.interview_phase = "done"
            st.rerun()

    elif st.session_state.interview_phase == "done":
        with st.chat_message("assistant"):
            st.markdown("""
            이제 도플갱어 챗봇과의 대화를 시작할 수 있어요!  
            👉 [다음 실험 단계로 이동](#)
            """)

        st.header("📆 인터뷰 결과 미리보기")
        for label, key in [
            ("좋아하는 것", "messages_likes"),
            ("싫어하는 것", "messages_dislikes"),
            ("주간 활동", "messages_weekly")
        ]:
            st.subheader(f"🔹 {label}")
            for msg in st.session_state.get(key, []):
                role = "🧍‍♀️" if msg["role"] == "user" else "🤖"
                st.markdown(f"{role} **{msg['role']}**: {msg['content']}")

        st.stop()
