import streamlit as st
from DataCreator import initialize, change_session_state, print_status

if print_status:
    print("Create a new query")

with st.form("creating_query"):
    query = st.text_input("Enter a query")
    k = st.slider("Amount of websites to retrieve", min_value=1, max_value=100, value=15)
    st.text("Select models to retrieve documents for the ranking pool: ")
    tf_idf = st.checkbox("use tf-idf", value=True, key="tf_idf")
    BM25 = st.checkbox("use bm25", value=True, key="BM25")
    LLM = st.checkbox("use a LLM", value=True, key="LLM")
    submit = st.form_submit_button("OK")
    if submit:
        change_session_state(subrole="rank", query=query, k=k, engines={"tf_idf":tf_idf, "BM25":BM25, "LLM":LLM})
        print(st.session_state)
        st.rerun()
st.button("Cancel", on_click=initialize, args=[True])   

