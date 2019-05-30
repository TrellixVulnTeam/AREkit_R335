#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import OrderedDict

import pandas as pd

from core.evaluation.labels import PositiveLabel, NegativeLabel, NeutralLabel, Label
from core.evaluation.statistic import FilesToCompare
from core.source.opinion import OpinionCollection
from core.source.synonyms import SynonymsCollection


# TODO: PNEvalResult
# TODO: TO separated file (result.py)
class EvalResult:

    C_POS_PREC = u'pos_prec'
    C_NEG_PREC = u'neg_prec'
    C_POS_RECALL = u'pos_recall'
    C_NEG_RECALL = u'neg_recall'
    C_F1_POS = u'f1_pos'
    C_F1_NEG = u'f1_neg'
    C_F1 = u'f1'

    def __init__(self):
        self.__documents = OrderedDict()
        self.__cmp_results = OrderedDict()
        self.__result = None

    @property
    def Result(self):
        return self.__result

    def add_document_results(self, doc_id, pos_prec, neg_prec, pos_recall, neg_recall):
        assert(doc_id not in self.__documents)

        f1 = self.__calc_f1(pos_prec=pos_prec,
                            neg_prec=neg_prec,
                            pos_recall=pos_recall,
                            neg_recall=neg_recall)

        self.__documents[doc_id] = OrderedDict()
        self.__documents[doc_id][self.C_F1] = round(f1, 2)
        self.__documents[doc_id][self.C_POS_PREC] = round(pos_prec, 4)
        self.__documents[doc_id][self.C_NEG_PREC] = round(neg_prec, 5)
        self.__documents[doc_id][self.C_POS_RECALL] = round(pos_recall, 5)
        self.__documents[doc_id][self.C_NEG_RECALL] = round(neg_recall, 5)

    def add_cmp_results(self, doc_id, cmp_results):
        assert(doc_id not in self.__cmp_results)
        self.__cmp_results[doc_id] = cmp_results

    def calculate(self):
        pos_prec, neg_prec, pos_recall, neg_recall = (0.0, 0.0, 0.0, 0.0)

        for info in self.__documents.itervalues():
            pos_prec += info[self.C_POS_PREC]
            neg_prec += info[self.C_NEG_PREC]
            pos_recall += info[self.C_POS_RECALL]
            neg_recall += info[self.C_NEG_RECALL]

        pos_prec /= len(self.__documents)
        neg_prec /= len(self.__documents)
        pos_recall /= len(self.__documents)
        neg_recall /= len(self.__documents)

        f1 = self.__calc_f1(pos_prec=pos_prec,
                            neg_prec=neg_prec,
                            pos_recall=pos_recall,
                            neg_recall=neg_recall)

        self.__result = OrderedDict()
        self.__result[self.C_F1] = f1
        self.__result[self.C_F1_POS] = self.__calc_f1_single_class(prec=pos_prec, recall=pos_recall)
        self.__result[self.C_F1_NEG] = self.__calc_f1_single_class(prec=neg_prec, recall=neg_recall)
        self.__result[self.C_POS_PREC] = pos_prec
        self.__result[self.C_NEG_PREC] = neg_prec
        self.__result[self.C_POS_RECALL] = pos_recall
        self.__result[self.C_NEG_RECALL] = neg_recall

    @staticmethod
    def __calc_f1_single_class(prec, recall):
        if prec * recall != 0:
            return 2 * prec * recall / (prec + recall)
        else:
            return 0

    @staticmethod
    def __calc_f1(pos_prec, neg_prec, pos_recall, neg_recall):
        f1_pos = EvalResult.__calc_f1_single_class(prec=pos_prec, recall=pos_recall)
        f1_neg = EvalResult.__calc_f1_single_class(prec=neg_prec, recall=neg_recall)
        return (f1_pos + f1_neg) * 1.0 / 2

    def iter_document_results(self):
        for doc_id, info in self.__documents.iteritems():
            yield doc_id, info

    def iter_document_cmp(self):
        for doc_id, cmp_result in self.__cmp_results.iteritems():
            yield doc_id, cmp_result


