#Basic functionality used for the bluebird project"
import tweepy
import json
import bbanalytics
import logging
import pickle
import os.path
import datetime
import time
import collections 
import sys
import os.path
import random
import lxml.html


#Make config file available in this module
cfg = None
def set_cfg(cfgobj = None):
    global cfg
    cfg = cfgobj

def initialize():
    glob_today = str(datetime.date.today())
    executed_number_follows_per_day[glob_today] = parse_number_follows_from_logfile()
    print "already added number of users today:", executed_number_follows_per_day[glob_today]

#verbose2 for all data that flows in
verbose2 = False

max_no_followers_per_day = 992
logr = logging.getLogger("logger")
executed_number_follows_per_day = collections.defaultdict(int)

def parse_number_follows_from_logfile():
    today = str(datetime.date.today())
    with open("../accounts/%s/bluebird.log"%cfg.own_twittername, "r") as f:
        today_follow_counts = 0
        for line in f:
            if today in line and "followinguser" in line:
                today_follow_counts += 1
            if today in line and "follower_level_reached" in line:
                return 5000
    return today_follow_counts


class CyclicArray(object):
    def __init__(self, len = 0):
        self.l = len*[None]
        self.count = 0
        self.array_length = len
        self.add_lock = False
        self.inc_lock = False

    def load_with_array(self, arr = []):
        arr_len = len(arr)
        if arr_len > self.array_length:
            raise Exception("in class CyclicArray function load_with_array: array to load is too long.")
        self.reset()
        for el in arr:
            self.add(el, auto_increase=True)
        print "successfully loaded cyclic array with array"

    def reset(self):
        self.count = 0
        self.l = self.array_length*[None]
        self.add_lock = False
        self.inc_lock = False
        
    def cprint(self):
        print "Cyclic Array Count: ", self.count
        print self.l
    
    def increase_count(self):
        if self.inc_lock:
            raise Exception("count increase is locked. First add new value to the cyclic array.")
        self.count += 1
        if self.count == self.array_length:
            self.count = 0
        self.inc_lock = True
        self.add_lock = False
            
    def add(self, entry, auto_increase = False):
        if self.add_lock:
            raise  Exception("add is locked. First increase count the add new values.")
        self.l[self.count] = entry
        self.add_lock = True
        self.inc_lock = False
        if auto_increase:
            self.increase_count()
    
    def get_current_entry(self):
        return self.l[self.count]
    
    def get_next_entry(self):
        if self.inc_lock:
            raise Exception("counter has already been incremented. Use current entry instead")
        if self.count == self.array_length - 1:
            return self.l[0]
        else:
            return self.l[self.count+1]

    def get_count(self):
        return self.count
    
    def get_array_length(self):
        return len(self.l)

    def get_list(self):
        return self.l
    
    def isin(self, x = 0):
        try:
            return self.l.index(x) >= 0
        except ValueError:
            return False
        
    def change_array_length(self, new_length):
        if new_length < len(self.l):
            self.l = self.l[:new_length -1]
        elif new_length > len(self.l):
            self.l.extend((new_length - len(self.l)) * [None])
        self.array_length = len(self.l)
        self.count = min(self.count, self.array_length -1)
        
    def release_add_lock_if_necessary(self):
        if self.add_lock:
            self.increase_count()
        
def get_ca_len(name = ""):
    if name == "favorites":
        return cfg.number_active_favorites
    if name == "retweets":
        return cfg.number_active_retweets
    if name == "follows":
        return cfg.number_active_follows

def ca_initialize(name = ""):
    if not os.path.isfile(name+".sav"):
        return CyclicArray(len = get_ca_len(name))
    else:
        ca = pickle.load(open(name+".sav", "rb"))
        if ca.get_array_length() != get_ca_len(name):
            print "length in config file has changed, tailoring..."
            ca.change_array_length(get_ca_len(name))
            print "new array length", ca.get_array_length()
        return ca

def ca_save_state(ca = None, name = ""):
    with open(name+".sav", 'w') as f:
        pickle.dump(ca, f)    

