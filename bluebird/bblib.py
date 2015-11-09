# Basic functionality used for the bluebird project"
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
import pymongo
import urllib2
import operator
from lxml import etree
from bs4 import UnicodeDammit
from io import StringIO


# Make config file available in this module
cfg = None
hdr = {'User-Agent': 'this and that'}

class Session:
    pass


def set_cfg(cfgobj=None):
    global cfg
    cfg = cfgobj


def set_api(api=None):
    Session.api = api


def initialize():
    glob_today = str(datetime.date.today())
    executed_number_follows_per_day[glob_today] = parse_number_follows_from_logfile()
    print "already added number of users today:", executed_number_follows_per_day[glob_today]


# verbose2 for all data that flows in
verbose2 = False

logr = logging.getLogger("logger")
executed_number_follows_per_day = collections.defaultdict(int)
max_number_follows_per_day = collections.defaultdict(int)


def parse_number_follows_from_logfile():
    today = str(datetime.date.today())
    with open("../accounts/%s/bluebird.log" % cfg.own_twittername, "r") as f:
        today_follow_counts = 0
        for line in f:
            if today in line and "followinguser" in line:
                today_follow_counts += 1
            if today in line and "follower_level_reached" in line:
                return 5000
    return today_follow_counts


class CyclicArray(object):
    def __init__(self, length=0):
        self.l = length * [None]
        self.count = 0
        self.array_length = length
        self.add_lock = False
        self.inc_lock = False

    def load_with_array(self, arr=None):
        if not arr:
            arr = []
        arr_len = len(arr)
        if arr_len > self.array_length:
            raise Exception("in class CyclicArray function load_with_array: array to load is too long.")
        self.reset()
        for el in arr:
            self.add(el, auto_increase=True)
        print "successfully loaded cyclic array with array"

    def reset(self):
        self.count = 0
        self.l = self.array_length * [None]
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

    def add(self, entry, auto_increase=False):
        if self.add_lock:
            raise Exception("add is locked. First increase count the add new values.")
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
            return self.l[self.count + 1]

    def get_count(self):
        return self.count

    def get_array_length(self):
        return len(self.l)

    def get_list(self):
        return self.l

    def isin(self, x=None):
        try:
            return self.l.index(x) >= 0
        except ValueError:
            return False

    def change_array_length(self, new_length):
        if new_length < len(self.l):
            self.l = self.l[:new_length - 1]
        elif new_length > len(self.l):
            self.l.extend((new_length - len(self.l)) * [None])
        self.array_length = len(self.l)
        self.count = min(self.count, self.array_length - 1)

    def release_add_lock_if_necessary(self):
        if self.add_lock:
            self.increase_count()


def get_ca_len(name=""):
    if name == "favorites":
        return cfg.number_active_favorites
    if name == "retweets":
        return cfg.number_active_retweets
    if name == "follows":
        return cfg.number_active_follows


def ca_initialize(name=""):
    if not os.path.isfile(name + ".sav"):
        return CyclicArray(length=get_ca_len(name))
    else:
        ca = pickle.load(open(name + ".sav", "rb"))
        if ca.get_array_length() != get_ca_len(name):
            print "length in config file has changed, tailoring..."
            ca.change_array_length(get_ca_len(name))
            print "new array length", ca.get_array_length()
        return ca


def ca_save_state(ca=None, name=""):
    with open(name + ".sav", 'w') as f:
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


def ru(s=""):
    """
    resolve unicode and return printable string
    """
    if type(s) == type(1) or type(s) == type(9999999999999999):
        return s
    return None if not s else s.encode('ascii', 'ignore')


def get_first_level_content(data, key):
    if key not in data:
        if cfg.verbose:
            print "key", key, "not found in tweet"
        return None
    return ru(data[key])


def tweet2obj(data):
    class Tweet:
        pass

    data = json.loads(data)
    if verbose2:
        print data
    try:
        Tweet.text = get_first_level_content(data, "text")
        Tweet.lan = get_first_level_content(data, "lang")
        Tweet.created = get_first_level_content(data, "created_at")
        Tweet.id = get_first_level_content(data, "id")
        Tweet.favorite_count = get_first_level_content(data, "favorite_count")
        Tweet.retweet_count = get_first_level_content(data, "retweet_count")
        Tweet.retweeted = get_first_level_content(data, "retweeted")
        user = data["user"]
        Tweet.description = get_first_level_content(user, "description")
        Tweet.loc = get_first_level_content(user, "location")
        Tweet.user_lang = get_first_level_content(user, "lang")
        Tweet.user_id = get_first_level_content(user, "id")
        Tweet.user_name = get_first_level_content(user, "name")
        Tweet.user_screen_name = get_first_level_content(user, "screen_name")
        Tweet.user_description = get_first_level_content(user, "description")
        Tweet.user_no_followers = get_first_level_content(user, "followers_count")
        return Tweet
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


