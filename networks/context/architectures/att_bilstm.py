from collections import OrderedDict

import tensorflow as tf

from core.networks.attention.architectures.peng_zhou import attention_by_peng_zhou
from core.networks.context.architectures.base import BaseContextNeuralNetwork
from core.networks.context.architectures.sequence import get_cell
from core.networks.context.configurations.att_bilstm import AttBiLSTMConfig
from core.networks.context.sample import InputSample
import utils


class AttBiLSTM(BaseContextNeuralNetwork):
    """
    Authors: Peng Zhou, Wei Shi, Jun Tian, Zhenyu Qi, Bingchen Li, Hongwei Hao, Bo Xu
    Paper: https://www.aclweb.org/anthology/P16-2034
    Code author: SeoSangwoo (c), https://github.com/SeoSangwoo
    Code: https://github.com/SeoSangwoo/Attention-Based-BiLSTM-relation-extraction
    """

    H_W = "W"
    H_b = "b"
    __attention_scope = "attention"

    def __init__(self):
        super(AttBiLSTM, self).__init__()
        self.__att_alphas = None
        self.__hidden = OrderedDict()

    @property
    def ContextEmbeddingSize(self):
        return self.Config.HiddenSize

    # region init methods

    def init_context_embedding(self, embedded_terms):
        assert(isinstance(self.Config, AttBiLSTMConfig))

        # Bidirectional LSTM
        with tf.variable_scope("bi-lstm"):

            # Length Calculation
            x_length = utils.calculate_sequence_length(self.get_input_parameter(InputSample.I_X_INDS))
            s_length = tf.cast(x=tf.maximum(x_length, 1), dtype=tf.int32)

            # Forward
            _fw_cell = get_cell(hidden_size=self.Config.HiddenSize,
                                cell_type=self.Config.CellType,
                                lstm_initializer=self.Config.LSTMCellInitializer)

            # TODO. Make a part of config. and move into method above.
            fw_cell = tf.nn.rnn_cell.DropoutWrapper(
                cell=_fw_cell,
                output_keep_prob=self.Config.DropoutRNNKeepProb)

            # Backward
            _bw_cell = get_cell(hidden_size=self.Config.HiddenSize,
                                cell_type=self.Config.CellType,
                                lstm_initializer=self.Config.LSTMCellInitializer)

            # TODO. Make a part of config. and move into method above.
            bw_cell = tf.nn.rnn_cell.DropoutWrapper(
                cell=_bw_cell,
                output_keep_prob=self.Config.DropoutRNNKeepProb)

            # Output
            rnn_outputs, _ = tf.nn.bidirectional_dynamic_rnn(cell_fw=fw_cell,
                                                             cell_bw=bw_cell,
                                                             inputs=embedded_terms,
                                                             sequence_length=s_length,
                                                             dtype=tf.float32)

            # TODO. Here we can make an extraction of frames.
            # TODO. As a part of separated model
            # TODO. att_frames_bilstm.
            # TODO. ----------------------------------------
            rnn_outputs = tf.add(rnn_outputs[0], rnn_outputs[1])
            # TODO. ----------------------------------------

        # Attention
        with tf.variable_scope('attention'):
            attn, self.__att_alphas = attention_by_peng_zhou(rnn_outputs)

        return attn

    def init_logits_unscaled(self, context_embedding):
        W = [tensor for var_name, tensor in self.__hidden.iteritems() if 'W' in var_name]
        b = [tensor for var_name, tensor in self.__hidden.iteritems() if 'b' in var_name]
        activations = [tf.tanh] * len(W)
        activations.append(None)
        return utils.get_k_layer_pair_logits(g=context_embedding,
                                             W=W,
                                             b=b,
                                             dropout_keep_prob=self.DropoutKeepProb,
                                             activations=activations)

    def init_hidden_states(self):
        self.__hidden[self.H_W] = tf.get_variable(
            name=self.H_W,
            shape=[self.ContextEmbeddingSize, self.Config.ClassesCount],
            initializer=self.Config.WeightInitializer,
            regularizer=self.Config.LayerRegularizer,
            dtype=tf.float32)

        self.__hidden[self.H_b] = tf.get_variable(
            name=self.H_b,
            shape=[self.Config.ClassesCount],
            initializer=self.Config.BiasInitializer,
            regularizer=self.Config.LayerRegularizer,
            dtype=tf.float32)

    # endregion

    # region iter methods

    def iter_hidden_parameters(self):
        for key, value in self.__hidden.iteritems():
            yield key, value

    def iter_input_dependent_hidden_parameters(self):
        for name, value in super(AttBiLSTM, self).iter_input_dependent_hidden_parameters():
            yield name, value

        yield u"ATT_Weights", self.__att_alphas

    # endregion
