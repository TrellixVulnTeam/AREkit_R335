import collections
from collections import OrderedDict

from arekit.common.evaluation.results.base import BaseEvalResult
from arekit.common.evaluation.results.utils import calc_f1_single_class, calc_f1_macro
from arekit.common.labels.base import Label
from arekit.contrib.utils.evaluation.results import metrics


class TwoClassEvalResult(BaseEvalResult):

    C_F1 = 'f1'
    C_POS_PREC = 'pos_prec'
    C_NEG_PREC = 'neg_prec'
    C_POS_RECALL = 'pos_recall'
    C_NEG_RECALL = 'neg_recall'
    C_F1_POS = 'f1_pos'
    C_F1_NEG = 'f1_neg'

    def __init__(self, label1, label2, get_item_label_func):
        assert(isinstance(label1, Label))
        assert(isinstance(label2, Label))
        assert(callable(get_item_label_func))

        self.__doc_results = OrderedDict()

        self.__pos_label = label1
        self.__neg_label = label2
        self.__get_item_label_func = get_item_label_func

        super(TwoClassEvalResult, self).__init__(
            supported_labels={self.__pos_label, self.__neg_label})

        self.__using_labels = {self.__pos_label, self.__neg_label}

    def __has_opinions_with_label(self, data_items, label):
        assert(isinstance(data_items, collections.Iterable))
        assert(isinstance(label, Label))

        for item in data_items:
            if self.__get_item_label_func(item) == label:
                return True
        return False

    def reg_doc(self, cmp_pair, cmp_table):
        super(TwoClassEvalResult, self).reg_doc(cmp_pair=cmp_pair,
                                                cmp_table=cmp_table)

        has_pos = self.__has_opinions_with_label(
            data_items=cmp_pair.EtalonData,
            label=self.__pos_label)

        has_neg = self.__has_opinions_with_label(
            data_items=cmp_pair.EtalonData,
            label=self.__neg_label)

        pos_prec, pos_recall = metrics.calc_prec_and_recall(cmp_table=cmp_table,
                                                            label=self.__pos_label,
                                                            opinions_exist=has_pos)

        neg_prec, neg_recall = metrics.calc_prec_and_recall(cmp_table=cmp_table,
                                                            label=self.__neg_label,
                                                            opinions_exist=has_neg)

        # Add document results.
        f1 = calc_f1_macro(pos_prec=pos_prec,
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
        pos_prec_macro, neg_prec_macro, pos_recall_macro, neg_recall_macro = (0.0, 0.0, 0.0, 0.0)

        for info in self.__doc_results.values():
            pos_prec_macro += info[self.C_POS_PREC]
            neg_prec_macro += info[self.C_NEG_PREC]
            pos_recall_macro += info[self.C_POS_RECALL]
            neg_recall_macro += info[self.C_NEG_RECALL]

        if len(self.__doc_results) > 0:
            pos_prec_macro /= len(self.__doc_results)
            neg_prec_macro /= len(self.__doc_results)
            pos_recall_macro /= len(self.__doc_results)
            neg_recall_macro /= len(self.__doc_results)

        f1 = calc_f1_macro(pos_prec=pos_prec_macro,
                           neg_prec=neg_prec_macro,
                           pos_recall=pos_recall_macro,
                           neg_recall=neg_recall_macro)

        # Filling total result.
        self._total_result[self.C_F1] = f1
        self._total_result[self.C_F1_POS] = calc_f1_single_class(prec=pos_prec_macro, recall=pos_recall_macro)
        self._total_result[self.C_F1_NEG] = calc_f1_single_class(prec=neg_prec_macro, recall=neg_recall_macro)
        self._total_result[self.C_POS_PREC] = pos_prec_macro
        self._total_result[self.C_NEG_PREC] = neg_prec_macro
        self._total_result[self.C_POS_RECALL] = pos_recall_macro
        self._total_result[self.C_NEG_RECALL] = neg_recall_macro

    def iter_document_results(self):
        return iter(self.__doc_results.items())