def add_favorite(identifier, api):
    try:
        api.create_favorite(identifier)
        if cfg.verbose:
            print "favorite added"
        logr.info("$$Favorite;%s" % identifier)
        return True
    except tweepy.error.TweepError, e:
        logr.info("FavoriteDenied;%s" % identifier)
        logr.error("in function add_favorite; %s" % e)
        print e[0]


def remove_favorite(identifier, api):
    try:
        api.destroy_favorite(identifier)
        if cfg.verbose:
            print "favorite removed"
        logr.info("FavoriteDestroyed;%s" % identifier)
        return True
    except tweepy.error.TweepError, e:
        print e
        logr.debug("in function remove_favorite; %s" % e)


class BuildText(object):
    def __init__(self, preambles, hashtags):
        # this line to be deleted and preambled removed from function call and in init
        self.preambles = preambles
        self.hashtags = hashtags
        self.last_used_preamble = ""
        if os.path.isfile("last_title.sav"):
            try:
                self.last_titles = self.load_last_titles()
            except:
                self.last_titles = CyclicArray(100)
        else:
            self.last_titles = CyclicArray(100)

    def get_title_from_website(self, html, debug=False):
        t = lxml.html.parse(StringIO(html))
        if t is None:
            return None
        obj = t.find(".//title")
        if obj is None:
            return None
        text = obj.text
        if not text:
            raise Exception("No Text in Website")
        if not text:
            raise Exception("Text has wrong encoding")
        if self.last_titles.isin(text) and not debug:
            logr.info('already_twittered')
            return None
        if len(text) > 20:
            if not debug:
                self.last_titles.add(text, auto_increase=True)
                self.update_last_titles(self.last_titles)
            return text
        else:
            return None

    @staticmethod
    def load_last_titles():
        with open("last_title.sav", "r") as f:
            return pickle.load(f)

    @staticmethod
    def update_last_titles(l):
        f = open("last_title.sav", "w")
        pickle.dump(l, f)
        f.close()
        return

    @staticmethod
    def get_ws_html(url):
        req = urllib2.Request(url, headers=hdr)
        try:
            html = urllib2.urlopen(req).read()
        except Exception, e:
            logr.error("in function get_ws_html")
            return None
        #dammit = UnicodeDammit(html)
        #print 'dammit'
        #html = dammit.unicode_markup
        html = unicode(html, errors='ignore')
        return html

    @staticmethod
    def read_ws(html):
        try:
            ws = lxml.html.parse(StringIO(html))
        except IOError, e:
            print e
            logr.error('in function read_ws, IOError')
            return ''
        result = etree.tostring(ws.getroot(), pretty_print=False, method="html")
        return result


    def build_text(self, url, debug=False):
        """
        take in a URL and build a tweet around it. use preambles and hashtags from random
        choice but make sure not to repeat the last one.
        """
        # choose preamble
        # build first part of text

        html = self.get_ws_html(url)
        if html is None:
            return None, 0
        try:
            title = self.get_title_from_website(html, debug=debug)
        except UnicodeError:
            logr.error("UnicodeError in  get_title_from_website;%s" % e)
            title = None
        if title is None:
            return None, 0
        text = "%s %s" % (title, url)
        # Title must exist an consist of at least 4 words
        if text is None or len(text.split(" ")) < 3:
            return None, 0
        # add hashtags until tweet length is full
        try:
            score = bbanalytics.score_tweets(self.read_ws(html), is_body=True)
            hashtag_candidates = bbanalytics.get_matching_keywords(self.read_ws(html))
        except UnicodeError:
            print 'unicode error'
            score = -1
            hashtag_candidates = []
        sorted_hts = sorted(hashtag_candidates.items(), key=operator.itemgetter(1), reverse=True)
        for i in xrange(3):
            old_text = "%s" % text
            try:
                hashtag = sorted_hts[i]
                text += " #" + hashtag[0]
            except IndexError:
                logr.error('Building tweet failed')
            if len(text) > 140:
                text = old_text
                break
        if cfg.verbose:
            print "generic text:", text
        return text, score


def update_status(text, api, score):
    if len(text) > 135:
        if cfg.verbose:
            print "Text Too Long!"
        return None
    try:
        # noinspection PyUnusedLocal
        status = api.update_status(text)
    except tweepy.error.TweepError, e:
        logr.error("in function bblib:update_status;%s" % e)
    logr.info("$$StatusUpdate;%d;%s" % (score, text))
    return


