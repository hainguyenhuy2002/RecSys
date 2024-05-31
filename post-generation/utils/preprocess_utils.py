import pandas as pd
import numpy as np
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

def get_lemma(paragraph):
  sentences = nltk.sent_tokenize(paragraph)
  lemmatizer = WordNetLemmatizer()
  # Lemmatization
  for i in range(len(sentences)):
      words = nltk.word_tokenize(sentences[i])
      words = [lemmatizer.lemmatize(word) for word in words if word not in set(stopwords.words('english'))]
      sentences[i] = ' '.join(words)

  return ' '.join(sentences)
