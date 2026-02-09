from langgraph.graph import StateGraph, END

from st_app.rag.llm import get_llm
from st_app.rag.prompt import ROUTER_PROMPT
from st_app.utils.state import GraphState
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node

VALID_ROUTES = {"chat", "subject_info", "rag_review"}


def router_node(state: GraphState) -> dict:
    llm = get_llm()
    chain = ROUTER_PROMPT | llm
    result = chain.invoke({"question": state["user_input"]})
    route = result.content.strip().lower()
    if route not in VALID_ROUTES:
        route = "chat"
    return {"route": route}


def route_decision(state: GraphState) -> str:
    return state["route"]


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("router", router_node)
    graph.add_node("chat", chat_node)
    graph.add_node("subject_info", subject_info_node)
    graph.add_node("rag_review", rag_review_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "chat": "chat",
            "subject_info": "subject_info",
            "rag_review": "rag_review",
        },
    )

    graph.add_edge("chat", END)
    graph.add_edge("subject_info", END)
    graph.add_edge("rag_review", END)

    return graph.compile()
