import streamlit as st
from st_app.graph.router import build_graph

st.set_page_config(page_title="에버랜드 챗봇", page_icon="🎢")
st.title("🎢 에버랜드 챗봇")
st.caption("에버랜드에 대해 무엇이든 물어보세요! (정보, 리뷰, 일반 대화)")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            result = st.session_state.graph.invoke({
                "user_input": prompt,
                "chat_history": st.session_state.messages,
                "route": "",
                "response": "",
            })
            response = result["response"]
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