def connect_app_to_twitter():
    """
    Use credential in config file and use OAuth to connect to twitter. return the authentication and the api.
    return auth, api
    """
    auth = tweepy.OAuthHandler(cfg.consumer_key, cfg.consumer_secret)
    auth.set_access_token(cfg.access_token, cfg.access_token_secret)
    api = tweepy.API(auth)
    return auth, api

def ru(s = ""):
    """
    resolve unicode and return printable string
    """
    if type(s) == type(1) or type(s) == type(9999999999999999): return s
    return None if not s else s.encode('ascii', 'ignore')

def get_first_level_content(data, key):
    if not key in data:
        if cfg.verbose:
            print "key", key, "not found in tweet"
        return None
    return ru(data[key])

def tweet2obj(data):
    class t:pass
    data = json.loads(data)
    if verbose2:
        print data
    try:
        t.text = get_first_level_content(data,"text")
        t.lan = get_first_level_content(data,"lang")
        t.created = get_first_level_content(data,"created_at")
        t.id = get_first_level_content(data, "id")
        t.favorite_count  = get_first_level_content(data, "favorite_count")
        t.retweet_count = get_first_level_content(data, "retweet_count")
        t.retweeted = get_first_level_content(data, "retweeted")
        user = data["user"]
        t.description = get_first_level_content(user,"description")
        t.loc = get_first_level_content(user, "location")
        t.user_lang = get_first_level_content(user, "lang")
        t.user_id = get_first_level_content(user, "id")
        t.user_name = get_first_level_content(user, "name")
        t.user_screen_name = get_first_level_content(user, "screen_name")
        t.user_description = get_first_level_content(user, "description")
        t.user_no_followers = get_first_level_content(user, "followers_count")
        return t
    except:
        return None

def print_tweet(t):
    print "-----"
    print t.text
    print t.loc
    print t.lan
    print t.retweet_count
    print t.favorite_count
    print t.created
    print t.retweeted
    print t.user_name
    print t.user_id
    print t.user_lang
    print t.user_screen_name
    print t.user_description
    print t.user_no_followers
    print "#####"

def add_favorite(id, api):
    try:
        api.create_favorite(id)
        if cfg.verbose: print "favorite added"
        logr.info("$$Favorite;%s"%(id))
        return True
    except tweepy.error.TweepError, e:
        logr.info("FavoriteDenied;%s"%(id))
        logr.error("in function add_favorite; %s"%e)
        print e[0]

def remove_favorite(id, api):
    try:
        api.destroy_favorite(id)
        if cfg.verbose: print "favorite removed"
        logr.info("FavoriteDestroyed;%s"%(id))
        return True
    except tweepy.error.TweepError, e:
        print e
        logr.debug("in function remove_favorite; %s"%e)


class BuildText(object):
    def __init__(self, preambles, hashtags):
        #this line to be deleted and preambled removed from function call and in init
        self.preambles = preambles
        self.hashtags = hashtags
        self.last_used_preamble = ""
        if os.path.isfile("last_title.sav"):
            self.last_titles = self.load_last_titles()
        else:
            self.last_titles = CyclicArray(100)

    def get_title_from_website(self, url):
        try:
            t = lxml.html.parse(url)
            text = t.find(".//title").text
            if not text:
                raise Exception("No Text in Website")
            text = ru(text)
            if not text:
                raise Exception("Text has wrong encoding")
            if self.last_titles.isin(text):
                raise Exception("already twittered")
            if len(text) > 20:
                self.last_titles.add(text, auto_increase= True)
                self.update_last_titles(self.last_titles)
                return text
            else:
                return None
        except Exception, e:
            return None

    def load_last_titles(self):
        with open("last_title.sav","r") as f:
            return pickle.load(f)

    def update_last_titles(self, l):
        f = open("last_title.sav","w")
        pickle.dump(l,f)
        f.close()
        return

    def build_text(self, url):
        """
        take in a URL and build a tweet around it. use preambles and hashtags from random choice but make sure not to repeat the last one.
        """
        #choose preamble
        #build first part of text
        title = self.get_title_from_website(url)
        if not title:
            return None
        text = "%s %s"%(title, url)
        #Title must exist an consist of at least 4 words
        if not text or len(text.split(" ")) < 3:
            return None
        #add hashtags until tweet length is full
        help_hashtags = []
        for i in xrange(3):
            old_text = "%s"%text
            hash = random.choice(self.hashtags)
            if hash in help_hashtags:
                continue
            help_hashtags.append(hash)
            text += " " + hash
            if len(text) > 140:
                text = old_text
                break
        if cfg.verbose:
            print "generic text:", text
        return text

