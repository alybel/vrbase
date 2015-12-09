import re
import math
from collections import Counter
import datetime
import logging
logr = logging.getLogger("logger")
import nltk
from nltk.util import ngrams

cfg = None
languages = []
locations = []
keywords = None
blacklist = {}


#Make config file available in this module
def set_cfg(cfgobj=None):
    """
    :param cfgobj (object):
    :return: None
    """
    global cfg
    cfg = cfgobj
    if cfg:
        "Config Loaded"
        return True
    else:
        "config not loaded"
        return False


def initialize():
    global languages, locations, keywords, blacklist
    languages = cfg.languages if cfg.languages != [] else None
    locations = cfg.locations if cfg.locations != [] else None
    keywords = manage_keywords2(cfg.keywords)
    try:
        #Blacklist must be a Dictonary
        blacklist = cfg.blacklist
    except:
        # If loaded from file, use the two lists and combine them 
        cfg.negative_keywords.extend(cfg.forbidden_keywords)
        for el in cfg.negative_keywords:
            blacklist[el] = 1000
    print keywords
    print blacklist


def manage_keywords(d):
    """
    split and iterate over keywords
    :param d: dictionary that contains the keywords extracted from the configuration file
    :return: a dictionary with mutually combined keywords
    """
    keylist = d.keys()    
    for key in keylist: 
        if " " in key: 
            kv = key.split(" ")
            for k in kv:
                #add each part of a keyword to the dict
                d[k] = d[key] / 2.
            #add the joint parts of the keyword to the dict
            d["".join(kv)] = d[key]
    return d

def manage_keywords2(d):
    """
    remove all whitespaces from keywords. do not split and double-store keywords with blanks.
    :param d:
    return d
    """

    keylist = d.keys()
    for key in keylist:
        if " " in key:
            d[key.replace(" ","")] = d.pop(key)
    return d

def generic_filter(entity, compare_list):
    if not compare_list:
        return True
    if entity not in compare_list:
        return False
    return True


def lan_filter(lan):
    return generic_filter(lan, languages)


def loc_filter(loc):
    return generic_filter(loc, locations)

def filter_unwanted_content(t):

    excluded_content = ["thong", "pussy", "horny", "sex", "porn", "drug", "xxx", "naked", "nackt", "pussies", "ass",
                        "bikini", "tits", "hot", "sexy", "naughty", "panty", "nasty", "bitch", "toy", "dildo",
                        "vibrator", "upskirt", "downblouse", "strip", "boobs", "seitensprung"]
    for word in excluded_content:
        if word in t.text:
            return False
        if t.description and (word in t.description):
            return False
        if t.user_name and (word in t.user_name):
            return False
        if t.user_screen_name and (word in t.user_screen_name):
            return False
    return True

def filter_tweets(t):
    if not filter_unwanted_content(t):
        return False
    if cfg.only_with_url and not is_url_in_tweet(t.text):
        return False
    if 0 <= cfg.number_hashtags < number_hashtags(t.text):
        return False
    return lan_filter(t.lan) and loc_filter(t.loc)


def split_and_clean_text(t=""):
    t = t.lower()
    for p in [",","!","?",".","]","["]:
        t = t.replace(p," ")
    t = t.replace("-","")  
    #split t into pieces
    t = t.split(" ")
    #remove hashtags
    t = [x.lstrip("#") for x in t]
    #remove plural s
    t = [x.rstrip("s") for x in t if len(x) > 2]
    #Uniquifiy the list of words
    #bild tuples of 2 words
    #tstar = [t[i] + " " + t[i+1] for i,x in enumerate(t) if i < len(t)-1]
    #t.extend(tstar)
    return t


def number_hashtags(t):
    count = 0
    for character in t:
        if character == "#":
            count +=1
    return count


def eval_tweet(t):
    #simple check for words in dict and attach their weights
    score = 0
    for word in t:
        if word in keywords:
            score += keywords[word]


def eval_tweet2(t):
    """
    calculate the whitelist-part score of a tweet. check the combination of one word plus its subsequent
    word if it matches a keyword. So, : "data science" will match "datascience"
    :param t:
    :return: score
    """
    if not keywords:
        raise ValueError('keywords list empty. is the config file properly loaded?')
    score = 0
    used_words = []
    for i, word in enumerate(t):
        if word in used_words:
            continue
        if word in keywords:
            score += keywords[word]
            used_words.append(word)
        else:
            if i == len(t) - 1:
                continue
            #build the combination of a word plus the subsequent word
            comb = word + t[i + 1]
            if comb in used_words:
                continue
            if comb in keywords:
                score += keywords[comb]
                used_words.append(comb)
    return score

def score_tweets(t="", verbose = False, is_body=False):
    """
    input the tweet text and receive a score
    :param: tweet text
    :type: string
    :returns score (int)
    """
    q = t
    t = split_and_clean_text(t)
    score = eval_tweet2(t)
    for word in t:
        if word in blacklist and not is_body:
            score -= blacklist[word]
            if verbose: print 'negative word',word
    if score >=0 and verbose:
        logr.info("TestTweet;%d;%s:%s"%(score,q,t))
        print score
        print q
        print t
    return score


def is_url_in_tweet(t = ""):
    q = t.split(" ")
    for word in q:
        if len(word) > 10 and "." in word and "/" in word:
            return True
    if "http" in t: 
        return True
    return False


def extract_url_from_tweet(t = ""):
    """extract url from a string. Check if url is more than 18 characters, as for example: http://bit.ly/fi23uhf"""
    q = t.split(" ")
    for word in q:
        if "http" in word and len(word) > 18:
            http_from = word.index('http')
            return word[http_from:]
    return None

def get_matching_keywords(text=''):
    """return a dictrionary that contains the keywords with weights that match a given text"""
    result = {}
    text = text.decode('utf-8', 'replace')
    token = nltk.word_tokenize(text)
    for word in keywords:
        if word in token and word not in result:
            result[word] = keywords[word]
        for w1, w2 in ngrams(token,2):
            if w1 + w2 == word and word not in result:
                result[word] = keywords[word]
    return result

class CosineStringSimilarity(object):
    def __init__(self):
        filling_words = ["in", "to", "a", "http", "as", "of", "and", "or", "it", "is", "on", "the"]
        filling_words.extend(cfg.keywords)
        self.filling_words = [x.lower() for x in filling_words]
        self.WORD = re.compile(r'\w+')
        
    @staticmethod
    def get_cosine(vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator
        
    def text_to_vector(self, text):
        words = self.WORD.findall(text)
        words = [x.lower() for x in words]
        words = list(set(words) - set(self.filling_words))
        return Counter(words)
    
    def tweets_similar(self, t1, t2):
        vector1 = self.text_to_vector(t1)
        vector2 = self.text_to_vector(t2)
        similarity = self.get_cosine(vector1, vector2)
        return similarity > 0.6
    
    def tweets_similar_list(self, t, tl):
        for t2 in tl:
            if not t2:
                continue
            if self.tweets_similar(t, t2):
                return True
        return False
            
            
def minutes_of_day():
    return datetime.datetime.now().time().minute + datetime.datetime.now().time().hour * 60
