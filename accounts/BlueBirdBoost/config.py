consumer_key = "UdTH9au9lT1Wpp4USFcCi7m5l"
consumer_secret = "9gfsgvJWNlUWijhPDKH42mJdiG7i5cy7RKCVY0JLhmTvAdo2zO"
access_token = "2853276243-LXxoxLDuCRzTYU9NJO8dcBGiBwCyQdMxmMElnin"
access_token_secret = "IfKD1WUYp8PgJAR1WRC6pZjQvt9FZ43yUi8DLgmbjMHPi"

own_twittername = "BlueBirdBoost"


# choose between 1 and 5 points for positive impact on score
keywords = {
    "social": 3
    , "media": 3
    , "socialmedia": 5
    , "automation": 4
    , "amu": 4
    , "online": 2
    , "advertising": 5
    , "automated": 4
    , "promote": 4
    , "advert": 4
    ,"analytic":4
    ,"analysis":4
    ,"marketing":4
    ,"monitoring":4
    ,"revenue":3
    ,"bigdata":2
    ,"internet":2
    ,"manager":3
    ,"CMO":4
    ,"consumer":5
    ,"product":4
    ,"increase":4
    ,"content":4
    ,"follower":3
    ,"audience":3
    ,"share":2
    ,"community":3
    ,"network":4
    ,"viral":5
    ,"tool":3
    ,"impact":4
    ,"sales":3
    ,"whitepaper":4
}

#remove plural s, check for combined wrods. and if they are joint



negative_keywords = ["price", "shop","ebay", "marketing", "music", "buy", "free", "only", "cheap",
                     "guarantee", "birthday", "job", "offer", "discount", "local", "ibm", "sap", "jobs"]
forbidden_keywords = ["job"]

languages = ["de", "en"]
locations = []

verbose = False

only_with_url = True

number_active_favorites = 120
number_active_retweets = 323
number_active_follows = 1932

#the higher the score the more exact do tweets match your needs but less tweets per time unit will be considered
favorite_score = 10
retweet_score = 10
follow_score = 10
status_update_score = 10

#Set the maximum number of hastags you would like to favorite in a tweet. Set -1 to ignore this option.
number_hashtags = 3

preambles = ["must read for all social media marketers:", "read this to stay tuned:", "very nice summary:", "couldn't have summed it up better:", "really insightful:",
            "must read article:", "nice to read:", "great article! "]

hashtags = ["#socialmedia", "#socialmediamarketing", "#twittermarketing", "#contentmarketing", "#marketingautomation", "#marketing", "#onlinemarketing", "#socmed", "#digital", "#content"]

accounts_never_delete = []

activity_frequency = 15

#this number regulates the frequency of status updates. the higher ne number the more updates there will be. should be between 0 and 1
status_update_prob=0.2
