from urllib.parse import urlparse, urlencode, urlunparse
from bs4 import BeautifulSoup
import json
import requests
import datetime
import logging as log
from time import sleep


class Twitter_Hashtag:
    def pipeline(query,max_tweet):
        global new_data,counter,max_tweets
        new_data = []
        max_tweets = max_tweet
        counter = 0
        Twitter_Hashtag.search(query)
        return new_data

    def search(query):
        Twitter_Hashtag.perform_search(query)

    def perform_search(query):
        url = Twitter_Hashtag.construct_url(query)
        continue_search = True
        min_tweet = None
        response = Twitter_Hashtag.execute_search(url)
        while response is not None and continue_search and response['items_html'] is not None:
            tweets = Twitter_Hashtag.parse_tweets(response['items_html'])

            # If we have no tweets, then we can break the loop early
            if len(tweets) == 0:
                break

            # If we haven't set our min tweet yet, set it now
            if min_tweet is None:
                min_tweet = tweets[0]

            continue_search = Twitter_Hashtag.save_tweets(tweets)

            # Our max tweet is the last tweet in the list
            max_tweet = tweets[-1]
            if min_tweet['tweet_id'] is not max_tweet['tweet_id']:
                if "min_position" in response.keys():
                    max_position = response['min_position']
                else:
                    max_position = "TWEET-%s-%s" % (max_tweet['tweet_id'], min_tweet['tweet_id'])
                url = Twitter_Hashtag.construct_url(query, max_position=max_position)
                # Sleep for our rate_delay
                sleep(0)
                response = Twitter_Hashtag.execute_search(url)

    def execute_search(url):
        try:
            # Specify a user agent to prevent Twitter from returning a profile card
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.'
                            '86 Safari/537.36'
            }
            req = requests.get(url, headers=headers)
            # response = urllib2.urlopen(req)
            data = json.loads(req.text)
            return data

        # If we get a ValueError exception due to a request timing out, we sleep for our error delay, then make
        # another attempt
        except Exception as e:
            print(e)
            print("Sleeping for %i" % 1)
            sleep(1)
            return Twitter_Hashtag.execute_search(url)

    def parse_tweets(items_html):
        soup = BeautifulSoup(items_html, "html.parser")
        tweets = []
        for li in soup.find_all("li", class_='js-stream-item'):

            # If our li doesn't have a tweet-id, we skip it as it's not going to be a tweet.
            if 'data-item-id' not in li.attrs:
                continue

            tweet = {
                'tweet_id': li['data-item-id'],
                'text': None,
                'user_id': None,
                'user_screen_name': None,
                'user_name': None,
                'created_at': None,
                'static_link':None,
                'retweets': 0,
                'favorites': 0
                
            }

            # Tweet Text
            text_p = li.find("p", class_="tweet-text")
            if text_p is not None:
                tweet['text'] = text_p.get_text()

            # Tweet User ID, User Screen Name, User Name
            user_details_div = li.find("div", class_="tweet")
            if user_details_div is not None:
                tweet['user_id'] = user_details_div['data-user-id']
                tweet['user_screen_name'] = user_details_div['data-user-id']
                tweet['user_name'] = user_details_div['data-name']

            # Tweet date
            date_span = li.find("span", class_="_timestamp")
            if date_span is not None:
                tweet['created_at'] = float(date_span['data-time-ms'])

            # Tweet Retweets
            retweet_span = li.select("span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
            if retweet_span is not None and len(retweet_span) > 0:
                tweet['retweets'] = int(retweet_span[0]['data-tweet-stat-count'])

            # Tweet Favourites
            favorite_span = li.select("span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
            if favorite_span is not None and len(retweet_span) > 0:
                tweet['favorites'] = int(favorite_span[0]['data-tweet-stat-count'])
                
            link = li.find('a', class_='tweet-timestamp js-permalink js-nav js-tooltip')
            if link is not None and len(link) > 0:
                tweet['static_link'] = "http://twitter.com"+link.get('href')

            tweets.append(tweet)
        return tweets

    def construct_url(query, max_position=None):
        """
        For a given query, will construct a URL to search Twitter with
        :param query: The query term used to search twitter
        :param max_position: The max_position value to select the next pagination of tweets
        :return: A string URL
        """

        params = {
            # Type Param
            'f': 'tweets',
            # Query Param
            'q': query
        }

        # If our max_position param is not None, we add it to the parameters
        if max_position is not None:
            params['max_position'] = max_position

        url_tupple = ('https', 'twitter.com', '/i/search/timeline', '', urlencode(params), '')
        return urlunparse(url_tupple)

    def save_tweets(tweets):
        global new_data,counter
        for tweet in tweets:
            # Lets add a counter so we only collect a max number of tweets
            new_data.append(tweet)
            counter = counter + 1

            # When we've reached our max limit, return False so collection stops
            if max_tweets is not None and counter >= max_tweets:
                return False

        return True