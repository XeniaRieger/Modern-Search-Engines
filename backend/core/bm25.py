from DocumentIndex import *

if __name__ == '__main__':
    parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
    serialisation_folder = os.path.join(parent_path, "serialization")
    index_path = os.path.join(serialisation_folder, "index.pickle")
    doc_index = DocumentIndex.load(index_path)

    print(doc_index.query_bm25("weather"))
    print(doc_index.query_bm25("tübingen"))
    print(doc_index.query_bm25("lustnau"))
    print(doc_index.query_bm25("restaurant boat trip"))
    print(doc_index.query_bm25("restaurant boat trip"))
    print(doc_index.query_bm25("restaurant boat trip"))
    print(doc_index.query_bm25("restaurant boat trip germany"))


