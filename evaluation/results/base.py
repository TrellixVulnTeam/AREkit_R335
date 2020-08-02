from core.evaluation.evaluators.cmp_table import DocumentCompareTable


class BaseEvalResult(object):

    def __init__(self):
        self.__documents = {}

    def get_cmp_table(self, doc_id):
        assert(isinstance(doc_id, int))
        return self.__documents[doc_id]

    def calculate(self):
        raise Exception("Not implemented")

    def add_cmp_table(self, doc_id, cmp_table):
        assert(doc_id not in self.__documents)
        assert(isinstance(cmp_table, DocumentCompareTable))
        self.__documents[doc_id] = cmp_table

    def iter_document_cmp_tables(self):
        for doc_id, cmp_table in list(self.__documents.items()):
            yield doc_id, cmp_table

    def iter_document_ids(self):
        for doc_id in list(self.__documents.keys()):
            yield doc_id
