import os
import streamlit as st
from langchain_upstage import ChatUpstage


def get_llm() -> ChatUpstage:
    api_key = st.secrets.get("UPSTAGE_API_KEY") or os.getenv("UPSTAGE_API_KEY")
    return ChatUpstage(model="solar-mini", api_key=api_key)
