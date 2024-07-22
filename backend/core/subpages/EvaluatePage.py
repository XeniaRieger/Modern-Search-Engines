import streamlit as st
from DataCreator import change_session_state, initialize, print_status, evaluation_folder, index
from DatasetEntry import *
import pandas as pd
import math
import time
from ReRanker import ReRanker 

if print_status:
    print("evaluating")
    print("session_state", st.session_state)

@st.cache_data
def get_all_entries(evaluation_folder:str) ->list[DatasetEntry]:
    dataset = []
    for file in os.listdir(evaluation_folder):
        with open(str(evaluation_folder +"/" + file), 'rb') as f:
            dataset.append(pickle.load(f))
    return dataset

@st.cache_data
def calculate_MRR(model_results, gt_results):
    i = 1
    for res in model_results:
        if res in gt_results:
            return 1/i
        i += 1
    return 0

@st.cache_data
def calculate_DCG(model_results, gt_results):
    DCG = 0
    IDCG = 0
    for n in range(1, len(model_results)+1):
        if model_results[n-1] in gt_results:
            gain =  1 / math.log2(n + 1)
            DCG += gain

    for j in range(1, len(gt_results)+1):
        IDCG += 1/math.log2(j+1)
    return DCG / IDCG

@st.cache_data
def calculate_MAP(model_results, gt_results):
    rel_at_n = 0
    precision = 0
    for n in range(1, len(model_results)+1):
        if model_results[n-1] in gt_results:
            rel_at_n += 1
            precision += rel_at_n/n
    return precision / len(gt_results)

@st.cache_data
def search_results_per_model(m, query:str, k:int) -> list[str]:
    if m == "tf-idf":
        return index.retrieve_tfidf(query, k)
    if m == "BM25":
        print("retrieve BM25")
        return index.retrieve_bm25(query, k)
    if m == "BM25_rerank":
        ranker.rank_documents(original_ranking=index.retrieve_bm25(query, k), topic_threshhold=0.5, 
                                       relevance_importance=st.session_state.get("relevance"), consider=10)
    if m == "tf-idf_rerank":
        return ranker.rank_documents(original_ranking=index.retrieve_tfidf(query, k), topic_threshhold=0.5, 
                                       relevance_importance=st.session_state.get("relevance"), consider=10)
    return []  
 
@st.cache_resource
def load_ranker():
    return ReRanker() 

with st.form("evaluate"):
    models = st.multiselect("Which retrieval models would you like to evaluate and compare?", ("tf-idf", "BM25", "BM25_rerank", "tf-idf_rerank"))
    relevance = st.slider("Diversity Value for reranking", min_value=0.0, max_value=1.0, value=0.5)
    default_value=10

    with st.container():
        if st.session_state.get("for_all"):
            default_value = st.session_state.get("set_all_val")

        NDCG = st.checkbox("NDCG", value=True)
        NDCG_value = st.slider("NDCG@ with value", min_value=1, max_value=15, value=default_value)
        MRR=st.checkbox("MRR@", value=True)
        MRR_value = st.slider("MRR@ with value", min_value=1, max_value=15, value=default_value)
        MAP = st.checkbox("MAP", value=True)
        MAP_value = st.slider("MAP@ with value", min_value=1, max_value=15, value=default_value)

        for_all = st.toggle("use one value for all")
        set_all_val = st.number_input("Set value for all selected", min_value=1, max_value=13, value=10, step=1)
        run_time=st.checkbox("retrieval time", value=True)
    if st.form_submit_button("Ok"):
        if for_all:
            MRR_val = set_all_val
            NDCG_val = set_all_val
            MAP_val = set_all_val
            change_session_state(models=models, metrics={"MRR": MRR, "NDCG":NDCG, "runtime":run_time, "MAP":MAP},
                                k_values = {"MRR": MRR_value, "NDCG":NDCG_value, "MAP":MAP_value}, set_all_val=set_all_val, for_all=for_all,
                                relevance=relevance)
        else:
            change_session_state(models=models, metrics={"MRR": MRR, "NDCG":NDCG, "runtime":run_time, "MAP":MAP},
                    k_values = {"MRR": MRR_value, "NDCG":NDCG_value, "MAP":MAP_value}, set_all_val=None, for_all=for_all,
                    relevance=relevance)
        st.rerun()

