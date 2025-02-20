class BaseOpinionAnnotator(object):
    """
    Performs annotation for a particular data_type
    using OpinOps and DocOps API.
    """

    def _annot_collection_core(self, parsed_news):
        raise NotImplementedError

    # region public methods

    def annotate_collection(self, parsed_news):
        return self._annot_collection_core(parsed_news=parsed_news)

    # endregion
