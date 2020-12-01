from flask import Flask, render_template, url_for, request, redirect, Response
from datetime import datetime
import os
import re
import sys
import pandas as pd
import io
from flask import Flask,render_template, request, send_file
from flask_navigation import Navigation
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import tweepy
from tweepy import OAuthHandler
from skimage.io import imread
import numpy as np
from PIL import Image
import collections
import pandas as pd

IMAGES_FOLDER = os.path.join('static', 'temporary_files')

# Twitter Develepor Cridentials
consumer_key = 'YAtTMCjSCTUpSviE2FDpENdMU'  
consumer_secret="wl6Lbp5Q1neIjnZORoLxB8NSfRHEs4L7IFq7PFxmYhqISCAn15"
access_token = '720827550-fcbS3qyZnMm7c42wymmvh8pu0DWg6RKqpAiQxJBz'
access_token_secret = 'VKocXcAsN0ApaFFOAHJ2XhUKTUH59GmbQ0pHZe13icoKO'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Creating the API
api = tweepy.API(auth,wait_on_rate_limit=True)

def tweets_df(results):
    id_list = [tweet.id for tweet  in results]
    data_set = pd.DataFrame(id_list, columns = ["id"])
    data_set["text"] = [tweet.text for tweet in results]
    data_set["Hashtags"] = [tweet.entities.get('hashtags') for tweet in results]
    return data_set

TWEET_LEN = 140

def check_if_hashtags_are_valid(hashtags):
    if len(hashtags) == 0:
        return False
    else:
        for ht in hashtags:
            if not (0 < len(ht) <= TWEET_LEN) or ht[0] != '#':
                return False
        return True

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = IMAGES_FOLDER

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/', methods=['POST', 'GET'])
def index():
   
    if request.method == 'POST':
        hashtag_name = request.form['hashtag']
        number = request.form['number']
        splitted_hashtags = [ht.strip() for ht in re.split(", ", hashtag_name)]
        if check_if_hashtags_are_valid(splitted_hashtags):
            results = []
            for tweet in tweepy.Cursor (api.search, q = splitted_hashtags, lang = "en").items(int(number)): 
                results.append(tweet)
            data_set = tweets_df(results)
            
            text = data_set["text"]
            for i in range(0,len(text)):
                txt = ' '.join(word for word in text[i] .split() if not word.startswith('https:'))
                data_set.at[i,'text2'] = txt
                data_set.drop_duplicates('text2', inplace=True)
                data_set.reset_index(drop = True, inplace=True)
                data_set.drop('text', axis = 1, inplace = True)
                data_set.rename(columns={'text2': 'text'}, inplace=True)
                
            # Join all the text from the 1000 tweets
            text_Combined = " ".join(text.values.astype(str))
            more_stopwords = {'https', 'RT', 'rt', 'CO', '@', 'el', 't', '&amp;', 'covid','covid 19', '#covid19','tco','covid19', 'amp' , '@drericding'}
            stopwords = STOPWORDS.union(more_stopwords)
            covid = " ".join([word for word in text_Combined.split()])
            wordcount = {}

            # To eliminate duplicates, remember to split by punctuation, and use case demiliters.
            for word in covid.lower().split():
                word = word.replace(".","")
                word = word.replace(",","")
                word = word.replace(":","")
                word = word.replace("\"","")
                word = word.replace("!","")
                word = word.replace("â€œ","")
                word = word.replace("â€˜","")
                word = word.replace("*","")
                if word not in stopwords:
                    if word not in wordcount:
                        wordcount[word] = 1
                    else:
                        wordcount[word] += 1

            word_counter = collections.Counter(wordcount)

            # Create a data frame of the most common words 
            lst = word_counter.most_common(100);
            df = pd.DataFrame(lst, columns = ['Word', 'Count'])
            text1 = df["Word"]
            text_Combined = " ".join(text1.values.astype(str))
            covid = " ".join([word for word in text_Combined.split()])

            #Create a Word Cloud
            wc = WordCloud(background_color = "White", stopwords = STOPWORDS.union(more_stopwords),width=600,height=300,relative_scaling = 0,  max_words=50)
            wc.generate(covid)
            wc.to_file('static/temporary_files/fig100.png')
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'fig100.png')
    
            return render_template("search.html", image = full_filename)
        else:
            return render_template("index.html")
    else:
        return render_template("index.html")
    
if __name__ == "__main__":
    app.run(debug=True , use_reloader=False)