st.button("Cancel", on_click=initialize, args=[True])   

if st.session_state.get("metrics"):
    dataset=get_all_entries(evaluation_folder)
    n = len(dataset)

    if ("tf-idf_rerank" in st.session_state.models or "BM25_rerank" in st.session_state.models):
        ranker = load_ranker()
    print(st.session_state)
    MRR_val = st.session_state.k_values["MRR"]
    NDCG_val = st.session_state.k_values["NDCG"]
    MAP_val = st.session_state.k_values["MAP"]

    if st.session_state.for_all:    
        k = st.session_state.set_all_val
        #MRR_val = k
        #NDCG_val = k
        #MAP_val = k
    else:
        #k = max(st.session_state.get("metrics").values())
        k = max(MRR_val, NDCG_val, MAP_val)
    
    res = {"idx":[], "model":[], "MRR":[], "NDCG":[], "MAP":[]}
    retrieval_time = {"model":[], "time":[]}

    # iterate over models
        # iterate over all collected datapoint
            # retrieve documents for each model for each query
            # calculate the metrics
        # mean over all queries

    for m in st.session_state.models:
        r_time = 0
        idx = 0
        for d in dataset:
            start_time = time.time()
            m_results =  search_results_per_model(m, d.query, k)
            r_time += (time.time() - start_time)
            model_results = [x.get("url") for x in m_results]
            gt_results = d.relevant_results
            if len(gt_results) <= 0:
                continue
            RR = calculate_MRR(model_results[:MRR_value], gt_results)
            NDCG = calculate_DCG(model_results[:NDCG_value], gt_results) 
            MAP = calculate_MAP(model_results[:MAP_value], gt_results)
            res["idx"].append(idx)
            res["model"].append(m)
            res["MRR"].append(RR)
            res["NDCG"].append(NDCG)
            res["MAP"].append(MAP)
            idx += 1
        retrieval_time["model"].append(m)
        retrieval_time["time"].append(r_time/n)

    df1 = pd.DataFrame(res)
    df_time = pd.DataFrame(retrieval_time)
    means = df1.groupby(["model"]).mean().rename(columns={'MRR':'MRR_mean', 'NDCG':'NDCG_mean', 'MAP':'MAP_mean'})
    var = df1.groupby(["model"]).var().rename(columns={'MRR':'MRR_var', 'NDCG':'NDCG_var', 'MAP':'MAP_var'})

    df2 = means
    df2[["MRR_var"]] = var[["MRR_var"]]
    df2[["NDCG_var"]] = var[["NDCG_var"]]
    df2[["MAP_var"]] = var[["MAP_var"]]
 
    if st.session_state.metrics.get("MRR"):
        with st.container(height=650, border=True):
            st.subheader(f"MMR@{MRR_val} for retrieval models {models} over {n} queries")
            st.dataframe(means[["MRR_mean", "MRR_var"]])
            st.bar_chart(means, y="MRR_mean", use_container_width=False, width=len(models)*150)
            st.line_chart(df1, x="idx", y="MRR", color="model")
    
    if st.session_state.metrics.get("NDCG"):
        with st.container(height=650, border=True):
            st.subheader(f"NDCG@{NDCG_val} for retrieval models {models} over {n} queries")
            st.dataframe(means[["NDCG_mean", "MRR_var"]])
            st.bar_chart(means, y="NDCG_mean", use_container_width=False, width=len(models)*150)
            st.line_chart(df1,  x="idx", y ="NDCG", color="model")

    if st.session_state.metrics.get("MAP"):
        with st.container(height=650, border=True):
            st.subheader(f"MAP@{MAP_val} for retrieval models {models} over {n} queries")
            st.dataframe(means[["MAP_mean", "MAP_var"]])
            st.bar_chart(means, y="MAP_mean", use_container_width=False, width=len(models)*150)
            st.line_chart(df1,  x="idx", y ="MAP", color="model")
    
    if st.session_state.metrics.get("runtime"):
        with st.container(height=200, border=True):
            st.subheader(f"Mean retrieval time for retrieval models {models} over {n} queries each with {k} results")
            st.dataframe(df_time)