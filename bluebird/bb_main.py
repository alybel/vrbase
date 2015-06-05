#! /usr/bin/python -u

import logging
import logging.handlers
import sys
import time
import traceback
import random
import argparse
import httplib
import collections

import tweepy


formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# first file logger
logr = logging.getLogger('logger')
hdlr_1 = None
TextBuilder = None

recent_follows = []

class ManageUpdatesPerDay(object):
    def __init__(self, max_updates):
        self.max_updates = max_updates
        self.no_updates = collections.defaultdict(int)
    def max_reached(self):
        return self.no_updates[bbl.get_today()] >= self.max_updates
    def add_update(self):
        self.no_updates[bbl.get_today()] += 1

def lp(s):
    """print this line if verbose is true """
    if verbose:
        print s


def favorite_management(t, ca, api):
    if random.random() > 0.3:
        return False
    #check if ID is already favorited. If yes, interrupt.
    if ca.isin(t.id):
        return True
    status = bbl.add_favorite(t.id, api)
    if not status:
        return False
    ca.add(t.id)
    next_entry = ca.get_next_entry()
    if next_entry:
        #try except needed becasue users may not exist anymore in the future. removing them would then throw an error
        try:bbl.remove_favorite(next_entry, api)
        except:pass
    ca.increase_count()
    bbl.ca_save_state(ca, "favorites")
    return True


