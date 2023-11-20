import streamlit as st
import os

st.set_page_config(layout="wide", page_title="AutoChecker", page_icon="📄")
with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()
st.markdown(readme, unsafe_allow_html=True)
with open('TOC.md', 'r', encoding='utf-8') as f:
    toc = f.read()
st.sidebar.markdown(toc)
