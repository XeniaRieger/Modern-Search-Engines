import sys

from DocumentIndex import *
from ReRanker import ReRanker


def load_index():
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    return DocumentIndex.load(os.path.join(parent_path, "serialization", "index.pickle"))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("You have to provide the query path and save file path")
        exit(0)

    query_file_path = sys.argv[1]
    save_file_path = sys.argv[2]

    if not os.path.exists(query_file_path):
        print(f"file {query_file_path} does not exist")
        exit(0)

    queries = {}
    with open(query_file_path, "r", encoding="utf-8") as file:
        for line in file:
            line_split = line.split("\t")
            queries[line_split[0]] = line_split[1].strip()

    index = load_index()
    re_ranker = ReRanker()
    open(save_file_path, "w").close() # make file empty
    for query_num, query_term in queries.items():
        docs = index.retrieve_bm25(query_term, top_k=100)
        docs = re_ranker.rank_documents(docs, relevance_importance=0.9, consider=len(docs))
        result = enumerate(docs)
        with open(save_file_path, "a", encoding="utf-8") as file:
            for i, doc in result:
                file.write(f"{query_num}\t{i+1}\t{doc['url']}\t{doc['score']}\n")
