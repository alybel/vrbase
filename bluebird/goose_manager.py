__author__ = 'alex'

def get_ws_text_and_title(url):
    from goose import Goose
    g = Goose()
    #logr.info(sys.getsizeof(g))
    #logr.info(sys.getsizeof(Goose))
    article = g.extract(url)
    #logr.info(sys.getsizeof(article))
    return article.cleaned_text, article.title
