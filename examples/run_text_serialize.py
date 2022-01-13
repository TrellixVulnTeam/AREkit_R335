import argparse
from collections import OrderedDict

from arekit.common.data.input.providers.label.multiple import MultipleLabelProvider
from arekit.common.experiment.annot.algo.pair_based import PairBasedAnnotationAlgorithm
from arekit.common.experiment.annot.default import DefaultAnnotator
from arekit.common.labels.base import NoLabel
from arekit.common.labels.provider.single_label import PairSingleLabelProvider
from arekit.common.labels.scaler.base import BaseLabelScaler
from arekit.common.labels.str_fmt import StringLabelsFormatter
from arekit.common.news.base import News
from arekit.common.news.entities_grouping import EntitiesGroupingPipelineItem
from arekit.common.news.sentence import BaseNewsSentence
from arekit.common.text.parser import BaseTextParser
from arekit.contrib.experiment_rusentrel.entities.factory import create_entity_formatter
from arekit.contrib.experiment_rusentrel.entities.types import EntityFormatterTypes

from arekit.contrib.experiment_rusentrel.synonyms.provider import RuSentRelSynonymsCollectionProvider
from arekit.contrib.networks.core.input.helper import NetworkInputHelper
from arekit.contrib.source.rusentrel.io_utils import RuSentRelVersions

from arekit.processing.lemmatization.mystem import MystemWrapper
from arekit.processing.pos.mystem_wrap import POSMystemWrapper
from arekit.processing.text.pipeline_frames_lemmatized import LemmasBasedFrameVariantsParser
from arekit.processing.text.pipeline_frames_negation import FrameVariantsSentimentNegation
from arekit.processing.text.pipeline_tokenizer import DefaultTextTokenizer

from examples.input import EXAMPLES
from examples.network.args.common import RusVectoresEmbeddingFilepathArg, TermsPerContextArg, StemmerArg
from examples.network.args.serialize import EntityFormatterTypesArg
from examples.network.common import create_infer_experiment_name_provider,\
    create_and_fill_variant_collection, \
    create_frames_collection
from examples.network.embedding import RusvectoresEmbedding
from examples.network.infer.doc_ops import SingleDocOperations
from examples.network.infer.exp import CustomExperiment
from examples.network.serialization_data import RuSentRelExperimentSerializationData
from examples.network.text_parser.entities import TextEntitiesParser
from examples.network.text_parser.terms import TermsSplitterParser


def run_serializer(sentences_text_list, terms_per_context, embedding_path, entity_fmt_type, stemmer):
    assert(isinstance(sentences_text_list, list))
    assert(isinstance(terms_per_context, int))
    assert(isinstance(embedding_path, str))
    assert(isinstance(entity_fmt_type, EntityFormatterTypes))

    labels_scaler = BaseLabelScaler(uint_dict=OrderedDict([(NoLabel(), 0)]),
                                    int_dict=OrderedDict([(NoLabel(), 0)]))

    label_provider = MultipleLabelProvider(label_scaler=labels_scaler)

    # TODO. split text onto sentences.
    sentences = list(map(lambda text: BaseNewsSentence(text), sentences_text_list))

    annot_algo = PairBasedAnnotationAlgorithm(
        dist_in_terms_bound=None,
        label_provider=PairSingleLabelProvider(label_instance=NoLabel()))

    frames_collection = create_frames_collection()
    frame_variants_collection = create_and_fill_variant_collection(frames_collection)

    # Step 1. Annotate text.
    synonyms = RuSentRelSynonymsCollectionProvider.load_collection(
        stemmer=stemmer,
        version=RuSentRelVersions.V11)

    # Step 2. Parse text.
    news = News(doc_id=0, sentences=sentences)

    text_parser = BaseTextParser(
        pipeline=[
            TermsSplitterParser(),
            TextEntitiesParser(),
            EntitiesGroupingPipelineItem(synonyms.get_synonym_group_index),
            DefaultTextTokenizer(keep_tokens=True),
            LemmasBasedFrameVariantsParser(save_lemmas=False,
                                           stemmer=stemmer,
                                           frame_variants=frame_variants_collection),
            FrameVariantsSentimentNegation()
        ])

    embedding = RusvectoresEmbedding.from_word2vec_format(filepath=embedding_path, binary=True)
    embedding.set_stemmer(stemmer)

    exp_data = RuSentRelExperimentSerializationData(
        labels_scaler=label_provider.LabelScaler,
        stemmer=stemmer,
        embedding=embedding,
        annotator=DefaultAnnotator(annot_algo=annot_algo),
        terms_per_context=terms_per_context,
        str_entity_formatter=create_entity_formatter(entity_fmt_type),
        pos_tagger=POSMystemWrapper(MystemWrapper().MystemInstance))

    labels_fmt = StringLabelsFormatter(stol={"neu": NoLabel})

    # Step 3. Serialize data
    experiment = CustomExperiment(
        exp_data=exp_data,
        doc_ops=SingleDocOperations(news=news, text_parser=text_parser),
        labels_formatter=labels_fmt,
        synonyms=synonyms,
        neutral_labels_fmt=labels_fmt,
        name_provider=create_infer_experiment_name_provider())

    NetworkInputHelper.prepare(experiment=experiment,
                               terms_per_context=terms_per_context,
                               balance=False,
                               value_to_group_id_func=synonyms.get_synonym_group_index)

    return experiment.ExperimentIO


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Serialization script for obtaining sources, "
                                                 "required for inference and training.")

    # Provide arguments.
    RusVectoresEmbeddingFilepathArg.add_argument(parser)
    TermsPerContextArg.add_argument(parser)
    EntityFormatterTypesArg.add_argument(parser)
    StemmerArg.add_argument(parser)

    # Parsing arguments.
    args = parser.parse_args()

    # Reading provided arguments.
    terms_per_context = TermsPerContextArg.read_argument(args)
    embedding_filepath = RusVectoresEmbeddingFilepathArg.read_argument(args)
    entity_fmt = EntityFormatterTypesArg.read_argument(args)
    stemmer = StemmerArg.read_argument(args)

    run_serializer(sentences_text_list=EXAMPLES["simple"],
                   terms_per_context=terms_per_context,
                   embedding_path=embedding_filepath,
                   entity_fmt_type=entity_fmt,
                   stemmer=stemmer)
