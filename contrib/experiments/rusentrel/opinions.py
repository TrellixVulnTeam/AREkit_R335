import collections
import logging
from os.path import exists

from arekit.common.evaluation.utils import OpinionCollectionsToCompareUtils
from arekit.common.experiment.data.base import DataIO
from arekit.common.experiment.data_type import DataType
from arekit.common.experiment.formats.cv_based.opinions import CVBasedOpinionOperations
from arekit.common.opinions.collection import OpinionCollection
from arekit.contrib.experiments.rusentrel.labels_formatter import RuSentRelNeutralLabelsFormatter
from arekit.contrib.networks.core.io_utils import NetworkIOUtils
from arekit.contrib.source.rusentrel.io_utils import RuSentRelVersions
from arekit.contrib.source.rusentrel.labels_fmt import RuSentRelLabelsFormatter
from arekit.contrib.source.rusentrel.opinions.collection import RuSentRelOpinionCollection


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RuSentrelOpinionOperations(CVBasedOpinionOperations):

    def __init__(self, data_io, experiment_io, version, rusentrel_news_ids):
        assert(isinstance(data_io, DataIO))
        assert(isinstance(version, RuSentRelVersions))
        assert(isinstance(rusentrel_news_ids, set))

        super(RuSentrelOpinionOperations, self).__init__()

        self.__news_ids = rusentrel_news_ids
        self.__eval_on_rusentrel_docs_key = True

        self.__experiment_io = experiment_io
        self.__synonyms = data_io.SynonymsCollection
        self.__opinion_formatter = data_io.OpinionFormatter
        self.__result_labels_fmt = RuSentRelLabelsFormatter()
        self.__neutral_labels_fmt = RuSentRelNeutralLabelsFormatter()
        self.__version = version

    # region property

    @property
    def NewsIDs(self):
        return self.__news_ids

    # endregion

    # region CVBasedOperations

    def get_doc_ids_set_to_neutrally_annotate(self):
        # Note:
        # We provide neutral annotation for every
        # document of RuSentRelCollection.
        return self.__news_ids

    def get_doc_ids_set_to_compare(self):
        return self.__news_ids

    def read_etalon_opinion_collection(self, doc_id):
        assert(isinstance(doc_id, int))
        return RuSentRelOpinionCollection.load_collection(doc_id=doc_id,
                                                          synonyms=self.__synonyms,
                                                          version=self.__version)

    def create_opinion_collection(self, opinions=None):
        assert(isinstance(opinions, list) or opinions is None)

        if self.__synonyms is None:
            raise NotImplementedError("Synonyms collection was not provided!")

        return OpinionCollection.init_as_custom(opinions=[] if opinions is None else opinions,
                                                synonyms=self.__synonyms)

    def iter_opinion_collections_to_compare(self, data_type, doc_ids, epoch_index):
        """
        Note: Assumes that all the results already converted into document-level opinions.
        """
        assert(isinstance(data_type, DataType))
        assert(isinstance(doc_ids, collections.Iterable))
        assert(isinstance(epoch_index, int))

        opinions_cmp_iter = OpinionCollectionsToCompareUtils.iter_comparable_collections(
            doc_ids=filter(lambda doc_id: doc_id in self.get_doc_ids_set_to_compare(), doc_ids),
            read_etalon_collection_func=lambda doc_id: self.read_etalon_opinion_collection(doc_id=doc_id),
            read_result_collection_func=lambda doc_id: self.__load_result(data_type=data_type,
                                                                          doc_id=doc_id,
                                                                          epoch_index=epoch_index))

        for opinions_cmp in opinions_cmp_iter:
            yield opinions_cmp

    def try_read_neutral_opinion_collection(self, doc_id, data_type):
        return self.__try_load_neutral(doc_id=doc_id,
                                       data_type=data_type)

    # endregion

    # region private provider methods

    def __try_load_neutral(self, doc_id, data_type):

        filepath = self.__experiment_io.create_neutral_opinion_collection_filepath(
            experiment=None,
            doc_id=doc_id,
            data_type=data_type)

        if not exists(filepath):
            return None

        return self.__load(filepath=filepath,
                           labels_fmt=self.__neutral_labels_fmt)

    def __load_result(self, data_type, doc_id, epoch_index):
        """ Since evaluation supported only for neural networks,
            we need to gaurantee the presence of a function that returns filepath
            by using isisntance command.
        """
        assert(isinstance(self.__experiment_io, NetworkIOUtils))

        filepath = self.__experiment_io.create_result_opinion_collection_filepath(
            experiment=None,
            data_type=data_type,
            doc_id=doc_id,
            epoch_index=epoch_index)

        return self.__load(filepath=filepath,
                           labels_fmt=self.__result_labels_fmt)

    def __load(self, filepath, labels_fmt):
        return self.__opinion_formatter.load_from_file(filepath=filepath,
                                                       labels_formatter=labels_fmt)

    # endregion