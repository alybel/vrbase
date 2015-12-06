__author__ = 'alex'
from goose import Goose
g = Goose()

def get_ws_text_and_title(url):
    article = g.extract(url)
    a, b = "%s" % article.cleaned_text, "%s" % article.title
    return None, None

