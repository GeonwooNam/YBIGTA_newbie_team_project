import os
import streamlit as st
from langchain_upstage import ChatUpstage


def _get_api_key() -> str:
    try:
        return st.secrets["UPSTAGE_API_KEY"]
    except (KeyError, FileNotFoundError):
        key = os.getenv("UPSTAGE_API_KEY", "")
        if not key:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")
        return key


def get_llm() -> ChatUpstage:
    return ChatUpstage(model="solar-mini", api_key=_get_api_key())