def retweet(identifier, api):
    try:
        status = api.retweet(identifier)
        if cfg.verbose:
            print "retweeted"
        logr.info("$$Retweet;%s;%s" % (identifier, status.id))
        return status.id
    except tweepy.error.TweepError, e:
        print e
        logr.info("RetweetDenied;%s" % identifier)
        logr.error("in function bblib:retweet;%s" % e)
        return False


def remove_retweet(identifier, api):
    try:
        api.destroy_status(identifier)
        logr.info("RetweetDestroyed;%s" % identifier)
        return True
    except tweepy.error.TweepError, e:
        print e
        logr.info("RetweetDestroyDenied;%s" % identifier)
        logr.error("in function: remove retweet; %s" % e)
        return False


def in_time():
    now = datetime.datetime.now()
    now_time = now.time()
    if datetime.time(8, 0) <= now_time <= datetime.time(10, 30):
        return True
    if datetime.time(11, 45) <= now_time <= datetime.time(22, 00):
        return True
    if cfg.verbose:
        print "Request not in allowed time"
    return False


def get_today():
    return str(datetime.date.today())


def update_max_followers_today(today):
    max_number_follows_per_day[today] = min(992, max(195, get_info_from_account_id(
        Session.api,
        cfg.own_twittername).followers_count))
    logr.info('set max_number_follows_to%d' % max_number_follows_per_day[today])
    # ToDO drop all other dates to avoid memory leaks:


def follow_gate_open():
    today = get_today()
    ex_today = executed_number_follows_per_day[today]
    if today not in max_number_follows_per_day:
        logr.info("$$set_number_followers_for_today")
        update_max_followers_today(today)
    if ex_today >= max_number_follows_per_day[today]:
        print today, "executed number of follows", ex_today
        logr.info("$$max_no_follows_reached")
        return False
    if not in_time():
        logr.info("time not accepted")
        return False
    return True


def add_as_follower(t, api, verbose=False):
    today = str(datetime.date.today())
    if not follow_gate_open():
        logr.info("Follow Gate Closed")
        if verbose:
            if cfg.verbose:
                print "follow gate closed"
        return False
    if t.user_lang not in cfg.languages:
        logr.info("follow not carried out because language did not match")
        return False
    try:
        api.create_friendship(t.user_screen_name)
        if cfg.verbose:
            print datetime.datetime.now(), "followed", t.user_name, t.user_screen_name
        logr.info("$$followinguser;%s,%s;%s;%s", t.user_id, t.user_name, t.user_screen_name, t.user_description)
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
            executed_number_follows_per_day[today] = max_number_follows_per_day
            time.sleep(360)
        if error_code == 89 or 'expired token' in e:
            logr.error('critical: new token required! access apps.twitter.com')
            print 'error'
            sys.exit()
        if error_code == 401:
            logr.error('critical: app unauthorized! access apps.twitter.com')
            print 'error'
            sys.exit()
        logr.error("in function add_as_follower;%s" % e)


def remove_follow(screen_name, api):
    if str(screen_name).isdigit():
        try:
            user = api.get_user(screen_name)
        except:
            raise Exception("In Function remove_follow. User object could not be loaded.")
        screen_name = user.screen_name

    if screen_name in cfg.accounts_never_delete:
        logr.info("unfollowprevented;%s" % screen_name)
        return
    try:
        api.destroy_friendship(screen_name)
        logr.info("destroyedfriendship;%s", screen_name)
    except tweepy.error.TweepError, e:
        print e
        logr.error("in function remove_follow; %s" % e)


def get_statuses(api, username=None):
    """
    important note: this method only returns statuses but not retweets
    :param api: twitter api
    :param username: own twittername or given screen_name
    :return: list of statuses
    """
    if not username:
        username = cfg.own_twittername
    tl = api.user_timeline(screen_name=username, count=200)
    if len(tl) > 0:
        max_id = tl[-1].id
    else:
        return []
    print len(tl)
    while True:
        tlx = api.user_timeline(screen_name=username, count=200, max_id=max_id)
        if len(tlx) > 1:
            tl.extend(tlx)
            if len(tl) > 0:
                max_id = tl[-1].id
                print max_id
            else:
                break
        else:
            break
    print len(tl)
    return tl


def get_info_from_account_id(api=None, identifier=0):
    user = api.get_user(identifier)
    return user


def get_all_friends(api, username=None):
    """
    important note: this method only returns statuses but not retweets
    :param api: twitter api
    :param username: own twittername or given screen_name
    :return: list of statuses
    """
    if not username:
        username = cfg.own_twittername
    tl = api.friends_ids(screen_name=username, count=200)
    if len(tl) > 0:
        max_id = tl[-1].id
    else:
        return []
    print len(tl)
    while True:
        tlx = api.friends_ids(screen_name=username, count=200, max_id=max_id)
        if len(tlx) > 1:
            tl.extend(tlx)
            if len(tl) > 0:
                max_id = tl[-1].id
                print max_id
            else:
                break
        else:
            break
    print len(tl)
    return tl


