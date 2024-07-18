from pyterrier_doc2query import Doc2Query, QueryScorer, QueryFilter
from pyterrier_dr import ElectraScorer
import pandas as pd
from Tokenizer import tokenize

doc2query = Doc2Query(num_samples=8, fast_tokenizer=True)
scorer = QueryScorer(ElectraScorer(verbose=False))
filterer = QueryFilter(t=0.1234, append=False)

def doc_2_query_minus(docs, ngrams):
    df = pd.DataFrame([{"docno": d.url_hash, "text": d.raw_text} for d in docs])
    pipeline = doc2query >> scorer >> filterer
    res = pipeline.transform(df)

    for index, row in res.iterrows():
        doc = next(d for d in docs if d.url_hash == row['docno'])
        doc.single_tokens.extend(tokenize(row['querygen'], ngrams))
