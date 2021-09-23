import logging

import numpy as np

from arekit.contrib.networks.core.input.providers.npz_utils import NpzUtilsProvider

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EmbeddingHelper:

    @staticmethod
    def save_embedding(data, target):
        NpzUtilsProvider.save(data=data, target=target)
        logger.info("Saving embedding [size={shape}]: {filepath}".format(shape=data.shape,
                                                                         filepath=target))

    @staticmethod
    def save_vocab(data, target):
        logger.info("Saving vocabulary [size={size}]: {filepath}".format(size=len(data),
                                                                         filepath=target))
        np.savez(target, data)

    @staticmethod
    def load_embedding(source):
        embedding = NpzUtilsProvider.load(source)
        logger.info("Embedding read [size={size}]: {filepath}".format(size=embedding.shape,
                                                                      filepath=source))
        return embedding

    @staticmethod
    def load_vocab(source):
        vocab = dict(NpzUtilsProvider.load(source))
        logger.info("Vocabulary read [size={size}]: {filepath}".format(size=len(vocab),
                                                                       filepath=source))
        return vocab
