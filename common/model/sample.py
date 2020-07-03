from collections import OrderedDict

from arekit.common.dataset.text_opinions.enums import DistanceType
from arekit.common.dataset.text_opinions.helper import TextOpinionHelper


class InputSampleBase(object):
    """
    Description of a single sample (context) of a model
    """

    def __init__(self, text_opinion_id, values):
        assert(isinstance(values, list))

        self.__text_opinion_id = text_opinion_id
        self.__values = OrderedDict(values)

    # region properties

    @property
    def TextOpinionID(self):
        return self.__text_opinion_id

    # endregion

    @staticmethod
    def check_ability_to_create_sample(window_size, text_opinion, text_opinion_helper):
        """
        Main text_opinion filtering rules
        """
        assert(isinstance(text_opinion_helper, TextOpinionHelper))

        if text_opinion_helper.calc_dist_between_text_opinion_ends(text_opinion, DistanceType.InTerms) < window_size:
            return True

        if text_opinion_helper.calc_dist_between_text_opinion_ends(text_opinion, DistanceType.InSentences) == 0:
            return True

        return False

    def __iter__(self):
        for key, value in self.__values.iteritems():
            yield key, value
