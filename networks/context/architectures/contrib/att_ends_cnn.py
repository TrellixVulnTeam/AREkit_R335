import tensorflow as tf
from arekit.networks.context.architectures.att_cnn_base import AttentionCNNBase
from arekit.networks.context.sample import InputSample


class AttentionEndsCNN(AttentionCNNBase):

    def get_att_input(self):
        return tf.stack([self.get_input_parameter(InputSample.I_SUBJ_IND),
                         self.get_input_parameter(InputSample.I_OBJ_IND)],
                        axis=-1)

