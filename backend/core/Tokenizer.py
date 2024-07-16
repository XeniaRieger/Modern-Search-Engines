import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

nltk.download('words')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')


def tokenize(text: str, ngrams=1):
    text = text.lower().replace("tuebingen", "tübingen").replace("tubingen", "tübingen").replace("tübinger", "tübingen")
    tokens = nltk.tokenize.word_tokenize(text)
    cleaned_tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum() and t not in stopwords]
    if ngrams > 1:
        return [" ".join(t) for t in nltk.ngrams(cleaned_tokens, ngrams)]

    return cleaned_tokens

def tokenize_query(query: str, ngrams=1, max_length_before_ngram=40):
    max_length = max_length_before_ngram
    query = query.lower()
    tokens = nltk.tokenize.word_tokenize(query)
    # try to remove Tübingen because every doc is about tübingen
    try_query = [e for e in tokens if e not in ("tuebingen", "tubingen", "tübingen", "tübinger")]
    if not try_query:
        query = tokens
    else:
        query = try_query
    # try to remove stopwords + lemmatize
    cleaned_tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum() and t not in stopwords]
    if cleaned_tokens:
        query = cleaned_tokens
    else:
        min_clean = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum()]
        if min_clean:
            query = min_clean
        else:
            query = [lemmatizer.lemmatize(t) for t in tokens]
    expanded_query = query.copy()
    i = 0
    for word in query:
        if len(expanded_query) >= max_length:
            break
        # query expansion
        added_syns = []
        for syn in wordnet.synonyms(word)[0]:
            syn_lem = lemmatizer.lemmatize(syn)
            if syn_lem != word:
                expanded_query.insert(i + 1, syn_lem)
                i += 1
        i += 1
    if len(query) > max_length:
        query = query[:max_length]
    if ngrams > 1:
        return [" ".join(t) for t in nltk.ngrams(query, ngrams)]
    return query
