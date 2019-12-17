from arekit.networks.attention.architectures.mlp import MLPAttention
from arekit.networks.attention.configurations.mlp import MLPAttentionConfig
from arekit.networks.context.configurations.att_cnn_base import AttentionCNNBaseConfig


class AttentionAttitudeEndsCNNConfig(AttentionCNNBaseConfig):

    def __init__(self):
        super(AttentionAttitudeEndsCNNConfig, self).__init__()
        self.__attention = None
        self.__attention_config = MLPAttentionConfig()

    # region properties

    @property
    def AttentionModel(self):
        return self.__attention

    # endregion

    # region public methods

    def get_attention_parameters(self):
        return self.__attention_config.get_parameters()

    def notify_initialization_completed(self):
        assert(self.__attention is None)

        self.__attention = MLPAttention(
            cfg=self.__attention_config,
            batch_size=self.BatchSize,
            terms_per_context=self.TermsPerContext)

    # endregion
