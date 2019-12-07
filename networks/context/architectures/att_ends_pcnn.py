import tensorflow as tf

from arekit.networks.attention.helpers import embedding
from arekit.networks.context.architectures.pcnn import PiecewiseCNN


class AttentionAttitudeEndsPCNN(PiecewiseCNN):
    __attention_var_scope_name = 'attention-model'

    def __init__(self):
        super(AttentionAttitudeEndsPCNN, self).__init__()
        self.__att_weights = None

    # region properties

    @property
    def ContextEmbeddingSize(self):
        return super(AttentionAttitudeEndsPCNN, self).ContextEmbeddingSize + \
               self.Config.AttentionModel.AttentionEmbeddingSize

    # endregion

    def set_att_weights(self, weights):
        self.__att_weights = weights

    def get_att_input(self):
        return self.get_input_entity_pairs()

    # region public 'init' methods

    def init_input(self):
        super(AttentionAttitudeEndsPCNN, self).init_input()
        with tf.variable_scope(self.__attention_var_scope_name):
            self.Config.AttentionModel.init_input(p_names_with_sizes=embedding.get_ns(self))

    def init_hidden_states(self):
        super(AttentionAttitudeEndsPCNN, self).init_hidden_states()
        with tf.variable_scope(self.__attention_var_scope_name):
            self.Config.AttentionModel.init_hidden()

    def init_context_embedding(self, embedded_terms):
        g = super(AttentionAttitudeEndsPCNN, self).init_context_embedding(embedded_terms)

        att_e, att_weights = embedding.init_mlp_attention_embedding(
            ctx_network=self,
            mlp_att=self.Config.AttentionModel,
            keys=self.get_att_input())

        self.set_att_weights(att_weights)

        return tf.concat([g, att_e], axis=-1)

    # endregion

    # region public 'iter' methods

    def iter_input_dependent_hidden_parameters(self):
        for name, value in super(AttentionAttitudeEndsPCNN, self).iter_input_dependent_hidden_parameters():
            yield name, value

        yield u"ATT_Weights", self.__att_weights

    def iter_hidden_parameters(self):
        for key, value in super(AttentionAttitudeEndsPCNN, self).iter_hidden_parameters():
            yield key, value

    # endregion