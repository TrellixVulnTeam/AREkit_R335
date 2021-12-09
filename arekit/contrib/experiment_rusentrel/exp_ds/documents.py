from arekit.common.experiment.api.enums import BaseDocumentTag
from arekit.common.experiment.api.ops_doc import DocumentOperations


class RuAttitudesDocumentOperations(DocumentOperations):

    def __init__(self, text_parser, folding, ru_attitudes):
        assert(isinstance(ru_attitudes, dict))
        super(RuAttitudesDocumentOperations, self).__init__(folding=folding, text_parser=text_parser)
        self.__ru_attitudes = ru_attitudes

    # region DocumentOperations

    def get_doc(self, doc_id):
        return self.__ru_attitudes[doc_id]

    def iter_tagget_doc_ids(self, tag):
        assert(isinstance(tag, BaseDocumentTag))
        assert(tag == BaseDocumentTag.Annotate or tag == BaseDocumentTag.Compare)
        return
        yield

    # endregion