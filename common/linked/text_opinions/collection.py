# -*- coding: utf-8 -*-
import logging
import collections

from arekit.common.linked.text_opinions.wrapper import LinkedTextOpinionsWrapper
from arekit.common.text_opinions.base import TextOpinion
from arekit.common.text_opinions.collection import BaseTextOpinionCollection


logger = logging.getLogger(__name__)


class LinkedTextOpinionCollection(BaseTextOpinionCollection):
    """
    Describes text opinions with a position precision and forward connection

    Limitations:
    Not it represents IN-MEMORY implementation.
    Therefore it is supposed not so large amount of linked_text_opinions.
    """

    NO_NEXT_OPINION = None

    def __init__(self):
        super(LinkedTextOpinionCollection, self).__init__(text_opinions=[])

        # list describes that has i'th relation continuation in text.
        self.__next_opinion_id = []

    # region private methods

    def __set_none_for_last_text_opinion(self):
        self.__next_opinion_id[-1] = self.NO_NEXT_OPINION

    # endregion

    # region protected methods

    def _remove_last_registered_text_opinion(self):
        super(LinkedTextOpinionCollection, self)._remove_last_registered_text_opinion()
        del self.__next_opinion_id[-1]

    def _register_text_opinion(self, text_opinion):
        assert(isinstance(text_opinion, TextOpinion))
        super(LinkedTextOpinionCollection, self)._register_text_opinion(text_opinion)
        self.__next_opinion_id.append(text_opinion.TextOpinionID + 1)

    # endregion

    def try_add_text_opinions(self, text_opinions_iter, check_opinion_correctness):
        """
        linked_text_opinions: iterable
            enumeration of text_opinions which are related to a certain opinion
            (in terms of Obj, Subj).
        check_opinion_correctness: bool
        """
        assert(isinstance(text_opinions_iter, collections.Iterable))
        assert(callable(check_opinion_correctness))

        discarded = 0
        registered_at_least_one = False
        for index, text_opinion in enumerate(text_opinions_iter):
            assert(isinstance(text_opinion, TextOpinion))
            assert(text_opinion.TextOpinionID is None)
            assert(text_opinion.Owner is None)

            registered = TextOpinion.create_copy(text_opinion)
            registered.set_owner(self)
            registered.set_text_opinion_id(len(self))

            self._register_text_opinion(registered)

            if not check_opinion_correctness(registered):
                discarded += 1
                self._remove_last_registered_text_opinion()
                del registered
            else:
                registered_at_least_one = True

        if registered_at_least_one:
            self.__set_none_for_last_text_opinion()

        return discarded

    # region iter methods

    def iter_wrapped_linked_text_opinions(self, news_id=None):
        assert(isinstance(news_id, int) or news_id is None)

        for linked_wrap in self.__iter_by_linked_text_opinions():
            if news_id is not None and linked_wrap.RelatedNewsID != news_id:
                continue

            yield linked_wrap

    def __iter_by_linked_text_opinions(self):
        linked_opinions = []
        for index, text_opinion in enumerate(self):
            linked_opinions.append(text_opinion)
            if self.__next_opinion_id[index] == self.NO_NEXT_OPINION:
                yield LinkedTextOpinionsWrapper(linked_text_opinions=linked_opinions)
                linked_opinions = []

    # endregion
