__author__ = 'alex'
from memory_profiler import profile


@profile
def get_ws_text_and_title(url):
    from goose import Goose
    g = Goose()
    article = g.extract(url)

    del g
    del Goose
    a, b = "%s" % article.cleaned_text, "%s" % article.title
    del article
    return a, b

