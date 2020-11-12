from arekit.common.news.entities_parser import BaseEntitiesParser


class News(object):

    def __init__(self, news_id, sentences, entities_parser):
        assert(isinstance(news_id, int))
        assert(isinstance(sentences, list))
        assert(isinstance(entities_parser, BaseEntitiesParser))
        self.__news_id = news_id
        self.__entities_parser = entities_parser

        self._sentences = sentences

    # region properties

    @property
    def ID(self):
        return self.__news_id

    @property
    def EntitiesParser(self):
        return self.__entities_parser

    @property
    def SentencesCount(self):
        """ Provides total amount of sentences within a news
            At present is useful in specific CV-splitters, which may rely on sentences count.
        """
        raise NotImplementedError()

    # endregion

    def iter_sentences(self, return_text):
        """
        return: list of string
            iterates per raw sentences.
        """
        assert(isinstance(return_text, bool))

        for sentence in self._sentences:
            if return_text:
                yield sentence.Text
            else:
                yield sentence

    def extract_text_opinions(self, opinion):
        """
        opinions: iterable Opinion
            is an iterable opinions that should be used to find a related text_opinion entries.
        """
        raise NotImplementedError()
