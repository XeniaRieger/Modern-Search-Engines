from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pickle
import os


# we have to define a custom unpickler because the index pickle file was created inside the DocumentIndex file
class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'DocumentIndex' or name == "create_int_defaultdict" or name == "create_float_defaultdict":
            from backend.core.DocumentIndex import DocumentIndex
            return DocumentIndex
        return super().find_class(module, name)


def unpickle_document_index(path):
    with open(path, 'rb') as f:
        return CustomUnpickler(f).load()


path = os.path.join(os.path.dirname(os.path.normpath(os.getcwd())), "serialization", "index.pickle")
document_index = unpickle_document_index(path)
print(f"loaded index with {document_index.total_documents} documents")


@csrf_exempt
def search(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            docs = document_index.retrieve_bm25(query, top_k=100)
            return JsonResponse(docs, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
