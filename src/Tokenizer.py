import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from pyterrier_doc2query import Doc2Query, QueryScorer, QueryFilter
from pyterrier_dr import ElectraScorer
import pandas as pd
import numpy as np
import math


# nltk.download('words')
# nltk.download('stopwords')
# nltk.download('punkt')
# nltk.download('wordnet')
# nltk.download('omw-1.4')


doc2query = Doc2Query(num_samples=10, fast_tokenizer=True)
scorer = QueryScorer(ElectraScorer(verbose=False))
filterer = QueryFilter(t=0, append=False)

lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')


def tokenize(text: str, ngrams=1):
    tokens = nltk.tokenize.word_tokenize(text)
    cleaned_tokens = [lemmatizer.lemmatize(t).lower() for t in tokens if t.isalnum() and t not in stopwords]
    if ngrams > 1:
        return [" ".join(t) for t in nltk.ngrams(cleaned_tokens, ngrams)]

    return cleaned_tokens

def doc_2_query_minus(doc: str):
    tokenized = doc.split()
    # generate queries from sequenced document 
    seq_length=400
    n = math.ceil(len(tokenized)/seq_length)
    for i in range(0, n):
        end = (i+1)*seq_length if (i+1)*seq_length < len(tokenized) else len(tokenized)
        sequence = " ".join(tokenized[i*seq_length:end])
        expanded = doc2query.transform(pd.DataFrame([{"text": sequence}]))
        relevant = filter_relevant_docs(expanded)
        doc = doc + " " + " ".join(relevant)
    return doc

def filter_relevant_docs(expanded: pd.DataFrame):
    # score generated queries
    score = scorer.transform(expanded)

    # filter for relevant queries
    filter = filterer.transform(score)
    return filter["querygen"].str.split("\n")[0]


def filter(filterer, score):
    temp = score["querygen_score"].to_list()[0]
    for _ in range(0, max_add):
        idx = np.argmax(temp, )
        doc = doc + " " + score["querygen"].str.split("\n")[0][idx]
        temp[idx] = float("-inf")
    return doc
