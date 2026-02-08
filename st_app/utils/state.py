from typing import TypedDict, List


class GraphState(TypedDict):
    user_input: str
    chat_history: List[dict]  # [{"role": "user/assistant", "content": "..."}]
    route: str  # "chat" | "subject_info" | "rag_review"
    response: str
