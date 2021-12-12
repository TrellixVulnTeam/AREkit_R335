import os

from arekit.common.entities.base import Entity
from arekit.common.experiment.api.base import BaseExperiment
from arekit.common.experiment.api.enums import BaseDocumentTag
from arekit.common.experiment.api.io_utils import BaseIOUtils
from arekit.common.experiment.api.ops_doc import DocumentOperations
from arekit.common.experiment.api.ops_opin import OpinionOperations
from arekit.common.experiment.data_type import DataType
from arekit.common.folding.nofold import NoFolding
from arekit.common.frames.variants.collection import FrameVariantsCollection
from arekit.common.opinions.collection import OpinionCollection
from arekit.contrib.experiment_rusentrel.common import entity_to_group_func
from arekit.contrib.experiment_rusentrel.connotations.provider import RuSentiFramesConnotationProvider
from arekit.contrib.experiment_rusentrel.entities.str_simple_fmt import StringEntitiesSimpleFormatter
from arekit.contrib.experiment_rusentrel.labels.scalers.three import ThreeLabelScaler
from arekit.contrib.networks.core.input.data_serialization import NetworkSerializationData
from arekit.contrib.networks.core.io_utils import NetworkIOUtils
from arekit.contrib.source import utils
from arekit.contrib.source.rusentiframes.collection import RuSentiFramesCollection
from arekit.contrib.source.rusentiframes.types import RuSentiFramesVersions
from arekit.processing.lemmatization.mystem import MystemWrapper
from arekit.processing.pos.mystem_wrap import POSMystemWrapper
from arekit.processing.text.parser import DefaultTextParser
from examples.download import EMBEDDING_FILENAME
from examples.network.embedding import RusvectoresEmbedding


class SingleDocOperations(DocumentOperations):
    """ Operations over a single document for inference.
    """

    def iter_tagget_doc_ids(self, tag):
        assert(isinstance(tag, BaseDocumentTag))
        assert(tag == BaseDocumentTag.Annotate)
        return [0]

    def __init__(self, news, text_parser):
        folding = NoFolding(doc_ids_to_fold=[0], supported_data_types=[DataType.Test])
        super(SingleDocOperations, self).__init__(folding, text_parser)
        self.__doc = news

    def get_doc(self, doc_id):
        return self.__doc


class CustomOpinionOperations(OpinionOperations):

    def __init__(self, labels_formatter, iter_opins, synonyms):
        super(CustomOpinionOperations, self).__init__()
        self.__labels_formatter = labels_formatter
        self.__iter_opins = iter_opins
        self.__synonyms = synonyms

    @property
    def LabelsFormatter(self):
        return self.__labels_formatter

    def iter_opinions_for_extraction(self, doc_id, data_type):
        return self.__iter_opins

    def get_etalon_opinion_collection(self, doc_id):
        return self.create_opinion_collection()

    def get_result_opinion_collection(self, doc_id, data_type, epoch_index):
        raise Exception("Not Supported")

    def create_opinion_collection(self):
        return OpinionCollection(opinions=None,
                                 synonyms=self.__synonyms,
                                 error_on_duplicates=True,
                                 error_on_synonym_end_missed=True)


class CustomExperiment(BaseExperiment):

    def __init__(self, synonyms, exp_data, exp_io_type, opin_ops, doc_ops):
        assert(issubclass(exp_io_type, BaseIOUtils))
        super(CustomExperiment, self).__init__(exp_data=exp_data,
                                               experiment_io=exp_io_type(self),
                                               opin_ops=opin_ops,
                                               doc_ops=doc_ops,
                                               name="test",
                                               extra_name_suffix="test")

        self.__synonyms = synonyms

    def entity_to_group(self, entity):
        return entity_to_group_func(entity, synonyms=self.__synonyms)


class CustomSerializationData(NetworkSerializationData):

    def __init__(self, label_scaler, annot, stemmer, frame_variants_collection):
        assert(isinstance(stemmer, MystemWrapper))
        assert(isinstance(frame_variants_collection, FrameVariantsCollection))

        super(CustomSerializationData, self).__init__(labels_scaler=label_scaler, annot=annot, stemmer=stemmer)

        frames_collection = RuSentiFramesCollection.read_collection(version=RuSentiFramesVersions.V20)
        self.__frame_roles_label_scaler = ThreeLabelScaler()
        self.__frames_connotation_provider = RuSentiFramesConnotationProvider(collection=frames_collection)
        self.__frame_variants_collection = frame_variants_collection
        self.__entities_formatter = StringEntitiesSimpleFormatter()
        self.__embedding = RusvectoresEmbedding.from_word2vec_format(
            filepath=os.path.join(utils.get_default_download_dir(), EMBEDDING_FILENAME),
            binary=True)
        self.__pos_tagger = POSMystemWrapper(stemmer.MystemInstance)

    @property
    def FrameRolesLabelScaler(self):
        return None

    @property
    def WordEmbedding(self):
        return self.__embedding

    @property
    def PosTagger(self):
        return self.__pos_tagger

    @property
    def StringEntityEmbeddingFormatter(self):
        return self.__entities_formatter

    @property
    def StringEntityFormatter(self):
        return self.__entities_formatter

    @property
    def FramesConnotationProvider(self):
        return self.__frames_connotation_provider

    @property
    def FrameVariantCollection(self):
        return self.__frame_variants_collection

    @property
    def TermsPerContext(self):
        return 50


class CustomTextParser(DefaultTextParser):

    def __init__(self, parse_options):
        super(CustomTextParser, self).__init__(parse_options)
        
        self.__id_in_doc = 0

    def _process_words_to_terms_list(self, word, keep_tokens):
        assert(isinstance(word, str))

        # If this is a special word which is related to the [entity] mention.
        if word[0] == "[" and word[-1] == "]":
            entity = Entity(value=word[1:-1], e_type=None, id_in_doc=self.__id_in_doc)
            self.__id_in_doc += 1
            return [entity]

        return super(CustomTextParser, self)._process_words_to_terms_list(word=word, keep_tokens=keep_tokens)


class CustomNetworkIOUtils(NetworkIOUtils):

    def get_experiment_sources_dir(self):
        return "."