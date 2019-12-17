from arekit.networks.attention.architectures.mlp_interactive import InteractiveMLPAttention
from arekit.networks.attention.configurations.mlp_interactive import InteractiveMLPAttentionConfig
from arekit.networks.context.configurations.att_cnn_base import AttentionCNNBaseConfig


class AttentionAttitudeSynonymEndsCNNConfig(AttentionCNNBaseConfig):

    def __init__(self):
        super(AttentionAttitudeSynonymEndsCNNConfig, self).__init__()
        self.__attention = None
        self.__attention_config = InteractiveMLPAttentionConfig(self.SynonymsPerContext * 2)

    # region properties

    @property
    def AttentionModel(self):
        return self.__attention

    @property
    def MLPAttentionConfig(self):
        return self.__attention_config

    # endregion

    # region public methods

    def notify_initialization_completed(self):
        assert(self.__attention is None)

        self.__attention = InteractiveMLPAttention(
            cfg=self.__attention_config,
            batch_size=self.BatchSize,
            terms_per_context=self.TermsPerContext)

    # endregion
