import time

from DocumentIndex import *
from BM25Ranker import BM25Ranker


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == '__main__':
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    index_path = os.path.join(serialisation_folder, "index.pickle")
    doc_index = load_pickle(index_path)

    bm25 = BM25Ranker(doc_index)
    start_time = time.time()
    print(bm25.search("weather"))
    print(bm25.search("tübingen"))
    print(bm25.search("lustnau"))
    print(bm25.search("restaurant boat trip"))
    print(bm25.search("restaurant boat trip"))
    print(bm25.search("restaurant boat trip"))
    print(bm25.search("restaurant boat trip germany"))
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time

    print(f"Time taken: {elapsed_time} seconds")