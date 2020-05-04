import logging

from arekit.processing.lemmatization.mystem import MystemWrapper
from arekit.source.ruattitudes.news.base import RuAttitudesNews
from arekit.source.ruattitudes.reader import RuAttitudesFormatReader


if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    stemmer = MystemWrapper()
    reader = RuAttitudesFormatReader()

    ids = set()
    for news in reader.iter_news(stemmer):
        assert(isinstance(news, RuAttitudesNews))
        if news.ID in ids:
            logging.debug("index already exist: {}".format(news.ID))
        ids.add(news.ID)

    logger.debug("OK")
