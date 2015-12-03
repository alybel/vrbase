#!/usr/bin/env python
# This shebang uses the python that is currently activated

import logging
import logging.handlers
import sys
import traceback
import random
import argparse
import httplib
import collections
import time
import numpy.random as nr
import load_config

import datetime as dt

import tweepy

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

recent_follows = {}

# first file logger
logr = logging.getLogger('logger')
hdlr_1 = None
TextBuilder = None

class ManageUpdatesPerDay(object):
    def __init__(self, max_updates, use_timer=False):
        self.max_updates = max_updates
        self.no_updates = collections.defaultdict(int)
        self.use_timer = use_timer
        self.timer = collections.defaultdict(int)

    def max_reached(self):
        if not self.use_timer:
            return self.no_updates[bbl.get_today()] >= self.max_updates
        else:
            return self.no_updates[bbl.get_today()] >= self.max_updates or time.time() < self.timer[bbl.get_today()]

    def add_update(self):
        self.clean_dict(self.no_updates)
        self.clean_dict(self.timer)
        self.no_updates[bbl.get_today()] += 1
        if self.use_timer:
            wait_time = time.time() + min(nr.exponential(24 * 60 * 60. / self.max_updates),
                                                            2 * 60 * 60)
            self.timer[bbl.get_today()] = wait_time
            logr.info('$$WaitingTime set to %s' % wait_time)
        return

    @staticmethod
    def clean_dict(d):
        for key in d.keys():
            if not key == bbl.get_today():
                del d[key]


def lp(s):
    """print this line if verbose is true """
    if verbose:
        print s


def favorite_management(t, ca, api):
    if random.random() > 0.3:
        return False
    # check if ID is already favorited. If yes, interrupt.
    if ca.isin(t.id):
        return True
    status = bbl.add_favorite(t.id, api)
    if not status:
        return False
    ca.add(t.id)
    next_entry = ca.get_next_entry()
    if next_entry:
        # try except needed becasue users may not exist anymore in the future. removing them would then throw an error
        try:
            bbl.remove_favorite(next_entry, api)
        except:
            pass
    ca.increase_count()
    bbl.ca_save_state(ca, "favorites")
    return True