def retweet_management(t, ca, api):
    if random.random() > 0.3:
        return False
    lp("Entering Retweet Management")
    if ca.isin(t.id):
        return False
    rt_id = bbl.retweet(t.id, api)
    if not rt_id:
        return False
    ca.add(rt_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        #try except needed becasue retweets may not exist anymore in the future. removing them would then throw an error
        try: bbl.remove_retweet(next_entry, api)
        except: pass
    ca.increase_count()
    bbl.ca_save_state(ca, "retweets")
    return True


def follow_management(t, ca, api):
    global recent_follows
    lp("entering follow management")
    if ca.isin(t.user_id):
        return False
    status = bbl.add_as_follower(t,api, verbose = verbose)
    if not status:
        return False
    ca.add(t.user_screen_name)
    recent_follows.append(t.user_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        try: bbl.remove_follow(next_entry, api)
        except: pass
    ca.increase_count()
    bbl.ca_save_state(ca, "follows")
    return True    


class tweet_buffer(object):
    def __init__(self, ca, api, management_fct, delta_time, max_number_actions = 3):
        self.buffer = []
        self.ca = ca
        self.api = api
        self.management_fct = management_fct
        self.delta_time = delta_time
        self.max_number_actions = max_number_actions
        lp("initiate tweet buffer")
        logr.info("initiate tweet buffer")

    def add_to_buffer(self, t, score):
        if bba.minutes_of_day() % self.delta_time == 0:
            self.flush_buffer()            
            self.buffer = []
        else:
            self.buffer.append((score,t))
        
    def flush_buffer(self):
        logr.info("Flush Buffer")
        lp("Flush Buffer!%s"%str(bba.minutes_of_day()))
        self.buffer.sort(reverse = True)
        for i in xrange(min(self.max_number_actions,len(self.buffer))):
            try:
                tweet = self.buffer[i][1]
            except IndexError:
                print self.buffer
                raise
            args = (tweet, self.ca, self.api)
            #Introduce some randomness such that not everything is retweeted favorited and statused
            self.management_fct(*args)
        return True


class FavListener(tweepy.StreamListener):
    def __init__(self, api):
        tweepy.StreamListener.__init__(self)
        self.api = api
        #ca is a cyclic array that contains the tweet ID's there were favorited. Once the number_active_favorites is reached, 
        #the oldest favorite is automatically removeedd.
        self.ca = bbl.ca_initialize("favorites")
        #self.ca_r = bbl.ca_initialize("retweets")
        #self.ca_f = bbl.ca_initialize("follows")

        #build the followers cyclic array
        self.ca_f = bbl.CyclicArray(len = bbl.get_ca_len("follows"))
        self.ca_r = bbl.CyclicArray(len = bbl.get_ca_len("retweets"))
        #refresh followers and statusses
        bbl.cleanup_followers(api, ca_follow = self.ca_f, ca_stat = self.ca_r, ca_fav = self.ca)

        self.ca_recent_r = bbl.CyclicArray(100)
        self.ca_recent_f =  bbl.CyclicArray(100)

        self.ca.release_add_lock_if_necessary()
        self.ca_r.release_add_lock_if_necessary()
        self.ca_f.release_add_lock_if_necessary()

        self.CSim = bba.CosineStringSimilarity()

        #Buffers for all 4 Types of Interaction
        self.tbuffer = tweet_buffer(api = self.api, ca = self.ca_f, management_fct=follow_management,
                                    delta_time=cfg.activity_frequency, max_number_actions=200)
        self.tbuffer_rt = tweet_buffer(api = self.api, ca = self.ca_r, management_fct=retweet_management,
                                       delta_time = cfg.activity_frequency)
        self.tbuffer_fav = tweet_buffer(api = self.api, ca = self.ca, management_fct=favorite_management,
                                        delta_time = cfg.activity_frequency)

        #TODO: ReWrite recent_follows such that vector does not become infinitely long ...
        global recent_follows
        recent_follows = list(bbl.get_recent_follows(days = 50))
        print len(recent_follows), "recent follows prevented from following here"
        try:
            print "last follow", recent_follows[-1]
        except IndexError:
            #in case no follows have been carried out yet.
            pass

        #self.tbuffer_status = tweet_buffer(api = self.api, ca = self.ca_st, management_fct=follow_management)

    def on_data(self, data):
        t = bbl.tweet2obj(data)
        #in case tweet cannot be put in object format just skip this tweet
        if not t:
            return True
        if t.user_screen_name == cfg.own_twittername:
            return True
        #Filter Tweets for url in tweet, number hashtags, language and location as in configuration
        if not bba.filter_tweets(t):
            return True
        if "dump_read" in vars(cfg):
            if cfg.dump_read == True:
                logr.info("$$DUMP",t.text, t.user_screen_name, t.description, t.created, t.id)
        #add score if tweet is relevant
        score = bba.score_tweets(t.text, verbose = verbose)
        #Manage Favorites
        if score >= cfg.favorite_score:
            if self.CSim.tweets_similar_list(t.text, self.ca_recent_f.get_list()):
                logr.info("favoriteprevented2similar;%s"%(t.id))
                return True
            self.tbuffer_fav.add_to_buffer(t, score)
            self.ca_recent_f.add(t.text, auto_increase = True)
        #Manage Status Updates
        if score >= cfg.status_update_score:
            url = bba.extract_url_from_tweet(t.text)
            if url:
                #return text and score from generated text. If no text is generated, TextBuilder will return 0 as score
                text, score2 = TextBuilder.build_text(url)
                #check if score2 also fulfills the score criteria
                if score2 < cfg.status_update_score:
                    return True
                #in case the text retrieved from the headline contains negative or forbidden keywords, don't send the update
                if text: #in some cases, text may be None.
                    if bba.score_tweets(text, verbose = verbose) < cfg.status_update_score:
                        return True
                    #Introduce some randomness such that not everything is automatically posted
                    if text and random.random() < cfg.status_update_prob:
                        if not ManageUpdatesPerDay.max_reached():
                            bbl.update_status(text = text, api = self.api, score = score)
                            ManageUpdatesPerDay.add_update()
                        else:
                            logr.info("$$MaxStatusUpdate;%d;%s"%(score, text))
                    elif text:
                        update_user_info.update_user_info(10)
                        logr.info("$$MissedStatusUpdate;%d;%s"%(score, text))
        #Manage Retweetssour
        if score >= cfg.retweet_score:
            if self.CSim.tweets_similar_list(t.text, self.ca_recent_r.get_list()):
                logr.info("retweetprevented2similar;%s"%(t.id))
                return True
            self.tbuffer_rt.add_to_buffer(t, score)
            self.ca_recent_r.add(t.text, auto_increase = True)
        #Manage Follows
        if score >= cfg.follow_score:
            #check with vars(cfg) if cfg contains follow_prob
            if "follow_prob" in vars(cfg):
                if random.random() > cfg.follow_prob:
                    return True
            #Check if the person to follow has been already followed in the past X days. In this case, do not follow again until this period is over.
            if int(t.user_id) in recent_follows:
                logr.info("refollowprevented;%s"%(t.user_id))
                return True
            self.tbuffer.add_to_buffer(t, score)
        return True

    def on_error(self, status):
        print "error: ",
        print status
        

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "Account Location has to be provided as a parameter")
    parser.add_argument('-l', '--location', help='account name', required=True)
    args = parser.parse_args()

    account_path = "../accounts/%s/"%args.location
    print account_path
    sys.path.append(account_path)
    try:
        import config as cfg
    except ImportError:
        print "Account %s does not exist" % args.location
        sys.exit(0)

    if cfg.own_twittername != args.location:
        print "serious error in starting: Twittername not same as account folder name!"
    print "running account:"
    print cfg.own_twittername

    hdlr_1 = logging.handlers.RotatingFileHandler("../accounts/%s/bluebird.log"%cfg.own_twittername, maxBytes=20000000, backupCount=5)
    hdlr_1.setFormatter(formatter)
    logr.setLevel(logging.INFO)
    logr.addHandler(hdlr_1)

    verbose = cfg.verbose

    import bblib as bbl
    bbl.set_cfg(cfg)
    bbl.initialize()

    import bbanalytics as bba
    bba.set_cfg(cfg)
    bba.initialize()
    ManageUpdatesPerDay = ManageUpdatesPerDay(cfg.max_updates_per_day)
    TextBuilder = bbl.BuildText(preambles = cfg.preambles, hashtags = cfg.hashtags)
    auth, api = bbl.connect_app_to_twitter()
    update_user_info = bbl.UpdateUserInfo(api = api, account_name = cfg.own_twittername)
    l = FavListener(api)
    stream = bbl.tweepy.Stream(auth, l)
    logr.info("EngineStarted")
    while True:
        try:
            stream.filter(track=bba.manage_keywords(cfg.keywords).keys())
        except KeyboardInterrupt:
            logr.info("EngineEnded")
            logging.shutdown()
            sys.exit()
        except httplib.IncompleteRead, e:
            logr.error("in main function; %s"%e)
        except Exception,e:
            logr.error("in main function; %s"%e)
            print "Exception in user code:"
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            time.sleep(2)
            pass
