from arekit.contrib.bert.formatters.opinions.provider import OpinionProvider
from arekit.contrib.bert.formatters.row_ids.base import BaseIDFormatter


class BinaryIDFormatter(BaseIDFormatter):
    """
    Considered that label of opinion IS A PART OF id.
    """

    @staticmethod
    def create_sample_id(opinion_provider, linked_opinions, index_in_linked):
        assert(isinstance(opinion_provider, OpinionProvider))
        assert(isinstance(linked_opinions, list))
        assert(isinstance(index_in_linked, int))

        o_id = BaseIDFormatter.create_opinion_id(
            opinion_provider=opinion_provider,
            linked_opinions=linked_opinions,
            index_in_linked=index_in_linked)

        return u"{multiple}_l{label}".format(
            multiple=o_id,
            label=opinion_provider.get_linked_sentiment(linked_opinions))


