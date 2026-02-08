import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_upstage import UpstageEmbeddings

FAISS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "faiss_index")


@st.cache_resource
def load_retriever(k: int = 5):
    api_key = st.secrets.get("UPSTAGE_API_KEY") or os.getenv("UPSTAGE_API_KEY")
    embeddings = UpstageEmbeddings(model="solar-embedding-1-large", api_key=api_key)
    vectorstore = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    return vectorstore.as_retriever(search_kwargs={"k": k})


def retrieve_reviews(query: str, k: int = 5) -> list:
    retriever = load_retriever(k=k)
    return retriever.invoke(query)
