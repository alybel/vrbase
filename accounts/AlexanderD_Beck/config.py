consumer_key = "ZWjpgmBvr7S9254IJp0Rw"
consumer_secret = "aXtSxw6Jxc8aZhMJPQCWz3gplR0ttUPArMily86JI"
access_token = "317005063-xDIynEL3JE2059IEpYXhErvOX4nRVgtFlB9qedAG"
access_token_secret = "jtZb6CrucwE5ZNP5BoYGBskMDyZ7GSfbnMjm5aifXQQg7"

own_twittername = "AlexanderD_Beck"


# choose between 1 and 5 points for positive impact on score
keywords = {
    "predictive analytics": 5
    , "data analytics": 5
    , "data science": 5
    , "data scientist": 5
    , "analytics tools": 4
    , "data visualization": 4
    , "data mining": 3
    , "python": 3
    , "scikit": 5
    , "machine learning": 5
    , "deep learning": 5
    , "rstudio": 3
    , "business analytics": 4
    , "prescriptive analytics": 5
    , "hadoop": 2
    , "big data": 3
    , "summary": 2
    , "overview": 2
    , "innovation": 2
    , "technology": 2
    , "business strategy": 4
    , "transform": 3
    , "credit": 3
    , "finance": 3
    , "trading": 3
    , "change management": 3
    , "manufacturing": 3
    , "internet of things": 6
    , "iot" :5
    , "fintech":10
    , "random forests":6
    , "neural networks":6
    , "artificial intelligence":5
    , "outlier detection": 5
    , "anomaly detection": 5
    , "unsupervised learning": 5
    , "supervised learning": 5
    , "dimensionality reduction" :5
}

#remove plural s, check for combined wrods. and if they are joint



negative_keywords = ["price", "shop", "advertising", "ebay", "marketing", "music", "buy", "free", "only", "cheap",
                     "guarantee", "birthday", "job", "offer", "discount", "local", "ibm", "sap", "jobs"]
forbidden_keywords = ["job", "sas", "spss", "knime", "rapidminer", "sap", "ibm", "microsoft", "azure", "oracle"]

languages = ["de", "en"]
locations = []

verbose = False

only_with_url = True

number_active_favorites = 121
number_active_retweets = 511
number_active_follows = 1823

#the higher the score the more exact do tweets match your needs but less tweets per time unit will be considered
favorite_score = 10
retweet_score = 10
follow_score = 10
status_update_score = 11
dump_score = 50

#Set the maximum number of hastags you would like to favorite in a tweet. Set -1 to ignore this option.
number_hashtags = 3


preambles = ["must read for all social media marketers:", "read this to stay tuned:", "very nice summary:", "couldn't have summed it up better:", "really insightful:",
            "must read article:", "nice to read:", "great article! ", "have a look at this: ", "very exciting! ", "must read! :", "don't miss on that: "]
hashtags = ["#datascience", "#bigdata", "#machinelearning", "#deeplearning", "#innovation", "#tech", "#ai"]

accounts_never_delete = ["WeissU", "hmason", "todd_park", "kdnuggets",
                         "dgruessi", "shoerand", "donvolkmar", "trieloff", "lisachwinter"]

activity_frequency = 30

#set the frequency for status updates
status_update_prob=0.2
