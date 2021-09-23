import collections
import logging

from arekit.common.experiment.data_type import DataType
from arekit.common.experiment.input.readers.base_sample import BaseInputSampleReader
from arekit.common.experiment.labeling import LabeledCollection
from arekit.common.model.labeling.stat import calculate_labels_distribution_stat

from arekit.contrib.networks.core.input.readers.samples_helper import NetworkInputSampleReaderHelper
from arekit.contrib.networks.sample import InputSample

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class HandledData(object):

    def __init__(self, labeled_collections, bags_collection):
        assert(isinstance(labeled_collections, dict))
        assert(isinstance(bags_collection, dict))
        self.__labeled_collections = labeled_collections
        self.__bags_collection = bags_collection
        self.__train_stat_uint_labeled_sample_row_ids = None

    # region Properties

    @property
    def BagsCollections(self):
        return self.__bags_collection

    @property
    def SamplesLabelingCollection(self):
        return self.__labeled_collections

    @property
    def HasNormalizedWeights(self):
        return self.__train_stat_uint_labeled_sample_row_ids is not None

    # endregion

    @classmethod
    def create_empty(cls):
        return cls(labeled_collections={},
                   bags_collection={})

    def initialize(self, dtypes, create_samples_reader_func, has_model_predefined_state,
                   vocab, labels_count, bags_collection_type,
                   # TODO: 199. Remove config.
                   config):
        """
        Perform reading information from the serialized experiment inputs.
        Initializing core configuration.
        """
        assert(isinstance(dtypes, collections.Iterable))
        assert(callable(create_samples_reader_func))
        assert(isinstance(has_model_predefined_state, bool))
        assert(isinstance(labels_count, int) and labels_count > 0)

        # Reading from serialized information
        for data_type in dtypes:

            # Create samples reader.
            samples_reader = create_samples_reader_func(data_type)

            # Extracting such information from serialized files.
            bags_collection, uint_labeled_sample_row_ids = self.__read_for_data_type(
                samples_reader=samples_reader,
                is_external_vocab=has_model_predefined_state,
                bags_collection_type=bags_collection_type,
                vocab=vocab,
                # TODO: 199. Remove config.
                config=config,
                desc="Filling bags collection [{}]".format(data_type))

            # Saving into dictionaries.
            self.__bags_collection[data_type] = bags_collection
            self.__labeled_collections[data_type] = LabeledCollection(
                uint_labeled_sample_row_ids=uint_labeled_sample_row_ids)

            if data_type == DataType.Train:
                self.__train_stat_uint_labeled_sample_row_ids = uint_labeled_sample_row_ids

    def calc_normalized_weigts(self, labels_count):
        assert(isinstance(labels_count, int) and labels_count > 0)

        if self.__train_stat_uint_labeled_sample_row_ids is None:
            return

        normalized_label_stat, _ = calculate_labels_distribution_stat(
            uint_labeled_sample_row_ids=self.__train_stat_uint_labeled_sample_row_ids,
            classes_count=labels_count)

        return normalized_label_stat

    # region private methods

    @staticmethod
    def __read_for_data_type(samples_reader, is_external_vocab,
                             bags_collection_type, vocab,
                             # TODO: 199. Remove config.
                             config, desc=""):
        assert(isinstance(samples_reader, BaseInputSampleReader))

        # TODO: 199. Use shapes.
        terms_per_context = config.TermsPerContext
        frames_per_context = config.FramesPerContext
        synonyms_per_context = config.SynonymsPerContext

        bags_collection = bags_collection_type.from_formatted_samples(
            formatted_samples_iter=samples_reader.iter_rows_linked_by_text_opinions(),
            desc=desc,
            bag_size=config.BagSize,
            shuffle=True,
            create_empty_sample_func=lambda: InputSample.create_empty(
                # TODO: 199. Use shapes.
                terms_per_context=terms_per_context,
                frames_per_context=frames_per_context,
                synonyms_per_context=synonyms_per_context),
            create_sample_func=lambda row: InputSample.create_from_parameters(
                input_sample_id=row.SampleID,
                terms=row.Terms,
                entity_inds=row.EntityInds,
                is_external_vocab=is_external_vocab,
                subj_ind=row.SubjectIndex,
                obj_ind=row.ObjectIndex,
                words_vocab=vocab,
                frame_inds=row.TextFrameVariantIndices,
                frame_sent_roles=row.TextFrameVariantRoles,
                syn_obj_inds=row.SynonymObjectInds,
                syn_subj_inds=row.SynonymSubjectInds,
                # TODO: 199. Use shapes.
                terms_per_context=terms_per_context,
                frames_per_context=frames_per_context,
                synonyms_per_context=synonyms_per_context,
                pos_tags=row.PartOfSpeechTags))

        rows_it = NetworkInputSampleReaderHelper.iter_uint_labeled_sample_rows(samples_reader)

        labeled_sample_row_ids = list(rows_it)

        return bags_collection, labeled_sample_row_ids

    # endregion
