from arekit.common.data.input.providers.label.base import LabelProvider
from arekit.common.data.input.providers.label.multiple import MultipleLabelProvider
from arekit.common.entities.base import Entity
from arekit.common.entities.collection import EntityCollection
from arekit.common.experiment.annot.single_label import DefaultSingleLabelAnnotationAlgorithm
from arekit.common.frames.variants.collection import FrameVariantsCollection
from arekit.common.labels.base import NoLabel
from arekit.common.news.base import News
from arekit.common.news.sentence import BaseNewsSentence
from arekit.common.text.options import TextParseOptions
from arekit.contrib.experiment_rusentrel.annot.three_scale import ThreeScaleTaskAnnotator
from arekit.contrib.experiment_rusentrel.labels.scalers.three import ThreeLabelScaler
from arekit.contrib.experiment_rusentrel.synonyms.provider import RuSentRelSynonymsCollectionProvider
from arekit.contrib.networks.core.input.helper import NetworkInputHelper
from arekit.contrib.networks.core.io_utils import NetworkIOUtils
from arekit.contrib.source.rusentiframes.collection import RuSentiFramesCollection
from arekit.contrib.source.rusentiframes.types import RuSentiFramesVersions
from arekit.contrib.source.rusentrel.io_utils import RuSentRelVersions
from arekit.processing.lemmatization.mystem import MystemWrapper
from examples.input import EXAMPLES
from examples.network.utils import SingleDocOperations, CustomOpinionOperations, CustomSerializationData, \
    CustomExperiment, CustomTextParser


def create_frame_variants_collection():

    frames = RuSentiFramesCollection.read_collection(RuSentiFramesVersions.V20)
    frame_variant_collection = FrameVariantsCollection()
    frame_variant_collection.fill_from_iterable(
        variants_with_id=frames.iter_frame_id_and_variants(),
        overwrite_existed_variant=True,
        raise_error_on_existed_variant=False)

    return frame_variant_collection


def extract_entities_from_news(news):
    entities = []
    for sentence in news.iter_sentences():
        for term in sentence.Text:
            if (isinstance(term, Entity)):
                entities.append(term)

    return entities


def pipeline_serialize(sentences_text_list, label_provider):
    assert(isinstance(sentences_text_list, list))
    assert(isinstance(label_provider, LabelProvider))

    # TODO. split text onto sentences.
    sentences = list(map(lambda text: BaseNewsSentence(text), sentences_text_list))

    stemmer = MystemWrapper()

    annot_algo = DefaultSingleLabelAnnotationAlgorithm(
        dist_in_terms_bound=None,
        label_instance=NoLabel())

    frame_variants_collection = create_frame_variants_collection()

    # Step 1. Parse text.

    news = News(doc_id=0, sentences=sentences)

    parse_options = TextParseOptions(
        parse_entities=False,
        frame_variants_collection=frame_variants_collection,
        stemmer=stemmer)

    text_parser = CustomTextParser(parse_options)

    parsed_news = text_parser.parse_news(news=news)

    # Step 2. Annotate text.
    synonyms = RuSentRelSynonymsCollectionProvider.load_collection(
        stemmer=stemmer,
        version=RuSentRelVersions.V11)

    entities_collection = EntityCollection(
        entities=extract_entities_from_news(news),
        synonyms=synonyms)

    opins_for_extraction = annot_algo.iter_opinions(
        parsed_news=parsed_news,
        entities_collection=entities_collection)   # TODO. Create custom entity collections.

    doc_ops = SingleDocOperations(news=news, text_parser=text_parser)

    opin_ops = CustomOpinionOperations(labels_formatter=None,
                                       iter_opins=opins_for_extraction,
                                       synonyms=synonyms)

    exp_data = CustomSerializationData(label_scaler=label_provider.LabelScaler,
                                       stemmer=stemmer,
                                       annot=ThreeScaleTaskAnnotator(annot_algo=annot_algo),
                                       frame_variants_collection=frame_variants_collection)

    # Step 3. Serialize data
    experiment = CustomExperiment(synonyms=synonyms,
                                  exp_data=exp_data,
                                  exp_io_type=NetworkIOUtils,
                                  doc_ops=doc_ops,
                                  opin_ops=opin_ops)

    NetworkInputHelper.prepare(experiment=experiment,
                               terms_per_context=50,
                               balance=False)


if __name__ == '__main__':

    text = EXAMPLES["simple"]

    labels_scaler = ThreeLabelScaler()
    label_provider = MultipleLabelProvider(label_scaler=labels_scaler)

    pipeline_serialize(sentences_text_list=text, label_provider=label_provider)
