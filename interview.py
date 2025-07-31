import streamlit as st
from openai import OpenAI

# 고정된 종료 문장
LIKE_END = "Thank you for sharing all these details."
DISLIKE_END = "Thank you so much for your detailed answers. This really helps Twinbot understand you better!"
WEEKLY_END = "Thank you for your detailed answers. Now I have a good picture of your past week. This will really help Twinbot understand you better!"

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def run():
    st.title("🧠 AITwinBot 인터뷰")

    # 단계 초기화
    if "interview_phase" not in st.session_state:
        st.session_state.interview_phase = "likes"
        st.session_state.messages = [{"role": "system", "content": load_prompt("prompts/preferences.txt")}]

    # 클라이언트 연결
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])

    # 채팅 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 입력
    if user_input := st.chat_input("메시지를 입력해주세요."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        # GPT 호출
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=st.session_state.messages,
            temperature=1,
            max_tokens=2048
        )
        reply = response.choices[0].message.content.strip()
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # 종료 감지 및 다음 단계 전환
    if st.session_state.interview_phase == "likes":
        if any(LIKE_END in m["content"] for m in st.session_state.messages if m["role"] == "assistant"):
            st.session_state.messages_likes = st.session_state.messages.copy()
            st.session_state.messages = [{"role": "system", "content": load_prompt("prompts/preferences.txt")}]
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

        st.header("📦 인터뷰 결과 미리보기")
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
