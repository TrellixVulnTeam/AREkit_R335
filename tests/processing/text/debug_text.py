import logging
from arekit.common.entities.base import Entity
from arekit.common.news.parsed.base import ParsedNews
from arekit.common.text_frame_variant import TextFrameVariant
from arekit.processing.text.token import Token


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


def debug_show_news_terms(parsed_news):
    assert(isinstance(parsed_news, ParsedNews))
    logger.info('------------------------')
    return debug_show_terms(terms=parsed_news.iter_terms())


def debug_show_terms(terms):
    for term in terms:
        if isinstance(term, str):
            logger.debug("Word:\t\t'{}'".format(term))
        elif isinstance(term, Token):
            logger.debug("Token:\t\t'{}' ('{}')".format(term.get_token_value(),
                                                        term.get_meta_value()))
        elif isinstance(term, Entity):
            logger.debug("Entity:\t\t'{}'".format(term.Value))
        elif isinstance(term, TextFrameVariant):
            logger.debug("TextFV:\t\t'{}'".format(term.Variant.get_value()))
        else:
            raise Exception("unsuported type {}".format(term))