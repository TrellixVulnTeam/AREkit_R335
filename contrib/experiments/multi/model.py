from arekit.contrib.experiments.multi.helper.initialization import MultiInstanceModelInitHelper
from arekit.contrib.experiments.single.model import SingleInstanceTensorflowModel
from arekit.networks.multi.training.batch import MultiInstanceBatch


class MultiInstanceTensorflowModel(SingleInstanceTensorflowModel):
    """
    This model assumes to perform a classification of a set of instances (sentences, or contexts)
    with an attitude mentioned in each sentence.
    """

    def create_batch_by_bags_group(self, bags_group):
        return MultiInstanceBatch(bags_group)

    def create_model_init_helper(self):
        return MultiInstanceModelInitHelper(io=self.IO, config=self.Config)