def get_friends_ids(api, user=None):
    """
    :param api: twitter api object
    :param user: twitter user object. if no user is provided, the user that the api refers to is used.
    :return: list of friends (limited to 5000)
    """
    if not user:
        user = api.me()

    # ToDo: in friends_ids needs to be implemented to receive more than 5000 ids
    # friends ids come sorted from freshly added to old.

    return user.friends_ids()


class UpdateUserInfo(object):
    def __init__(self, api, account_name):
        # If this is not run from the berlin server, a ssh tunnel must be established first
        client = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = client.friends
        self.api = api
        self.account_name = account_name

    def id_exists_in_userdb(self, update_id):
        """
        Check if a certain Tweet_ID exists in the user-database
        :rtype : bool
        :param update_id: int
        :return: if user exists in database
        """
        return bool(self.db[self.account_name].find({"_id": update_id}).count())

    def update_info_in_mongodb(self, info):
        # set a propoer _id variable for mongodb that corresponds with the Twitter user_id
        info._json["_id"] = info.id
        try:
            self.db[self.account_name].update_one(
                {"_id": info.id},
                {
                    "$set": info._json,
                    "$currentDate": {"lastModified": True}
                },
                upsert=True)
            print "updated", info.id
        except Exception, e:
            logr.error("in function update_info_in_mongodb; %s" % e)

    def update_user_info(self, n=10):
        """
        update the user info to the database
        :param n: Number of users to be updated
        """
        ids = get_friends_ids(self.api)
        for user_id in random.sample(ids, n):
            info = self.get_user_info(user_id)
            self.update_info_in_mongodb(info)

    def get_user_info(self, identifier=0):
        info = get_info_from_account_id(api=self.api, identifier=identifier)
        return info


def cleanup_followers(api, ca_follow=None, ca_stat=None):
    me = api.me()
    friends_diff = me.friends_count - (cfg.number_active_follows + 10)
    friends_ids = get_friends_ids(api=api, user=me)
    print len(friends_ids), "friends found"
    if friends_diff > 0:
        for friend in random.sample(friends_ids, friends_diff + 20):
            # replace screen name and pop ids from friends and refresh cyclic array
            user = api.get_user(friend)
            screen_name = user.screen_name
            remove_follow(screen_name, api)
            logr.info("cleanupdestroy %s" % screen_name)
            friends_ids.pop(friends_ids.index(friend))
    ca_follow.load_with_array(friends_ids)

    statuses = get_statuses(api)
    nstatuses = len(statuses)
    print nstatuses, "statuses (exluding retweets) found"
    stat_diff = nstatuses - cfg.number_active_retweets
    if stat_diff > 0:
        for status in random.sample(statuses, min(nstatuses, stat_diff + 20)):
            try:
                api.destroy_status(status.id)
                logr.info("cleanupremovestatus %s %d" % (status.id, stat_diff))
                statuses.pop(statuses.index(status))
                stat_diff -= 1
            except:
                pass
    ca_stat.load_with_array(statuses)

    if me.favourites_count > cfg.number_active_favorites + 9:
        fav_diff = me.favourites_count - cfg.number_active_favorites
        for fav in api.favorites():
            try:
                remove_favorite(fav.id, api)
                logr.info("cleanupremovefavorite %s %d" % (fav.id, fav_diff))
                fav_diff -= 1
            except:
                pass


###
###
# Test Connect to Stream
###
###


def get_recent_follows(days=50):
    today = datetime.date.today()
    begin_date = today - datetime.timedelta(days=days)
    res = []
    logfile = "../accounts/%s/bluebird.log" % (cfg.own_twittername if cfg else "AlexanderD_Beck")
    with open(logfile, 'r') as f:
        for line in f:
            if "$$followinguser" in line:
                lv = line.split(';')
                strdate = lv[0].split(" ")[0]
                y, m, d = [int(x) for x in strdate.split('-')]
                if begin_date < datetime.date(y, m, d):
                    res.append(int(lv[1].split(',')[0]))
    return set(res)


class DummyListener(tweepy.StreamListener):
    def __init__(self):
        self.f = open("dev_dump.txt", "w")

    def on_data(self, data):
        # print "Tweet Start"
        self.f.write(data)
        # pprint(json.loads(data))
        tweet = tweet2obj(data)
        if not tweet:
            return True
        print('.'),
        # print tweet.text
        # print tweet.created
        # print tweet.favorite_count
        # print "Tweet End \n"
        return True

    @staticmethod
    def on_error(status):
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