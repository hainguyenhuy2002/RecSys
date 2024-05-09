import string
import re

def remove_date(text):
    patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2}\b',  
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b\d{2}[/-]\d{1,2}[/-]\d{1,2}\b',  
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}\b',  
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}\b', 
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b',  
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b'  
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text

def remove_url(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub(r'', text)

def remove_special_chars(s):
    remove_chars = string.punctuation.replace('.','')
    table = str.maketrans('', '', remove_chars)
    return s.translate(table)

def remove_emojis(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')

def remove_dotspace(s):
    return s.split('. ')

def remove_rt(text):
    pattern = r'\brt\b'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text



def remove_dotts(text):
    # Define the patterns
    patterns = [r'(?<!\w)\.\.\.(?!\w)', r'(?<!\w)\.\.(?!\w)', r'(?<!\w)\.(?!\w)']
    
    # Replace the patterns with an empty string
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    
    return text

def filter_keywords(list_of_keywords):
    if len(list_of_keywords)> 10:
        return list_of_keywords[:8]
    else:
        return list_of_keywords
    
def preprocess_tweet(df):
    df['keyWords'] = df['keyWords'].apply(filter_keywords)
    df_tweets = df.explode('keyWords')
    df_tweets['keyWordsClean'] =df_tweets.keyWords.apply(remove_url)
    df_tweets['keyWordsClean'] =df_tweets.keyWordsClean.apply(remove_rt)
    df_tweets['keyWordsClean'] = df_tweets.keyWordsClean.apply(remove_emojis)
    df_tweets['keyWordsClean'] = df_tweets.keyWordsClean.apply(remove_date)
    df_tweets['keyWordsClean'] = df_tweets.keyWordsClean.apply(remove_special_chars)
    df_tweets['keyWordsClean'] = df_tweets.keyWordsClean.apply(remove_dotspace)
    df_tweets_filter = df_tweets.explode('keyWordsClean')
    df_tweets_filter['keyWordsClean'] = df_tweets_filter.keyWordsClean.apply(remove_dotts)
    df_tweets_filter = df_tweets_filter[df_tweets_filter['keyWordsClean'].apply(lambda x: x.strip())!='']
    df_tweets_filter['keyWordsClean'] = df_tweets_filter['keyWordsClean'].apply(lambda x: re.sub(r'\s+', ' ', x).strip())
    df_tweets_filter['count']=1
    return df_tweets_filter