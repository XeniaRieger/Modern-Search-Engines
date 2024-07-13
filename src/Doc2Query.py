from pyterrier_doc2query import Doc2Query, QueryScorer, QueryFilter
from pyterrier_dr import ElectraScorer
import pandas as pd
import numpy as np
import math
import Document

doc2query = Doc2Query(num_samples=10, fast_tokenizer=True)
scorer = QueryScorer(ElectraScorer(verbose=False))
filterer = QueryFilter(t=0, append=False)


def doc_2_query_minus(doc: Document):
    # generate queries from sequenced document
    tokens = doc.raw_text.split()
    seq_length = 400
    n = math.ceil(len(tokens)/seq_length)
    query = ""
    for i in range(0, n):
        end = (i + 1) * seq_length if (i + 1) * seq_length < len(tokens) else len(tokens)
        sequence = " ".join(tokens[i * seq_length:end])
        expanded = doc2query.transform(pd.DataFrame([{"text": sequence}]))
        relevant = filter_relevant_docs(expanded)
        query += " " + " ".join(relevant)
    return query.split()


def filter_relevant_docs(expanded: pd.DataFrame):
    # score generated queries
    score = scorer.transform(expanded)

    # filter for relevant queries
    filter = filterer.transform(score)
    return filter["querygen"].str.split("\n")[0]


# def filter(filterer, score):
#     temp = score["querygen_score"].to_list()[0]
#     for _ in range(0, max_add):
#         idx = np.argmax(temp, )
#         doc = doc + " " + score["querygen"].str.split("\n")[0][idx]
#         temp[idx] = float("-inf")
#     return doc

