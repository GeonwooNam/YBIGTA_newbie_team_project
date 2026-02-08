from st_app.rag.llm import get_llm
from st_app.rag.prompt import CHAT_PROMPT
from st_app.utils.state import GraphState


def chat_node(state: GraphState) -> dict:
    llm = get_llm()
    chain = CHAT_PROMPT | llm
    result = chain.invoke({"question": state["user_input"]})
    return {"response": result.content}