# TODO: New evaluator that is irrespective of the label
class Evaluator:

    # Columns for differences
    C_WHO = 'who'
    C_TO = 'to'
    C_ORIG = 'how_orig'
    C_RES = 'how_results'
    C_CMP = 'comparison'

    def __init__(self, synonyms):
        assert(isinstance(synonyms, SynonymsCollection) and synonyms.IsReadOnly)
        self.__synonyms = synonyms
        self.__pos_label = PositiveLabel()
        self.__neg_label = NegativeLabel()
        # TODO: This is useless variable.
        self.__neutral_label = NeutralLabel()

    @staticmethod
    def __calc_recall(results, answers, label, answer_exist):
        # TODO: Add type checking for results.
        assert(isinstance(label, PositiveLabel) or isinstance(label, NegativeLabel))
        assert(isinstance(answer_exist, bool))
        # TODO: same operation, len(...) refactor.
        if len(results[results[Evaluator.C_ORIG] == label.to_str()]) != 0:
            return 1.0 * len(answers[(answers[Evaluator.C_CMP] == True)]) / len(results[results[Evaluator.C_ORIG] == label.to_str()])
        else:
            return 0.0 if answer_exist else 1.0

    @staticmethod
    def __calc_precision(answers, answer_exist):
        assert(isinstance(answer_exist, bool))
        # TODO: same operation len(...), refactor.
        if len(answers) != 0:
            return 1.0 * len(answers[(answers[Evaluator.C_CMP] == True)]) / len(answers)
        else:
            return 0.0 if answer_exist else 1.0

    # TODO: refactor for single parameter (pos/neg).
    def __calc_prec_and_recall(self, results, pos_opinions_exist, neg_opinions_exist):
        assert(isinstance(pos_opinions_exist, bool))
        assert(isinstance(neg_opinions_exist, bool))

        pos_answers = results[(results[Evaluator.C_RES] == self.__pos_label.to_str())]
        neg_answers = results[(results[Evaluator.C_RES] == self.__neg_label.to_str())]

        pos_prec = self.__calc_precision(pos_answers, answer_exist=pos_opinions_exist)
        neg_prec = self.__calc_precision(neg_answers, answer_exist=neg_opinions_exist)

        # TODO: write parameters.
        pos_recall = self.__calc_recall(results, pos_answers, self.__pos_label, answer_exist=pos_opinions_exist)
        neg_recall = self.__calc_recall(results, neg_answers, self.__neg_label, answer_exist=neg_opinions_exist)

        assert(isinstance(pos_prec, float))
        assert(isinstance(neg_prec, float))
        assert(isinstance(pos_recall, float))
        assert(isinstance(neg_recall, float))

        return pos_prec, neg_prec, pos_recall, neg_recall

    # TODO: Rename, as it generates the differences.
    def __check(self, etalon_opins, test_opins):
        assert(isinstance(etalon_opins, OpinionCollection))
        assert(isinstance(test_opins, OpinionCollection))

        df = pd.DataFrame(
                columns=[self.C_WHO, self.C_TO, self.C_ORIG, self.C_RES, self.C_CMP])

        r_ind = 0
        for o_etalon in etalon_opins:
            comparison = False
            has_opinion = test_opins.has_synonymous_opinion(o_etalon)

            # TODO: Disable this check in case of non label evaluation method.

            if has_opinion:
                o_test = test_opins.get_synonymous_opinion(o_etalon)
                comparison = o_test.sentiment == o_etalon.sentiment

            df.loc[r_ind] = [o_etalon.value_left.encode('utf-8'),
                             o_etalon.value_right.encode('utf-8'),
                             o_etalon.sentiment.to_str(),
                             None if not has_opinion else o_test.sentiment.to_str(),
                             comparison]
            r_ind += 1

        for o_test in test_opins:
            has_opinion = etalon_opins.has_synonymous_opinion(o_test)
            if has_opinion:
                continue
            df.loc[r_ind] = [o_test.value_left.encode('utf-8'),
                             o_test.value_right.encode('utf-8'),
                             None, o_test.sentiment.to_str(), False]
            r_ind += 1

        return df

    def __calc_a_file(self, files_to_compare, debug):
        assert(isinstance(files_to_compare, FilesToCompare))

        # Reading test answers.
        test_opins = OpinionCollection.from_file(
            filepath=files_to_compare.TestFilepath,
            synonyms=self.__synonyms)

        # Reading etalon answers.
        etalon_opins = OpinionCollection.from_file(
            filepath=files_to_compare.EtalonFilepath,
            synonyms=self.__synonyms)

        if debug:
            print "{} <-> {}, {}".format(
                    files_to_compare.TestFilepath,
                    files_to_compare.EtalonFilepath,
                    files_to_compare.index)

        results = self.__check(etalon_opins, test_opins)

        return results, \
               self.__has_opinions_with_label(etalon_opins, PositiveLabel()),\
               self.__has_opinions_with_label(etalon_opins, NegativeLabel())

    def __has_opinions_with_label(self, opinions, label):
        assert(isinstance(label, Label))
        assert(isinstance(opinions, OpinionCollection))
        for opinion in opinions:
            if opinion.sentiment.to_int() == label.to_int():
                return True
        return False

    def evaluate(self, files_to_compare_list, debug=False):
        assert(isinstance(files_to_compare_list, list))

        result = EvalResult()
        for files_to_compare in files_to_compare_list:
            cmp_results, has_pos, has_neg = self.__calc_a_file(files_to_compare, debug=debug)
            # TODO: Two separated calls for pos/neg labels
            pos_prec, neg_prec, pos_recall, neg_recall = self.__calc_prec_and_recall(results=cmp_results,
                                                                                     pos_opinions_exist=has_pos,
                                                                                     neg_opinions_exist=has_neg)
            result.add_document_results(doc_id=files_to_compare.index,
                                        pos_recall=pos_recall,
                                        neg_recall=neg_recall,
                                        pos_prec=pos_prec,
                                        neg_prec=neg_prec)

        result.calculate()
        return result
