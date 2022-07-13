import logging
from os.path import join, exists

from arekit.common.data.input.writers.tsv import TsvWriter
from arekit.common.data.row_ids.multiple import MultipleIDProvider
from arekit.common.data.storages.base import BaseRowsStorage
from arekit.common.data.views.opinions import BaseOpinionStorageView
from arekit.common.data.views.samples import BaseSampleStorageView
from arekit.common.experiment.api.io_utils import BaseIOUtils
from arekit.common.experiment.data_type import DataType
from arekit.contrib.utils.model_io.utils import join_dir_with_subfolder_name, filename_template

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DefaultBertIOUtils(BaseIOUtils):
    """ This is a default file-based Input-output utils,
        which describes file-paths towards the resources, required
        for BERT-related data preparation.
    """

    def _get_experiment_sources_dir(self):
        """ Provides directory for samples.
        """
        raise NotImplementedError()

    def _create_opinion_collection_provider(self):
        pass

    def _create_opinion_collection_writer(self):
        pass

    def create_docs_stat_target(self):
        return join(self.__get_target_dir(), "docs_stat.txt")

    def try_prepare(self):
        model_dir = self.__get_target_dir()
        if not exists(model_dir):
            logger.info("Model dir does not exist. Skipping")
            return False

        exp_dir = join_dir_with_subfolder_name(
            subfolder_name=self.__get_experiment_folder_name(),
            dir=self._get_experiment_sources_dir())

        if not exists(exp_dir):
            logger.info("Experiment dir: {}".format(exp_dir))
            logger.info("Experiment dir does not exist. Skipping")
            return False

        return

    # region experiment dir related

    def __get_target_dir(self):
        """ Provides a main directory for input

            NOTE:
            We consider to save serialized results into model dir,
            rather than experiment dir in a base implementation,
            as model affects on text_b, entities representation, etc.
        """
        default_dir = join_dir_with_subfolder_name(
            subfolder_name=self.__get_experiment_folder_name(),
            dir=self._get_experiment_sources_dir())

        return join(default_dir, self._exp_ctx.ModelIO.get_model_name())

    def __get_experiment_folder_name(self):
        return "{name}_{scale}l".format(name=self._exp_ctx.Name,
                                        scale=str(self._exp_ctx.LabelsCount))

    # endregion

    # region public methods

    def create_samples_view(self, data_type, data_folding):
        return BaseSampleStorageView(
            storage=BaseRowsStorage.from_tsv(filepath=self.__get_input_sample_filepath(
                data_type=data_type, data_folding=data_folding)),
            row_ids_provider=MultipleIDProvider())

    def create_opinions_view(self, data_type, data_folding):
        storage = BaseRowsStorage.from_tsv(
            filepath=self.__get_input_opinions_filepath(data_type, data_folding=data_folding),
            compression='infer')

        return BaseOpinionStorageView(storage=storage)

    def create_opinions_writer_target(self, data_type, data_folding):
        return self.__get_input_opinions_filepath(data_type, data_folding=data_folding)

    def create_samples_writer_target(self, data_type, data_folding):
        return self.__get_input_sample_filepath(data_type, data_folding=data_folding)

    def create_samples_writer(self):
        return TsvWriter(write_header=True)

    def create_opinions_writer(self):
        return TsvWriter(write_header=False)

    # endregion

    # region private methods (filepaths)

    def __get_input_opinions_filepath(self, data_type, data_folding):
        template = filename_template(data_type=data_type, data_folding=data_folding)
        return self.__get_filepath(out_dir=self.__get_target_dir(), template=template, prefix="opinion")

    def __get_input_sample_filepath(self, data_type, data_folding):
        template = filename_template(data_type=data_type, data_folding=data_folding)
        return self.__get_filepath(out_dir=self.__get_target_dir(), template=template, prefix="sample")

    @staticmethod
    def __get_filepath(out_dir, template, prefix):
        assert(isinstance(template, str))
        assert(isinstance(prefix, str))
        return join(out_dir, DefaultBertIOUtils.__generate_tsv_archive_filename(template=template, prefix=prefix))

    @staticmethod
    def __generate_tsv_archive_filename(template, prefix):
        return "{prefix}-{template}.tsv.gz".format(prefix=prefix, template=template)

    def __get_annotator_dir(self):
        return join_dir_with_subfolder_name(dir=self.__get_target_dir(),
                                            subfolder_name=self.__get_annotator_name())

    def __get_annotator_name(self):
        """ We use custom implementation as it allows to
            be independent of NeutralAnnotator instance.
        """
        return "annot_{labels_count}l".format(labels_count=self._exp_ctx.LabelsCount)

    # endregion

    # region protected methods

    def _create_annotated_collection_target(self, doc_id, data_type, check_existence):
        assert(isinstance(doc_id, int))
        assert(isinstance(data_type, DataType))
        assert(isinstance(check_existence, bool))

        annot_dir = self.__get_annotator_dir()

        if annot_dir is None:
            raise NotImplementedError("Neutral root was not provided!")

        # TODO. This should not depends on the neut.
        filename = "art{doc_id}.neut.{d_type}.txt".format(doc_id=doc_id,
                                                          d_type=data_type.name)

        target = join(annot_dir, filename)

        if check_existence and not exists(target):
            return None

        return target

    # endregion
