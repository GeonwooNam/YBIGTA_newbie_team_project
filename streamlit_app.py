import streamlit as st
from st_app.graph.router import build_graph

st.set_page_config(page_title="에버랜드 챗봇", page_icon="🎢")
st.title("🎢 에버랜드 챗봇")
st.caption("에버랜드에 대해 무엇이든 물어보세요! (정보, 리뷰, 일반 대화)")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

ROUTE_LABELS = {
    "subject_info": "에버랜드 정보",
    "rag_review": "리뷰 기반 답변",
    "chat": "일반 대화",
}

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "route" in msg:
            st.caption(f"질문 분류: **{ROUTE_LABELS.get(msg['route'], msg['route'])}**")
        st.markdown(msg["content"])
        if msg.get("retrieved_reviews"):
            with st.expander("검색된 리뷰 정보"):
                for review in msg["retrieved_reviews"]:
                    st.markdown(f"- {review}")

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
                "retrieved_reviews": [],
            })
            response = result["response"]
            route = result["route"]
            retrieved_reviews = result.get("retrieved_reviews", [])

        st.caption(f"질문 분류: **{ROUTE_LABELS.get(route, route)}**")
        st.markdown(response)

        if retrieved_reviews:
            with st.expander("검색된 리뷰 정보"):
                for review in retrieved_reviews:
                    st.markdown(f"- {review}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "route": route,
        "retrieved_reviews": retrieved_reviews,
    })
