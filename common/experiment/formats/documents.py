from arekit.processing.text.parser import TextParser


class DocumentOperations(object):
    """
    Provides operations with documents
    """

    def iter_supported_data_types(self):
        """ Iterates through data_types, supported in a related experiment
            Note:
            In CV-split algorithm, the first part corresponds to a LARGE split,
            Jand second to small; therefore, the correct sequence is as follows:
            DataType.Train, DataType.Test.
        """
        raise NotImplementedError()

    def read_news(self, doc_id):
        raise NotImplementedError()

    def create_parse_options(self):
        raise NotImplementedError()

    def iter_news_indices(self, data_type):
        """ Provides a news indeces, related to a particular `data_type`
        """
        raise NotImplementedError()

    def iter_parsed_news(self, doc_inds):
        for doc_id in doc_inds:
            yield self.__parse_news(doc_id=doc_id)

    def __parse_news(self, doc_id):
        news = self.read_news(doc_id=doc_id)
        return TextParser.parse_news(news=news,
                                     parse_options=self.create_parse_options())
