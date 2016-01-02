#! /usr/bin/python -u

import sys
import os.path
import time
valureach_ops_path = "/home/vr/valureach_ops"
sys.path.append("%s/bluebird" % valureach_ops_path)
import bblib as bbl
import random
import vr_main
import subprocess

def rtime():
    return int(random.random() * 10 * 60)

def tweet_account(account_name=""):
    print "starting", account_name
    account_path = "%s/accounts/%s/" % (valureach_ops_path, account_name)
    if not os.path.isfile("%s/tweet.py" % account_path):
        return False
    sys.path.append(account_path)
    import config as cfg
    import tweet
    bbl.set_cfg(cfg)
    auth, api = bbl.connect_app_to_twitter()
    #Check for correct frequency
    freq = tweet.freq * 60
    logfile = "%stweet_engine.log" % account_path
    if os.path.isfile(logfile):
        with open(logfile, 'r') as f:
            for line in f:
                if "tweetid" in line:
                    tweet_id =line.strip("\n").split(":")[1]
                    try:
                        api.destroy_status(tweet_id)
                        print account_name,"tweet destroyed in ramping up", tweet_id
                    except:
                        pass
        #reset the logfile
        f = open(logfile, "w")
        f.close()
    while True:
        #Tweet own tweets
        sel_tweet = random.choice(tweet.tweets)
        print "selected tweet:", sel_tweet
        res = api.update_status(sel_tweet)
        with open(logfile, 'a') as f:
            f.write("tweetid:%d\n" % res.id)
        print account_name, "tweeted:", sel_tweet
        time.sleep(rtime())
        #retweet tweets from friended accounts
        for account in tweet.watch_account:
            print "seeking for tweets to retweet in", account
            apath = "%s/accounts/%s/" % (valureach_ops_path, account)
            lf = "%stweet_engine.log"%apath
            if not os.path.isfile(lf):
                continue
            with open(lf,'r') as f2:
                for line in f2:
                    print line
                    if "tweetid" in line:
                        tweet_id  = line.strip("\n").split(":")[1]
                        print "tweet_id", tweet_id
                        try:
                            api.retweet(tweet_id)
                            print "retweeted", tweet_id
                        except Exception,e:
                            print e
                            print "retweet not carried out", tweet_id
        print "reached sleep point"
        time.sleep(freq)
        #remove own tweets
        try:
            api.destroy_status(res.id)
        except:
            pass
        print account_name, "status deleted"
        with open(logfile, 'a') as f:
            f.write("deleted-tweetiid:%d\n"%res.id)
        f = open(logfile, "w")
        f.close()
        time.sleep(rtime())

def clean_account(account, api = None):
    """
    not used yet
    """
    if not api:
        api = get_account_api(account)
    account_path = "%s/accounts/%s/" % (valureach_ops_path, account_name)
    logfile = "%stweet_engine.log"%account_path
    if os.path.isfile(logfile):
        with open(logfile, 'r') as f:
            for line in f:
                if "tweetid" in line:
                    tweet_id  = line.strip("\n").split(":")[1]
                    try:
                        api.destroy_status(tweet_id)
                        print account_name,"tweet destroyed in ramping up", tweet_id
                    except:
                        pass   
        
def get_account_api(account):
    account_path = "%s/accounts/%s/" % (valureach_ops_path, account_name)
    sys.path.append(account_path)
    import config as cfg
    bbl.set_cfg(cfg)  
    auth, api = bbl.connect_app_to_twitter()
    return api

def start_account(account):
    if os.path.isfile("accounts/%s/.tweet_engine_lock" % account):
        print "tweet engine Account", account, "is locked. is already running?"
        return False
    print "starting account", account
    with open("stdout/tweet_engine_%s.out" % account, "w") as f:
        subprocess.Popen(["python", "tweet_engine.py", "%s" % account], stdout=f)
    subprocess.call(["touch","accounts/%s/.tweet_engine_lock" % account])
    return True  

def stop_account(account):
    procname = "tweet_engine.py"
    subprocess.call(["rm","accounts/%s/.tweet_engine_lock" % account])
    print "lockfile removed"
    for proc in psutil.process_iter():
        if proc.name() == procname and account in proc.cmdline()[-1]:
            print "killing", proc.cmdline()
            psutil.Process(proc.pid).kill()
            return True
    if not auto_call:
        print "no running tweet engine proccess for account", account, "could be found"
    return False

def remove_all_lockfiles():
    accounts = vr_main.get_accounts()
    for account in accounts:
        subprocess.call(["rm","accounts/%s/.tweet_engine_lock" % account])
    print "all tweet_engine lockfiles removed"

def start_all():
    accounts = vr_main.get_accounts()
    for account in accounts:
        start_account(account)

if __name__ == "__main__":
    args = sys.argv
    if not len(args) == 2:
        print "usage: tweet_engine.py <account_name>"
        print "other options: all, stopall"
        sys.exit()
    print "starting for account", args[1]
    if args[1] == "all":
        start_all()
    elif args[1] == "stopall":
        subprocess.call(["killall", "tweet_engine.py"])
        subprocess.call(["killall", "tweet_engine.py"])
        remove_all_lockfiles()
        
    else:
        tweet_account(args[1])
