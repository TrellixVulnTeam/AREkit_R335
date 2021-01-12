from collections import OrderedDict

from arekit.common.evaluation.results import metrics
from arekit.common.evaluation.results.base import BaseEvalResult
from arekit.common.evaluation.results.utils import calc_f1_single_class, calc_f1
from arekit.common.labels.base import PositiveLabel, NegativeLabel, Label
from arekit.common.opinions.collection import OpinionCollection


class TwoClassEvalResult(BaseEvalResult):

    C_F1 = u'f1'
    C_POS_PREC = u'pos_prec'
    C_NEG_PREC = u'neg_prec'
    C_POS_RECALL = u'pos_recall'
    C_NEG_RECALL = u'neg_recall'
    C_F1_POS = u'f1_pos'
    C_F1_NEG = u'f1_neg'

    def __init__(self):
        super(TwoClassEvalResult, self).__init__()
        self.__doc_results = OrderedDict()
        self.__pos_label = PositiveLabel()
        self.__neg_label = NegativeLabel()

    @staticmethod
    def __has_opinions_with_label(opinions, label):
        assert(isinstance(label, Label))
        assert(isinstance(opinions, OpinionCollection))
        for opinion in opinions:
            if opinion.Sentiment == label:
                return True
        return False

    def reg_doc(self, cmp_pair, cmp_table):
        super(TwoClassEvalResult, self).reg_doc(cmp_pair=cmp_pair,
                                                cmp_table=cmp_table)

        has_pos = self.__has_opinions_with_label(
            opinions=cmp_pair.EtalonOpinionCollection,
            label=self.__pos_label)

        has_neg = self.__has_opinions_with_label(
            opinions=cmp_pair.EtalonOpinionCollection,
            label=self.__neg_label)

        pos_prec, pos_recall = metrics.calc_prec_and_recall(cmp_table=cmp_table,
                                                            label=self.__pos_label,
                                                            opinions_exist=has_pos)

        neg_prec, neg_recall = metrics.calc_prec_and_recall(cmp_table=cmp_table,
                                                            label=self.__neg_label,
                                                            opinions_exist=has_neg)

        # Add document results.
        f1 = calc_f1(pos_prec=pos_prec,
                     neg_prec=neg_prec,
                     pos_recall=pos_recall,
                     neg_recall=neg_recall)

        # Filling results.
        doc_id = cmp_pair.DocumentID
        self.__doc_results[doc_id] = OrderedDict()
        self.__doc_results[doc_id][self.C_F1] = f1
        self.__doc_results[doc_id][self.C_POS_PREC] = pos_prec
        self.__doc_results[doc_id][self.C_NEG_PREC] = neg_prec
        self.__doc_results[doc_id][self.C_POS_RECALL] = pos_recall
        self.__doc_results[doc_id][self.C_NEG_RECALL] = neg_recall

    def calculate(self):
        pos_prec, neg_prec, pos_recall, neg_recall = (0.0, 0.0, 0.0, 0.0)

        for info in self.__doc_results.itervalues():
            pos_prec += info[self.C_POS_PREC]
            neg_prec += info[self.C_NEG_PREC]
            pos_recall += info[self.C_POS_RECALL]
            neg_recall += info[self.C_NEG_RECALL]

        if len(self.__doc_results) > 0:
            pos_prec /= len(self.__doc_results)
            neg_prec /= len(self.__doc_results)
            pos_recall /= len(self.__doc_results)
            neg_recall /= len(self.__doc_results)

        f1 = calc_f1(pos_prec=pos_prec,
                     neg_prec=neg_prec,
                     pos_recall=pos_recall,
                     neg_recall=neg_recall)

        # Filling total result.
        self._total_result[self.C_F1] = f1
        self._total_result[self.C_F1_POS] = calc_f1_single_class(prec=pos_prec, recall=pos_recall)
        self._total_result[self.C_F1_NEG] = calc_f1_single_class(prec=neg_prec, recall=neg_recall)
        self._total_result[self.C_POS_PREC] = pos_prec
        self._total_result[self.C_NEG_PREC] = neg_prec
        self._total_result[self.C_POS_RECALL] = pos_recall
        self._total_result[self.C_NEG_RECALL] = neg_recall

    def iter_document_results(self):
        return self.__doc_results.iteritems()
