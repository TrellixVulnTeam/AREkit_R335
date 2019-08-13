import collections

from core.evaluation.evaluators.base import BaseEvaluator
from core.common.synonyms import SynonymsCollection
from core.networks.eval.base import EvaluationHelper
from core.networks.network_io import NetworkIO


class OpinionBasedEvaluationHelper(EvaluationHelper):

    def __init__(self, evaluator):
        assert(isinstance(evaluator, BaseEvaluator))
        self.__evaluator = evaluator

    def evaluate_model(self, data_type, io, doc_ids, synonyms):
        assert(isinstance(io, NetworkIO))
        assert(isinstance(doc_ids, collections.Iterable))
        assert(isinstance(synonyms, SynonymsCollection) and synonyms.IsReadOnly)

        opinions_cmp = io.iter_opinion_collections_to_compare(data_type=data_type,
                                                              synonyms=synonyms,
                                                              doc_ids=doc_ids)

        return self.__evaluator.evaluate(cmp_pairs=opinions_cmp)