def retweet_management(t, ca, api):
    if random.random() > 0.3:
        return False
    lp("Entering Retweet Management")
    if ca.isin(t.id):
        return False
    rt_id = bbl.retweet(t.id, t.text, api)
    if not rt_id:
        return False
    ca.add(rt_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        # try except needed becasue retweets may not exist anymore in the future. removing them would then throw error
        try:
            bbl.remove_retweet(next_entry, api)
        except:
            pass
    ca.increase_count()
    bbl.ca_save_state(ca, "retweets")
    return True

def add_follow_to_watchlist(user_id):
    global recent_follows
    # add new follow
    recent_follows[dt.datetime.now()] = user_id
    logr.info('adding %s to recent_follows' % user_id)
    # kick out all follows which are older than 50 days
    for key in recent_follows.keys():
        if key < dt.datetime.now() - dt.timedelta(50):
            logr.info('cleaning recent_follows from old entries')
            del recent_follows[key]

def follow_management(t, ca, api):
    lp("entering follow management")
    if ca.isin(t.user_id):
        return False
    status = bbl.add_as_follower(t, api, verbose=verbose)
    if not status:
        return False
    ca.add(t.user_screen_name)
    add_follow_to_watchlist(t.user_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        # user may not exist any more in the future. hence errors here need to be catched.
        try:
            bbl.remove_follow(next_entry, api)
        except:
            pass
    ca.increase_count()
    bbl.ca_save_state(ca, "follows")
    wait = int(nr.rand() * 20)
    logr.info('Waiting %d seconds after follow' % wait)
    time.sleep(wait)
    return True


class TweetBuffer(object):
    """
    This Object is used for Retweet, Favorite and Follow management
    """
    def __init__(self, ca, api, management_fct, delta_time, max_number_actions=3):
        self.buffer = []
        self.ca = ca
        self.api = api
        self.management_fct = management_fct
        self.delta_time = delta_time
        self.max_number_actions = max_number_actions
        self.this_run_not_yet_carried_out = True
        lp("initiate tweet buffer")
        logr.info("initiate tweet buffer")

    def add_to_buffer(self, t, score):
        # Check if something in Buffer and if yes flush the buffer, else append to buffer
        if self.buffer and bba.minutes_of_day() % self.delta_time == 0:
            if self.this_run_not_yet_carried_out:
                self.flush_buffer()
                self.buffer = []
                self.this_run_not_yet_carried_out = False
        if bba.minutes_of_day() % self.delta_time != 0:
            self.this_run_not_yet_carried_out = True
        else:
            self.buffer.append((score, t))

    def flush_buffer(self):
        logr.info("Flush Buffer")
        lp("Flush Buffer!%s" % str(bba.minutes_of_day()))
        self.buffer.sort(reverse=True)
        for i in xrange(min(self.max_number_actions, len(self.buffer))):
            try:
                tweet = self.buffer[i][1]
            except IndexError:
                print self.buffer
                raise
            args = (tweet, self.ca, self.api)
            # Introduce some randomness such that not everything is retweeted favorited and statused
            self.management_fct(*args)
        return True


class FavListener(tweepy.StreamListener):

    def __init__(self, api):
        self.action_counter = 0
        tweepy.StreamListener.__init__(self)
        self.api = api
        # ca is a cyclic array that contains the tweet ID's there were favorited.
        # Once the number_active_favorites is reached,
        # the oldest favorite is automatically removeedd.
        self.ca = bbl.ca_initialize("favorites")
        # self.ca_r = bbl.ca_initialize("retweets")
        # self.ca_f = bbl.ca_initialize("follows")

        # build the followers cyclic array
        self.ca_f = bbl.CyclicArray(length=bbl.get_ca_len("follows"))
        self.ca_r = bbl.CyclicArray(length=bbl.get_ca_len("retweets"))
        # refresh followers and statusses
        bbl.cleanup_followers(api, ca_follow=self.ca_f, ca_stat=self.ca_r)

        self.ca_recent_r = bbl.CyclicArray(100)
        self.ca_recent_f = bbl.CyclicArray(100)

        self.ca.release_add_lock_if_necessary()
        self.ca_r.release_add_lock_if_necessary()
        self.ca_f.release_add_lock_if_necessary()

        self.CSim = bba.CosineStringSimilarity()

        # Buffers for all 4 Types of Interaction
        self.tbuffer = TweetBuffer(
            api=self.api, ca=self.ca_f, management_fct=follow_management,
            delta_time=cfg.activity_frequency, max_number_actions=3)
        self.tbuffer_rt = TweetBuffer(
            api=self.api, ca=self.ca_r, management_fct=retweet_management,
            delta_time=cfg.activity_frequency)
        self.tbuffer_fav = TweetBuffer(
            api=self.api, ca=self.ca, management_fct=favorite_management,
            delta_time=cfg.activity_frequency)

        recent_follows_from_file = list(bbl.get_recent_follows(days=50))
        print recent_follows_from_file
        for user_id in recent_follows_from_file:
            time.sleep(0.01)
            add_follow_to_watchlist(user_id)

    def on_data(self, data):
        t = bbl.tweet2obj(data)
        # in case tweet cannot be put in object format just skip this tweet
        self.action_counter += 1
        if self.action_counter > 200:
            logr.info("$$ActionCounterAnother200")
            self.action_counter = 0
        if t is None:
            return True

        if t.user_screen_name == cfg.own_twittername:
            return True

        # Filter Tweets for url in tweet, number hashtags, language and location as in configuration
        if not bba.filter_tweets(t):
            return True

        if "dump_read" in vars(cfg):
            if cfg.dump_read:
                # logr.info("$$DUMP", t.text, t.user_screen_name, t.description, t.created, t.id)
                with open('/home/vr/dumps/feed.txt', 'a+') as f:
                    f.write(data)
        # add score if tweet is relevant
        score = bba.score_tweets(t.text, verbose=verbose)
        # Manage Favorites

        if score >= cfg.favorite_score:
            if not self.CSim.tweets_similar_list(t.text, self.ca_recent_f.get_list()):
                self.tbuffer_fav.add_to_buffer(t, score)
                self.ca_recent_f.add(t.text, auto_increase=True)
            else:
                #logr.info("favoriteprevented2similar;%s" % t.id)
                pass
        # Manage Status Updates

        if score >= cfg.status_update_score:
            url = bba.extract_url_from_tweet(t.text)
            if url:
                # return text and score from generated text. If no text is generated, TextBuilder will return 0 as score
                text, score2 = TextBuilder.build_text(url)
                # check if score2 also fulfills the score criteria
                if score2 > cfg.status_update_score:
                    update_candidate = True
                else:
                    update_candidate = False
                    logr.info("$$MissedStatusUpdateStatusScoreTooLow;%d;%s;%s" % (score2, text, url))
                # in case the text retrieved from the headline contains negative or
                # forbidden keywords, don't send the update
                if update_candidate and text:  # in some cases, text may be None.
                    if bba.score_tweets(text, verbose=verbose) < cfg.status_update_score:
                        update_candidate = False
                        logr.info("$$MissedStatusUpdateStatusScoreTooLowStage2;%d;%s;%s" % (score2, text, url))
                    # Introduce some randomness such that not everything is automatically posted
                    if update_candidate and text and random.random() < cfg.status_update_prob:
                        if not ManageUpdatesPerDay.max_reached():
                            bbl.update_status(text=text, api=self.api, score=score)
                            ManageUpdatesPerDay.add_update()
                        else:
                            logr.info("$$MaxStatusUpdateMaxPerDayReached;%d;%s" % (score, text))
                    elif text:
                        logr.info("$$MissedStatusUpdateRejectedByRandomOrTextScore;%d;%s" % (score, text))
                    else:
                        logr.info("$$MissedStatusUpdateNoText;%d;%s" % (score, text))
                        
        if score >= cfg.retweet_score:
            logr.info('entering retweet area, retweet_score is %d;size of ca_recent_r: %s' %
                      (cfg.retweet_score, sys.getsizeof(self.ca_recent_r)))
            if not self.CSim.tweets_similar_list(t.text, self.ca_recent_r.get_list()):
                self.tbuffer_rt.add_to_buffer(t, score)
                self.ca_recent_r.add(t.text, auto_increase=True)
                logr.info('$$CandidateRetweet;%d;%s' % (score, t.text))
            else:
                #logr.info("retweetprevented2similar;%s" % t.id)
                pass
        # Manage Follows
        if score >= cfg.follow_score:
            # check with vars(cfg) if cfg contains follow_prob
            if "follow_prob" in vars(cfg):
                if random.random() > cfg.follow_prob:
                    return True
            # Check if the person to follow has been already followed in the past X days.
            # In this case, do not follow again until this period is over.
            if int(t.user_id) in recent_follows.values():
                logr.info("refollowprevented;%s" % t.user_id)
                return True
            self.tbuffer.add_to_buffer(t, score)
        return True

    @staticmethod
    def on_error(status):
        print "error: ",
        print status


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Account Location has to be provided as a parameter")
    parser.add_argument('-l', '--location', help='account name', required=True)
    sysargs = parser.parse_args()

    account_path = "../accounts/%s/" % sysargs.location
    print account_path
    
    #ToDo properly catch cases where no db entry was found
    try:
        # Try to load from database
        cfg = load_config.load_config(sysargs.location)
        load_config.check_if_folder_exists_or_create(cfg.own_twittername)
    except AttributeError: #Bad method of checking this
        #No database entry found
        try:
            sys.path.append(account_path)
            import config as cfg
        except:
            print "Account %s does not exist" % sysargs.location
            sys.exit(0)
    print cfg.keywords
    if cfg.own_twittername != sysargs.location:
        print "serious error in starting: Twittername not same as account folder name!"
    print "running account:"
    print cfg.own_twittername

    hdlr_1 = logging.handlers.RotatingFileHandler("../accounts/%s/bluebird.log" % cfg.own_twittername,
                                                  maxBytes=20000000, backupCount=5)
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
    ManageUpdatesPerDay = ManageUpdatesPerDay(cfg.max_updates_per_day, use_timer=True)
    # TODO below object not yet in use. Find proper use of it in a place where it
    # not called to oftern
    TextBuilder = bbl.BuildText(preambles=cfg.preambles, hashtags=cfg.hashtags)
    auth, global_api = bbl.connect_app_to_twitter()
    bbl.set_api(global_api)
    update_user_info = bbl.UpdateUserInfo(api=global_api, account_name=cfg.own_twittername)
    l = FavListener(global_api)
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
            logr.info("in main function; %s" % e)
        except Exception, e:
            logr.error("in main function; %s" % e)
            print "Exception in user code:"
            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60
            time.sleep(2)
            # ToDo remove the below line to guarantee ongoing operations
            sys.exit()
