from arekit.common.experiment.api.ctx_base import ExperimentContext


class ExperimentTrainingContext(ExperimentContext):
    """ Data, that is necessary for models training stage.
    """

    def __init__(self, labels_count, name_provider):
        super(ExperimentTrainingContext, self).__init__(name_provider)
        self.__labels_count = labels_count

    @property
    def LabelsCount(self):
        return self.__labels_count
