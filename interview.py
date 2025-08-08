import streamlit as st
from openai import OpenAI
import time
from oauth2client.service_account import ServiceAccountCredentials
import gspread

LIKE_END = "Thank you for sharing all these details."
DISLIKE_END = "Thank you so much for your detailed answers. This really helps Twinbot understand you better!"
WEEKLY_END = "I now have a good picture of your week."

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

from google.oauth2.service_account import Credentials
import gspread

def save_to_sheet():
    try:
        # 인증 및 시트 열기
        creds = Credentials.from_service_account_info(st.secrets["google"])
        client = gspread.authorize(creds)
        sheet = client.open("internal_knowledge").sheet1

        # 🔁 헤더에서 열 이름 기준으로 인덱스 찾기
        headers = sheet.row_values(1)
        name_col_index = headers.index("Name") + 1  # 사용자 ID가 저장된 열
        id_column = sheet.col_values(name_col_index)

        # 🧍 사용자 ID 확인 및 행 찾기
        user_id = st.session_state.get("user_id", None)
        if user_id is None:
            st.warning("❗ 사용자 ID가 설정되지 않았습니다.")
            return

        if user_id not in id_column:
            st.warning(f"❗ ID '{user_id}'를 시트에서 찾을 수 없습니다.")
            return

        row_idx = id_column.index(user_id) + 1

        # 💬 메시지 압축
        def extract_content(key):
            messages = st.session_state.get(key, [])
            return "\n".join([
                f"{'👤' if m['role'] == 'user' else '🤖'} {m['content']}"
                for m in messages if m["role"] in ["user", "assistant"]
            ])

        likes_text = extract_content("messages_likes")
        dislikes_text = extract_content("messages_dislikes")
        weekly_text = extract_content("messages_weekly")

        # ✍️ 각 열 위치 찾기
        love_col = headers.index("top5_love") + 1
        hate_col = headers.index("top5_hate") + 1
        weekly_col = headers.index("weekly_activities") + 1

        # 📤 시트에 쓰기
        sheet.update_cell(row_idx, love_col, likes_text)
        sheet.update_cell(row_idx, hate_col, dislikes_text)
        sheet.update_cell(row_idx, weekly_col, weekly_text)

        st.success("✅ 인터뷰 결과가 Google Sheet에 저장되었습니다!")

    except Exception as e:
        st.error(f"❌ Google Sheet 저장 중 오류 발생: {e}")

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

        st.session_state.messages.append({"role": "system", "content": load_prompt("prompts/likes.txt")})

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
            st.session_state.messages = [{"role": "system", "content": load_prompt("prompts/dislikes.txt")}]
            st.session_state.chat_history.append(("🤖", "Now let’s move on to things you dislike. Ready?"))
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
            st.session_state.chat_history.append(("🤖", "Great! Let’s talk about your weekly activities. Good to go?"))
            st.rerun()

    elif st.session_state.interview_phase == "weekly":
        if any(WEEKLY_END in m["content"] for m in st.session_state.messages if m["role"] == "assistant"):
            st.session_state.messages_weekly = st.session_state.messages.copy()
            st.session_state.interview_phase = "done"
            st.rerun()

    elif st.session_state.interview_phase == "done":
        save_to_sheet()  # 🔥 대화 종료 시 자동 저장 실행

        with st.chat_message("assistant"):
            st.markdown("""
            이제 도플갱어 챗봇과의 대화를 시작할 수 있어요!  
            👉 [다음 실험 단계로 이동](#)
            """)
        st.stop()
