from django.urls import path
from .views import search, summarize

urlpatterns = [
    path('search', search, name='search'),
    path('summarize', summarize, name='summarize'),
]