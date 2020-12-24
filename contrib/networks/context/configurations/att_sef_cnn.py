from arekit.contrib.networks.attention.architectures.mlp_interactive import InteractiveMLPAttention
from arekit.contrib.networks.attention.configurations.mlp_interactive import InteractiveMLPAttentionConfig
from arekit.contrib.networks.context.configurations.base.att_cnn_base import AttentionCNNBaseConfig


class AttentionSynonymEndsAndFramesCNNConfig(AttentionCNNBaseConfig):

    def __init__(self):
        super(AttentionSynonymEndsAndFramesCNNConfig, self).__init__()
        self.__attention = None
        self.__attention_config = InteractiveMLPAttentionConfig(
            keys_count=self.FramesPerContext + 2 * self.SynonymsPerContext)

    # region properties

    @property
    def AttentionModel(self):
        return self.__attention

    # endregion

    # region public methods

    def get_attention_parameters(self):
        return self.__attention_config.get_parameters()

    def init_config_depended_parameters(self):
        assert(self.__attention is None)
        super(AttentionSynonymEndsAndFramesCNNConfig, self).init_config_depended_parameters()

        self.__attention = InteractiveMLPAttention(
            cfg=self.__attention_config,
            batch_size=self.BatchSize,
            terms_per_context=self.TermsPerContext,
            support_zero_length=False)

    # endregion