def update_status(text, api):
    if len(text) > 135:
        if cfg.verbose: print "Text Too Long!"
        return None
    try:
        status = api.update_status(text)
    except tweepy.error.TweepError, e:
        logr.error("in function bblib:update_status;%s"%e)
    logr.info("$$StatusUpdate;%s"%(text))
    return

def retweet(id, api):
    try:
        status = api.retweet(id)
        if cfg.verbose: print "retweeted"
        logr.info("$$Retweet;%s;%s"%(id,status.id))
        return status.id
    except tweepy.error.TweepError, e:
        print e
        logr.info("RetweetDenied;%s"%(id))
        logr.error("in function bblib:retweet;%s"%e)
        return False
    
def remove_retweet(id, api):
    try:
        api.destroy_status(id)
        logr.info("RetweetDestroyed;%s"%(id))
        return True
    except tweepy.error.TweepError, e:
        print e
        logr.info("RetweetDestroyDenied;%s"%(id))
        logr.error("in function: remove retweet; %s"%e)
        return False

def in_time():
    now = datetime.datetime.now()
    now_time = now.time()
    if now_time >= datetime.time(8,0) and now_time <= datetime.time(10,30):
        return True
    if now_time >= datetime.time(11,45) and now_time <= datetime.time(22,00):
        return True
    if cfg.verbose: print "Request not in allowed time"
    return False

def follow_gate_open():  
    today = str(datetime.date.today())
    ex_today = executed_number_follows_per_day[today]
    if ex_today >= max_no_followers_per_day:
        print today,"executed number of follows", ex_today
        logr.info("NumberFollowersExceeded")
        return False
    if not in_time():
        logr.info("time not accepted")
        return False
    return True

def add_as_follower(t, api, verbose = False):
    today = str(datetime.date.today())
    if not follow_gate_open():
        logr.info("Follow Gate Closed")
        if verbose:
            if cfg.verbose: print "follow gate closed"
        return False
    if not t.user_lang in cfg.languages:
        logr.info("follow not carried out because language did not match")
        return False 
    try:
        api.create_friendship(t.user_screen_name)
        if cfg.verbose: print datetime.datetime.now(),"followed", t.user_name, t.user_screen_name
        logr.info("$$followinguser;%s,%s;%s;%s",t.user_id, t.user_name, t.user_screen_name, t.user_description)
        if cfg.verbose:
            print "Following User"
            print t.user_screen_name
            print t.user_description
        executed_number_follows_per_day[today] += 1        
        return True
    except tweepy.error.TweepError, e:
        print e        
        error_code = e[0][0]["code"]
        if error_code == 161: 
            logr.info("follower_level_reached")
            print "Follower level reached this should not happen. Function: add_as_follower in bblib.py"
            executed_number_follows_per_day[today] = max_no_followers_per_day
            time.sleep(360)
        logr.error("in function add_as_follower;%s"%e)
        
def remove_follow(screen_name, api):
    if str(screen_name).isdigit():
        try:
            user = api.get_user(screen_name)
        except:
            raise Exception("In Function remove_follow. User object could not be loaded.")
        screen_name = user.screen_name
    
    if screen_name in cfg.accounts_never_delete:
        logr.info("unfollowprevented;%s"%(screen_name))
        return 
    try:
        api.destroy_friendship(screen_name)
        logr.info("destroyedfriendship;%s",screen_name)
    except tweepy.error.TweepError, e:
        print e
        logr.error("in function remove_follow; %s"%e)

