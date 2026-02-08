from st_app.rag.llm import get_llm
from st_app.rag.prompt import RAG_REVIEW_PROMPT
from st_app.rag.retriever import retrieve_reviews
from st_app.utils.state import GraphState


def rag_review_node(state: GraphState) -> dict:
    docs = retrieve_reviews(state["user_input"])

    context_parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        context_parts.append(
            f"[리뷰 {i}] 플랫폼: {meta.get('platform', '?')}, "
            f"평점: {meta.get('rating', '?')}, "
            f"날짜: {meta.get('date', '?')}\n"
            f"{doc.page_content}"
        )
    context = "\n\n".join(context_parts)

    llm = get_llm()
    chain = RAG_REVIEW_PROMPT | llm
    result = chain.invoke({"context": context, "question": state["user_input"]})
    return {"response": result.content}
