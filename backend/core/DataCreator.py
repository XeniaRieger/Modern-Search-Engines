import streamlit as st
from DatasetEntry import DatasetEntry 
import os
import hashlib
from DocumentIndex import *
print_status = False

@st.cache_data
def create_folder_structure(path:str) -> str: 
    evaluation_folder = os.path.join(path, "dataset")
    if (not os.path.exists(evaluation_folder)):
        os.makedirs(evaluation_folder)
    return evaluation_folder

@st.cache_resource
def load_document_index():
    return DocumentIndex.load(os.path.join(parent_path, "serialization", "index.pickle"))

@st.cache_data
def search_results(query:str, k:int) -> list[str]:
    engines = st.session_state["engines"]
    results = []
    if engines["tf_idf"]:
        results.extend(index.retrieve(query, k))
    if engines["BM25"]:
        results.extend(index.retrieve_bm25(query, k))
    if engines["LLM"]:
        pass  #TODO: fill LLM model

    duplicate_free=[]
    urls = list(set([res.get("url") for res in results]))
    for res in results:
        if res.get("url") in urls:
            duplicate_free.append(res)
            urls.remove(res.get("url"))
    return duplicate_free

@st.cache_resource
def get_docs(urls:list[str]):
    docs = []
    for url in urls:
        try:
            docs.append(Document.Document(url))
        except:
            docs.append({"description":None, "last_modified":None, "raw_text":None})
            st.error("Document not retrievable (e.g due to timeout)")
    return docs

@st.cache_resource
def get_all_entries(evaluation_folder:str) ->list[DatasetEntry]:
    dataset = []
    for file in os.listdir(evaluation_folder):
        with open(str(evaluation_folder +"/" + file), 'rb') as f:
            dataset.append(pickle.load(f))
    return dataset

def get_least_ranked_entry(evaluation_folder:str) ->DatasetEntry:
    dataset=get_all_entries(evaluation_folder)
    min = float("inf")
    dat = None
    for d in dataset:
        if min > d.number_ranked:
            min = d.number_ranked
            dat = d
    return dat

def save_entry(evalaution_folder:str):
    query = st.session_state["query"]
    results = st.session_state["result"]
    ranking = [1 if rank else -1 for rank in list(st.session_state.ranking.values())]   # rank -1 for irrelevant results and 1 for relevant
    engines = [model for model in ["tf_idf", "BM25", "LLM"] if st.session_state.get(model)]
    query_name = str(int(hashlib.md5(query.encode('utf-8')).hexdigest(), 16))
    entry = DatasetEntry(name=query_name, query=query, results=results, ranking=ranking, engines=engines) 
    entry.save(evalaution_folder)

def initialize(force:bool=False):
    if st.session_state == {} or force:
        st.session_state.update({
            "role":None,
            "subrole":None,
            "query":None,
            "k":None,
            "result":None,
            "ranking":None,
            "engines":None
        })

def change_session_state(**new_state:dict[str]):
    st.session_state.update(new_state)


parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
evaluation_folder = create_folder_structure(parent_path)
index = load_document_index()
if __name__ == '__main__':
    initialize()
    if st.session_state.role == "create_query":
        if st.session_state.subrole == "create":
            pg = st.navigation([st.Page("pages/CreateQuery.py")])

        if st.session_state.subrole == "rank":
            results = search_results(st.session_state["query"], st.session_state["k"])
            #results = list(dict.fromkeys(results)) # filter duplicates

            if len(results) <= 0:
                st.error("Query did not return any results")
                if st.button("Stop"):
                    initialize(force=True)
                    st.rerun()
                if st.button("Retry"):
                    change_session_state(role="create_query", subrole="create", query=None)
                    st.rerun()
            else:
                st.session_state["result"] = results
                pg = st.navigation([st.Page("pages/RankQuery.py")])

        if st.session_state.subrole == "save":
            save_entry(evaluation_folder)
            initialize(force=True)
            change_session_state(subrole="create", role="create_query")
            st.rerun()
    
    if st.session_state.role == "rerank":
        if st.session_state.subrole == "rerank":
            d = get_least_ranked_entry(evaluation_folder)
            change_session_state(query=d.query, result=d.results, entry=d)
            pg = st.navigation([st.Page("pages/Rerank.py")])

        if st.session_state.subrole == "save":
            d = st.session_state.entry
            ranking = [1 if rank else -1 for rank in list(st.session_state.ranking.values())] 
            d.rerank(ranking)
            d.save(evaluation_folder)
            initialize(force=True)
            change_session_state(subrole="rerank", role="rerank")
            st.rerun()

    if st.session_state.role == "evaluate":
        pg = st.navigation([st.Page("pages/EvaluatePage.py")])
   
    if st.session_state.role == None:
        pg = st.navigation([st.Page("pages/start_page.py")])
    
    pg.run()