def get_statuses(api, username = None):
    """
    :param api: twitter api
    :param username: own twittername or given screen_name
    :return: list of statuses
    """
    if not username: username = cfg.own_twittername
    tl = api.user_timeline(screen_name = username, count = 200)
    if len(tl) > 0 :
        max_id = tl[-1].id
    else:
        return []
    while True:
        tlx = api.user_timeline(screen_name = username, count = 200, max_id = max_id)
        if len(tlx)>1:
            tl.extend(tlx)
            if len(tl) > 0:
                max_id = tl[-1].id
            else:
                break
        else:
            break
    return tl

def get_friends_ids(api, user = None):
    """
    :param api: twitter api object
    :param user: twitter user object. if no user is provided, the user that the api refers to is used.
    :return: list of friends (limited to 5000)
    """
    if not user:
        user = api.me()
    #ToDo: in friends_ids needs to be implemented to receive more than 5000 ids
    #friends ids come sorted from freshly added to old.
    return user.friends_ids()

def cleanup_followers(api, ca_follow = None, ca_stat = None, ca_fav = None):
    me = api.me()
    friends_diff = me.friends_count - (cfg.number_active_follows+10)
    friends_ids = get_friends_ids(api=api, user=me)
    print len(friends_ids), "friends found"
    if friends_diff > 0:
        for friend in random.sample(friends_ids,friends_diff+20):
            #replace screen name and pop ids from friends and refresh cyclic array
            user = api.get_user(friend)
            screen_name = user.screen_name
            remove_follow(screen_name, api)
            logr.info("cleanupdestroy %s"%screen_name)
            friends_ids.pop(friends_ids.index(friend))
    ca_follow.load_with_array(friends_ids)

    statuses = get_statuses(api)
    print len(statuses), "statuses found"
    stat_diff = me.statuses_count - cfg.number_active_retweets
    if stat_diff > 0:
        for status in random.sample(statuses, stat_diff+20):
            try:
                api.destroy_status(status.id)
                logr.info("cleanupremovestatus %s %d" % (status.id, stat_diff))
                statuses.pop(statuses.index(status))
                stat_diff -= 1
            except:
                pass
    print len(statuses)
    ca_stat.load_with_array(statuses)

    if me.favourites_count > cfg.number_active_favorites+9:
        fav_diff = me.favourites_count - cfg.number_active_favorites
        for fav in api.favorites():
            try:
                remove_favorite(fav.id, api)
                logr.info("cleanupremovefavorite %s %d"(fav.id, fav_diff))
                fav_diff -= 1
            except:
                pass


###
###
#Test Connect to Stream
###
###


def get_recent_follows(days = 50):
    today = datetime.date.today()
    begin_date = today - datetime.timedelta(days = days)
    res = []
    logfile = "../accounts/%s/bluebird.log" % (cfg.own_twittername if cfg else "AlexanderD_Beck")
    with open(logfile, 'r') as f:
        for line in f:
            if "$$followinguser" in line:
                lv = line.split(';')
                strdate = lv[0].split(" ")[0]
                y,m,d = [int(x) for x in strdate.split('-')]
                if begin_date < datetime.date(y,m,d):
                    res.append(int(lv[1].split(',')[0]))
    return set(res)




class DummyListener(tweepy.StreamListener):
    def __init__(self):
        self.f = open("dev_dump.txt", "w")
    def on_data(self, data):
        #print "Tweet Start"
        self.f.write(data)
        #pprint(json.loads(data))
        tweet = tweet2obj(data)
        if not tweet: return True
        print('.'),
        #print tweet.text
        #print tweet.created
        #print tweet.favorite_count
        #print "Tweet End \n"
        return True
    def on_error(self, status):
        print "error: ",
        print status

def test_stream():
    print "running test_stream"
    auth, api = connect_app_to_twitter()
    l = DummyListener()
    stream = tweepy.Stream(auth, l)
    kw = bbanalytics.manage_keywords(cfg.keywords)
    print kw.keys()
    while True:
        try:
            stream.filter(track=kw.keys())
        except Exception, e:
            print e
            pass
    
if __name__ == '__main__':
    from pprint import pprint
    #connect_app_to_twitter()
    #test_stream()
    get_recent_follows()
