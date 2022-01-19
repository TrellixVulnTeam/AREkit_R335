from arekit.common.experiment.api.ctx_base import DataIO
from arekit.common.experiment.callback import ExperimentCallback


class TrainingData(DataIO):
    """ Data, that is necessary for models training stage.
    """

    def __init__(self, labels_count, callback):
        assert(isinstance(callback, ExperimentCallback))
        super(TrainingData, self).__init__()
        self.__labels_count = labels_count
        self.__exp_callback = callback

    @property
    def LabelsCount(self):
        return self.__labels_count

    @property
    def Evaluator(self):
        raise NotImplementedError()

    @property
    def Callback(self):
        return self.__exp_callback
