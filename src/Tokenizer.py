import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# nltk.download('words')
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('omw-1.4')

lemmatizer = WordNetLemmatizer()
stopwords = stopwords.words('english')


def tokenize(tokens: list):
    return [lemmatizer.lemmatize(t).lower() for t in tokens if t.isalnum() and t not in stopwords]
