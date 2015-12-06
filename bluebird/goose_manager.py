__author__ = 'alex'

def get_ws_text_and_title(url):
    from goose import Goose
    g = Goose()
    article = g.extract(url)
    del article
    del g
    del Goose
    a, b = article.cleaned_text, article.title
    return a, b

