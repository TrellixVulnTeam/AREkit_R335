from arekit.common.experiment.api.ctx_base import ExperimentContext
from arekit.common.experiment.api.io_utils import BaseIOUtils
from arekit.common.folding.types import FoldingType
from arekit.common.folding.united import UnitedFolding
from arekit.contrib.experiment_rusentrel.exp_ds.factory import create_ruattitudes_experiment
from arekit.contrib.experiment_rusentrel.exp_ds.folding import create_ruattitudes_experiment_data_folding
from arekit.contrib.experiment_rusentrel.exp_joined.factory import create_rusentrel_with_ruattitudes_expriment
from arekit.contrib.experiment_rusentrel.exp_sl.factory import create_rusentrel_experiment
from arekit.contrib.experiment_rusentrel.exp_sl.folding import create_rusentrel_experiment_data_folding
from arekit.contrib.experiment_rusentrel.types import ExperimentTypes
from arekit.contrib.source.ruattitudes.io_utils import RuAttitudesVersions
from arekit.contrib.source.rusentrel.io_utils import RuSentRelVersions


def create_experiment(exp_type,
                      exp_ctx,
                      exp_io,
                      folding_type,
                      rusentrel_version,
                      load_ruattitude_docs,
                      ruattitudes_version=None):
    """ This method allows to instanciate all the supported experiments
        by `contrib/experiments/` module of AREkit framework.
    """

    assert(isinstance(exp_io, BaseIOUtils))
    assert(isinstance(exp_type, ExperimentTypes))
    assert(isinstance(exp_ctx, ExperimentContext))
    assert(isinstance(folding_type, FoldingType))
    assert(isinstance(load_ruattitude_docs, bool))

    if exp_type == ExperimentTypes.RuSentRel:
        # Supervised learning experiment type.
        return create_rusentrel_experiment(exp_ctx=exp_ctx,
                                           version=rusentrel_version,
                                           folding_type=folding_type,
                                           exp_io=exp_io)

    if exp_type == ExperimentTypes.RuAttitudes:
        # Application of the distant supervision only (assumes for pretraining purposes)
        return create_ruattitudes_experiment(exp_ctx=exp_ctx,
                                             version=ruattitudes_version,
                                             exp_io=exp_io,
                                             load_docs=load_ruattitude_docs)

    if exp_type == ExperimentTypes.RuSentRelWithRuAttitudes:
        # Supervised learning with an application of distant supervision in training process.
        return create_rusentrel_with_ruattitudes_expriment(exp_io=exp_io,
                                                           exp_ctx=exp_ctx,
                                                           folding_type=folding_type,
                                                           ruattitudes_version=ruattitudes_version,
                                                           rusentrel_version=rusentrel_version,
                                                           load_docs=load_ruattitude_docs)


def create_folding(exp_type, rusentrel_folding_type, rusentrel_version, ruattitudes_version):
    assert(isinstance(rusentrel_folding_type, FoldingType))
    assert(isinstance(exp_type, ExperimentTypes))
    assert(isinstance(rusentrel_version, RuSentRelVersions))
    assert(isinstance(ruattitudes_version, RuAttitudesVersions))

    if exp_type == ExperimentTypes.RuSentRel:
        return create_rusentrel_experiment_data_folding(folding_type=rusentrel_folding_type,
                                                        version=rusentrel_version)

    if exp_type == ExperimentTypes.RuAttitudes:
        return create_ruattitudes_experiment_data_folding(ruattitudes_version)

    if exp_type == ExperimentTypes.RuSentRelWithRuAttitudes:
        rsr = create_rusentrel_experiment_data_folding(folding_type=rusentrel_folding_type,
                                                       version=rusentrel_version)
        ra = create_ruattitudes_experiment_data_folding(version=ruattitudes_version,
                                                        states_count=rsr.StatesCount)
        return UnitedFolding(foldings=[rsr, ra])

