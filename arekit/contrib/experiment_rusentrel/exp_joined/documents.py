from arekit.common.experiment.api.ops_doc import DocumentOperations
from arekit.contrib.experiment_rusentrel.exp_ds.documents import RuAttitudesDocumentOperations
from arekit.contrib.experiment_rusentrel.exp_sl.documents import RuSentrelDocumentOperations


class RuSentrelWithRuAttitudesDocumentOperations(DocumentOperations):

    def __init__(self, rusentrel_doc, get_ruattitudes_doc, text_parser):
        assert(isinstance(rusentrel_doc, RuSentrelDocumentOperations))
        assert(callable(get_ruattitudes_doc))

        # We consider RuSentRel folding algorithm by default.
        # The latter utilized in experiment as `main`, while
        # RuAttitude data-folding considered as `auxiliary`.
        super(RuSentrelWithRuAttitudesDocumentOperations, self).__init__(
            folding=rusentrel_doc.DataFolding,
            text_parser=text_parser)

        self.__rusentrel_doc = rusentrel_doc
        self.__get_ruattitudes_doc = get_ruattitudes_doc

    # region private methods

    def __select_doc_ops(self, doc_id):
        if self.__rusentrel_doc.DataFolding.contains_doc_id(doc_id):
            return self.__rusentrel_doc

        ruattitudes_doc = self.__get_ruattitudes_doc()
        assert(isinstance(ruattitudes_doc, RuAttitudesDocumentOperations))

        if ruattitudes_doc.DataFolding.contains_doc_id(doc_id):
            return ruattitudes_doc

        raise Exception(
            "Doc-id {} has not been found both in RuSentRel and RuAttitudes related doc formatters.".format(doc_id))

    # endregion

    # region DocumentOperations

    def get_doc(self, doc_id):
        target_doc_ops = self.__select_doc_ops(doc_id)
        return target_doc_ops.get_doc(doc_id)

    def iter_doc_ids(self, data_type):
        for doc_id in self.__rusentrel_doc.iter_doc_ids(data_type):
            yield doc_id

        ruattitudes_doc = self.__get_ruattitudes_doc()
        assert(isinstance(ruattitudes_doc, RuAttitudesDocumentOperations))

        for doc_id in ruattitudes_doc.iter_doc_ids(data_type):
            yield doc_id

    def iter_tagget_doc_ids(self, tag):
        return self.__rusentrel_doc.iter_tagget_doc_ids(tag)

    # endregion
