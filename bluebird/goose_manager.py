__author__ = 'alex'
from goose import Goose
g = Goose({'browser_user_agent': 'Mozilla', 'parser_class':'soup'})

def get_ws_text_and_title(url = 'http://www.faz.net/aktuell/politik/kommentar-von-michaela-wiegel-zum-sieg-des-front-national-13953429.html'):

    article = g.extract(url)
    a, b = "%s" % article.cleaned_text, "%s" % article.title
    article = None
    return None, None

