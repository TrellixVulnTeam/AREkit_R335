# -*- coding: utf-8 -*-
import io
from core.common.opinions.collection import OpinionCollection
from core.evaluation.labels import Label
from core.common.synonyms import SynonymsCollection
from core.source.rusentrel.io_utils import RuSentRelIOUtils
from core.source.rusentrel.opinions.opinion import RuSentRelOpinion


class RuSentRelOpinionCollection(OpinionCollection):
    """
    Collection of sentiment opinions between entities
    """

    @classmethod
    def read_collection(cls, doc_id, synonyms):
        return RuSentRelIOUtils.read_opinions(
            doc_id=doc_id,
            process_func=lambda input_file: cls.__from_file(input_file, synonyms))

    @classmethod
    def __from_file(cls, input_file, synonyms):
        assert(isinstance(synonyms, SynonymsCollection))

        opinions = []
        for i, line in enumerate(input_file.readlines()):

            line = line.decode('utf-8')

            if line == '\n':
                continue

            args = line.strip().split(',')
            print args
            assert(len(args) >= 3)

            value_source = args[0].strip()
            value_target = args[1].strip()
            sentiment = Label.from_str(args[2].strip())

            o = RuSentRelOpinion(value_source=value_source,
                                 value_target=value_target,
                                 sentiment=sentiment)
            opinions.append(o)

        return cls(opinions, synonyms)

    @staticmethod
    def __opinion_to_str(opinion):
        assert(isinstance(opinion, RuSentRelOpinion))
        return u"{}, {}, {}, current".format(
            opinion.SourceValue,
            opinion.TargetValue,
            opinion.Sentiment.to_str())

    def save(self, filepath):
        assert(isinstance(filepath, unicode))

        def __opinion_key(opinion):
            assert(isinstance(opinion, RuSentRelOpinion))
            return opinion.SourceValue + opinion.TargetValue

        sorted_ops = sorted(self, key=__opinion_key)

        with io.open(filepath, 'w') as f:
            for o in sorted_ops:
                f.write(self.__opinion_to_str(o))
                f.write(u'\n')
