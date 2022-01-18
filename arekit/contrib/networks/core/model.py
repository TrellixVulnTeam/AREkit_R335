import collections
import logging

from arekit.common.model.base import BaseModel
from arekit.common.experiment.data_type import DataType
from arekit.common.pipeline.context import PipelineContext

from arekit.contrib.networks.core.cancellation import OperationCancellation
from arekit.contrib.networks.core.feeding.bags.collection.factory import create_batch_by_bags_group
from arekit.contrib.networks.core.model_ctx import TensorflowModelContext
from arekit.contrib.networks.core.network_callback import NetworkCallback
from arekit.contrib.networks.core.params import NeuralNetworkModelParams
from arekit.contrib.networks.core.pipeline_epoch import EpochHandlingPipelineItem
from arekit.contrib.networks.tf_helpers.nn_states import TensorflowNetworkStatesProvider

logger = logging.getLogger(__name__)


class BaseTensorflowModel(BaseModel):

    SaveTensorflowModelStateOnFit = True

    def __init__(self, context, callback,
                 predict_pipeline=None,
                 fit_pipeline=None):
        assert(isinstance(context, TensorflowModelContext))
        assert(isinstance(callback, NetworkCallback))
        assert(isinstance(predict_pipeline, list))
        assert(isinstance(fit_pipeline, list))
        super(BaseTensorflowModel, self).__init__()

        self.__context = context
        self.__callback = callback
        self.__predict_pipeline = predict_pipeline
        self.__fit_pipeline = fit_pipeline
        self.__states_provider = TensorflowNetworkStatesProvider()

    @property
    def Context(self):
        return self.__context

    # region private methods

    def __run_epoch_pipeline(self, data_type, pipeline, prefix):
        assert(isinstance(pipeline, list))
        assert(isinstance(prefix, str))

        bags_per_group = self.__context.Config.BagsPerMinibatch
        bags_collection = self.__context.get_bags_collection(data_type)
        minibatches_count = bags_collection.get_groups_count(bags_per_group)

        logger.info("Minibatches passing per epoch count: ~{} "
                    "(Might be greater or equal, as the last "
                    "bag is expanded)".format(minibatches_count))

        groups_it = self.__callback.handle_batches_iter(
            batches_iter=bags_collection.iter_by_groups(bags_per_group=bags_per_group),
            total=minibatches_count,
            prefix="Training")

        for item in pipeline:
            assert(isinstance(item, EpochHandlingPipelineItem))
            item.before_epoch(model_context=self.__context,
                              data_type=data_type)

        for bags_group in groups_it:
            assert(isinstance(bags_group, list))

            # Composing minibatch from bags group.
            minibatch = create_batch_by_bags_group(
                bags_coolection_type=self.__context.BagsCollectionType,
                bags_group=bags_group)

            ctx = PipelineContext({"src": minibatch})

            for item in pipeline:
                item.apply(pipeline_ctx=ctx)

    def __try_load_state(self):
        if self.__context.IO.IsPretrainedStateProvided:
            self.__states_provider.load_model(sess=self.__context.Session,
                                              path_tf_prefix=self.__context.IO.get_model_source_path_tf_prefix())

    @staticmethod
    def __get_item_from_pipeline(pipeline, item_type):
        assert(isinstance(pipeline, list))
        assert(issubclass(item_type, EpochHandlingPipelineItem))

        for item in pipeline:
            if isinstance(item, item_type):
                return item

    def __fit(self, epochs_count):
        assert(isinstance(epochs_count, int))
        assert(self.__context.Session is not None)
        assert(isinstance(self.__callback, NetworkCallback))

        operation_cancel = OperationCancellation()
        bags_collection = self.__context.get_bags_collection(DataType.Train)
        self.__callback.on_fit_started(operation_cancel)

        for epoch_index in range(epochs_count):

            if operation_cancel.IsCancelled:
                break

            bags_collection.shuffle()

            self.__run_epoch_pipeline(pipeline=self.__fit_pipeline, data_type=DataType.Train, prefix="Training")

            if self.__callback is not None:
                self.__callback.on_epoch_finished(epoch_index=epoch_index,
                                                  operation_cancel=operation_cancel)

            if BaseTensorflowModel.SaveTensorflowModelStateOnFit:
                self.__states_provider.save_model(sess=self.__context.Session,
                                                  path_tf_prefix=self.__context.IO.get_model_target_path_tf_prefix())

        if self.__callback is not None:
            self.__callback.on_fit_finished()

    # endregion

    def fit(self, model_params, seed):
        assert(isinstance(model_params, NeuralNetworkModelParams))
        self.__context.Network.compile(self.__context.Config, reset_graph=True, graph_seed=seed)
        self.__context.set_optimiser()
        self.__callback.on_initialized(self)
        self.__context.initialize_session()
        self.__try_load_state()
        self.__fit(epochs_count=model_params.EpochsCount)

        self.__context.dispose_session()

    def predict(self, data_type=DataType.Test, do_compile=False, graph_seed=0):
        """ Fills the related labeling collection.
        """
        # Optionally perform network compilation
        if do_compile:
            self.__context.Network.compile(config=self.__context.Config, reset_graph=True, graph_seed=graph_seed)
        self.__context.initialize_session()
        self.__try_load_state()
        self.__run_epoch_pipeline(pipeline=self.__predict_pipeline,
                                  data_type=data_type,
                                  prefix="Predict [{dtype}]".format(dtype=data_type))

    def from_fitted(self, item_type):
        assert(issubclass(item_type, EpochHandlingPipelineItem))
        return self.__get_item_from_pipeline(pipeline=self.__fit_pipeline, item_type=item_type)

    def from_predicted(self, item_type):
        assert (issubclass(item_type, EpochHandlingPipelineItem))
        return self.__get_item_from_pipeline(pipeline=self.__predict_pipeline, item_type=item_type)
