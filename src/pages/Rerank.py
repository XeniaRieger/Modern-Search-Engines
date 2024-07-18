import streamlit as st
import streamlit.components.v1 as components
from DataCreator import  change_session_state, initialize, get_docs, print_status

if print_status:
    print("New reranking of query")

st.title("Rerank Documents")
st.header(f"current query: \"{st.session_state.query}\" with {len(st.session_state.result)} results")
st.subheader("Rank the retrieved documents based on ther relevancy for the query ")
results = st.session_state.result
query = st.session_state.query
idx = 0
docs = get_docs(results)

ranking = {}
with st.form("creating_ranking", clear_on_submit=True):
    for url in results:
        doc = docs[idx]
        idx += 1
        st.write(f"**Document Number {idx}**")
        st.write("result", url)
        st.write(f"current query:**{query}**")
        ranking[idx] = st.toggle("Document " + str(idx) + " is relevant", value=False)
        with st.container(height=350, border=True):
            try:
                st.text(str("Last modified: " + doc.last_modified) )
                with st.expander("description"):
                    st.markdown(doc.description)
                with st.expander("page preview"):
                    components.iframe(url, width=650, height=400, scrolling = True)
                with st.expander("all text"):
                    st.markdown(doc.raw_text) 
            except:
                st.error("couldnt find some information, check Link")
    submitted = st.form_submit_button("Submit Ranking")
    if submitted:
        change_session_state(ranking=ranking, subrole="save")
        st.rerun()
st.info("Please ignore any error message after submitting! \n The process is saving and will then start over by itself")
st.button("Cancel", on_click=initialize, args=[True])  