from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pickle
import os

# we have to define a custom unpickler because the index pickle file was created inside the DocumentIndex file
from api.Summarizer import generate_batch_summary, generate_summary


class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'DocumentIndex' or name == "create_int_defaultdict" or name == "create_float_defaultdict":
            from backend.core.DocumentIndex import DocumentIndex
            return DocumentIndex
        return super().find_class(module, name)


def unpickle_document_index(path):
    with open(path, 'rb') as f:
        return CustomUnpickler(f).load()


print("loading index...")
path = os.path.join(os.path.dirname(os.path.normpath(os.getcwd())), "serialization", "index.pickle")
document_index = unpickle_document_index(path)
print(f"loaded index with {document_index.total_documents} documents")


@csrf_exempt
def search(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            top_k = int(data.get('top_k', 20))
            docs = document_index.retrieve_bm25(query, top_k=top_k)
            for d in docs:
                del d['raw_text']
            # generate_batch_summary(docs)
            return JsonResponse(docs, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def summarize(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url_hash = data.get('url_hash', '')
            if url_hash:
                parent_path = os.path.dirname(os.path.normpath(os.getcwd()))
                documents_path = os.path.join(parent_path, "serialization", "documents", "pickle")
                doc_path = os.path.join(documents_path, url_hash + ".pickle")
                if not os.path.exists(doc_path):
                    return JsonResponse({'error': 'Document not found'}, status=404)

                with open(doc_path, 'rb') as f:
                    doc = pickle.load(f)

                summary = generate_summary(doc.raw_text)
                return JsonResponse({"summary": summary}, safe=False)
            else:
                return JsonResponse({'error': 'Document not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)