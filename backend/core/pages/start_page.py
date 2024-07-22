import streamlit as st
from DataCreator import  change_session_state, print_status

if print_status:
    print("Create a new main page")
    
st.title("What would you like to do?")
st.button("Create a new query", on_click=change_session_state, kwargs={"role":"create_query", "subrole":"create"})
st.button("Rerank existing  query", on_click=change_session_state, kwargs={"role":"rerank", "subrole":"rerank"})
st.button("Evaluate a retrieval model", on_click=change_session_state, kwargs={"role":"evaluate"})

