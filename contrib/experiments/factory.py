from arekit.common.experiment.data.base import DataIO
from arekit.common.experiment.folding.types import FoldingType
from arekit.contrib.experiments.ruattitudes.experiment import RuAttitudesExperiment
from arekit.contrib.experiments.rusentrel.experiment import RuSentRelExperiment
from arekit.contrib.experiments.rusentrel_ds.experiment import RuSentRelWithRuAttitudesExperiment
from arekit.contrib.experiments.types import ExperimentTypes


def create_experiment(exp_type,
                      experiment_data,
                      folding_type,
                      rusentrel_version,
                      is_training,
                      experiment_io_type,
                      ruattitudes_version=None):
    """ This method allows to instanciate all the supported experiments
        by `contrib/experiments/` module of AREkit framework.
    """

    assert(isinstance(exp_type, ExperimentTypes))
    assert(isinstance(experiment_data, DataIO))
    assert(isinstance(folding_type, FoldingType))
    assert(isinstance(is_training, bool))

    if exp_type == ExperimentTypes.RuSentRel:
        # Supervised learning experiment type.
        return RuSentRelExperiment(data_io=experiment_data,
                                   version=rusentrel_version,
                                   folding_type=folding_type,
                                   experiment_io_type=experiment_io_type)

    if exp_type == ExperimentTypes.RuAttitudes:
        # Application of the distant supervision only (assumes for pretraining purposes)
        return RuAttitudesExperiment(data_io=experiment_data,
                                     version=ruattitudes_version,
                                     experiment_io_type=experiment_io_type,
                                     load_ruatittudes=is_training)

    if exp_type == ExperimentTypes.RuSentRelWithRuAttitudes:
        # Supervised learning with an application of distant supervision in training process.
        return RuSentRelWithRuAttitudesExperiment(ruattitudes_version=ruattitudes_version,
                                                  data_io=experiment_data,
                                                  rusentrel_version=rusentrel_version,
                                                  folding_type=folding_type,
                                                  experiment_io_type=experiment_io_type)
