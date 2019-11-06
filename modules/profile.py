from bs4 import BeautifulSoup
import requests
from os.path import join, dirname, realpath
import os
import json
import sys
import re
import pickle
import time
import numpy as np
import pandas as pd
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
from collections import Counter

UPLOADS_PATH = join(dirname(realpath(__file__)), '../static/uploads/')
with open(UPLOADS_PATH+'turkce-stop-words.txt', encoding='utf-8') as file:
    stw = file.read()
stw = stw.split()
stw = [s.lower() for s in stw]
news = ["com","http","twitter","https","status","www","pic"]
stop = stw
stop += news

class Twitter_Profile:
    def get_tweet_text(tweet):
        tweet_text_box = tweet.find("p", {"class": "TweetTextSize TweetTextSize--normal js-tweet-text tweet-text"})
        images_in_tweet_tag = tweet_text_box.find_all("a", {"class": "twitter-timeline-link u-hidden"})
        tweet_text = tweet_text_box.text
        for image_in_tweet_tag in images_in_tweet_tag:
            tweet_text = tweet_text.replace(image_in_tweet_tag.text, '')

        return tweet_text

    def get_this_page_tweets(soup):
        tweets_list = list()
        tweets = soup.find_all("li", {"data-item-type": "tweet"})
        for tweet in tweets:
            tweet_data = None
            try:
                tweet_data = Twitter_Profile.get_tweet_text(tweet)
            except Exception as e:
                continue
                #ignore if there is any loading or tweet error

            if tweet_data:
                tweets_list.append(tweet_data)
                sys.stdout.flush()

        return tweets_list


    def get_tweets_data(username, soup):
        tweets_list = list()
        tweets_list.extend(Twitter_Profile.get_this_page_tweets(soup))

        next_pointer = soup.find("div", {"class": "stream-container"})["data-min-position"]

        while True:
            next_url = "https://twitter.com/i/profiles/show/" + username + \
                    "/timeline/tweets?include_available_features=1&" \
                    "include_entities=1&max_position=" + next_pointer + "&reset_error_state=false"

            next_response = None
            try:
                next_response = requests.get(next_url)
            except Exception as e:
                # in case there is some issue with request. None encountered so far.
                return tweets_list

            tweets_data = next_response.text
            tweets_obj = json.loads(tweets_data)
            if not tweets_obj["has_more_items"] and not tweets_obj["min_position"]:
                # using two checks here bcz in one case has_more_items was false but there were more items
                break
            next_pointer = tweets_obj["min_position"]
            html = tweets_obj["items_html"]
            soup = BeautifulSoup(html, 'lxml')
            tweets_list.extend(Twitter_Profile.get_this_page_tweets(soup))

        return tweets_list

    def start(username = None):
        username = username
        url = "http://www.twitter.com/" + username
        response = None
        try:
            response = requests.get(url)
        except Exception as e:
            print(repr(e))
            sys.exit(1)

        if response.status_code != 200:
            sys.exit(1)

        soup = BeautifulSoup(response.text, 'lxml')

        if soup.find("div", {"class": "errorpage-topbar"}):
            sys.exit(1)

        tweets = Twitter_Profile.get_tweets_data(username, soup)
        tweet_count = soup.findAll("span", {"class": "ProfileNav-value"})[0].text.strip(' \n\t')
        follower_count = soup.findAll("span", {"class": "ProfileNav-value"})[1].text.strip(' \n\t')
        following_count = soup.findAll("span", {"class": "ProfileNav-value"})[2].text.strip(' \n\t')
        fav_count = soup.findAll("span", {"class": "ProfileNav-value"})[3].text.strip(' \n\t')
        return tweets,tweet_count, following_count, follower_count, fav_count

    def preprocessing(ReviewText):
        ReviewText = ReviewText.lower()
        #Verideki <br> taglarını kaldır.
        ReviewText = ReviewText.replace("(<br/>)", "")
        ReviewText = ReviewText.replace('(<a).*(>).*(</a>)', '')
        ReviewText = ReviewText.replace('(&amp)', '')
        ReviewText = ReviewText.replace('(&gt)', '')
        ReviewText = ReviewText.replace('(&lt)', '')
        ReviewText = ReviewText.replace('(\xa0)', ' ')
        #Verideki Linkleri Kaldır.
        ReviewText = ReviewText.replace(r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', ' ')
        return " ".join([word for word in ReviewText.split() if word not in stop])

    def get_top_n_words(corpus, n=None, query=None):
        global stop
        stop.append(query.lower())
        vec = CountVectorizer(stop_words = stop).fit(corpus)
        bag_of_words = vec.transform(corpus)
        sum_words = bag_of_words.sum(axis=0)
        words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
        words_freq =sorted(words_freq, key = lambda x: x[1], reverse=True)
        return words_freq[:n],len(words_freq)

    def predicting(x,vectorizer,model):
        test_sample = []
        for i in range(len(x)):
            test_sample.append(Twitter_Profile.preprocessing(x[i]))
        sample = vectorizer.transform(test_sample).toarray()
        result = model.predict(sample)
        return result