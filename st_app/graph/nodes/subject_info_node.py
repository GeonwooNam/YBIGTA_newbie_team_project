import json
import os

from st_app.rag.llm import get_llm
from st_app.rag.prompt import SUBJECT_INFO_PROMPT
from st_app.utils.state import GraphState

SUBJECTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "subject_information", "subjects.json",
)


def _load_subject_info() -> str:
    with open(SUBJECTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False, indent=2)


def subject_info_node(state: GraphState) -> dict:
    llm = get_llm()
    info_text = _load_subject_info()
    chain = SUBJECT_INFO_PROMPT | llm
    result = chain.invoke({"subject_info": info_text, "question": state["user_input"]})
    return {"response": result.content}
