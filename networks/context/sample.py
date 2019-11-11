import collections
import numpy as np
from collections import OrderedDict

from core.networks.context.training.embedding import indices
from core.networks.context.configurations.base import DefaultNetworkConfig

from core.common.entities.entity import Entity
from core.common.text_opinions.end_type import EntityEndType
from core.common.text_opinions.helper import TextOpinionHelper
from core.common.text_opinions.text_opinion import TextOpinion

from core.source.rusentiframes.collection import RuSentiFramesCollection
from core.source.rusentiframes.variants.text_variant import TextFrameVariant


class InputSample(object):
    """
    Base sample which is a part of a Bag
    It provides a to_network_input method which
    generates an input info in an appropriate way
    """

    # It is important to name with 'I_' prefix
    I_X_INDS = "x_indices"
    I_SUBJ_IND = "subj_inds"
    I_OBJ_IND = "obj_inds"
    I_SUBJ_DISTS = "subj_dist"
    I_OBJ_DISTS = "obj_dist"
    I_POS_INDS = "pos_inds"
    I_TERM_TYPE = "term_type"
    I_FRAME_INDS = 'frame_inds'

    # TODO: Should be -1, but now it is not supported
    FRAMES_PAD_VALUE = 0
    POS_PAD_VALUE = 0
    X_PAD_VALUE = 0
    TERM_TYPE_PAD_VALUE = -1

    def __init__(self, X,
                 subj_ind,
                 obj_ind,
                 dist_from_subj,
                 dist_from_obj,
                 pos_indices,
                 term_type,
                 frame_indices,
                 text_opinion_id):
        """
            X: np.ndarray
                x indices for embedding
            y: int
            subj_ind: int
                subject index positions
            obj_ind: int
                object index positions
            dist_from_subj: np.ndarray
            dist_from_obj: np.ndarray
            pos_indices: np.ndarray
        """
        assert(isinstance(X, np.ndarray))
        assert(isinstance(subj_ind, int))
        assert(isinstance(obj_ind, int))
        assert(isinstance(dist_from_subj, np.ndarray))
        assert(isinstance(dist_from_obj, np.ndarray))
        # TODO. Provide syn_objs (OPTIONAL)
        # TODO. Provide syn_subjs (OPTIONAL)
        # TODO. Provide dist_from_near_obj
        # TODO. Provide dist_from_near_subj
        assert(isinstance(pos_indices, np.ndarray))
        assert(isinstance(term_type, np.ndarray))
        assert(isinstance(frame_indices, np.ndarray))
        assert(isinstance(text_opinion_id, int))

        self.__text_opinion_id = text_opinion_id

        self.values = OrderedDict(
            [(InputSample.I_X_INDS, X),
             (InputSample.I_SUBJ_IND, subj_ind),
             (InputSample.I_OBJ_IND, obj_ind),
             (InputSample.I_SUBJ_DISTS, dist_from_subj),
             (InputSample.I_OBJ_DISTS, dist_from_obj),
             (InputSample.I_POS_INDS, pos_indices),
             (InputSample.I_FRAME_INDS, frame_indices),
             (InputSample.I_TERM_TYPE, term_type)])

    # region properties

    @property
    def TextOpinionID(self):
        return self.__text_opinion_id

    # endregion

    # region class methods

    @classmethod
    def create_empty(cls, config):
        assert(isinstance(config, DefaultNetworkConfig))
        blank_terms = np.zeros(config.TermsPerContext)
        blank_frames = np.full(shape=config.FramesPerContext,
                               fill_value=cls.FRAMES_PAD_VALUE)
        return cls(X=blank_terms,
                   subj_ind=0,
                   obj_ind=1,
                   dist_from_subj=blank_terms,
                   dist_from_obj=blank_terms,
                   pos_indices=blank_terms,
                   term_type=blank_terms,
                   frame_indices=blank_frames,
                   text_opinion_id=-1)

    @classmethod
    def from_text_opinion(cls, text_opinion, terms, config):
        assert(isinstance(text_opinion, TextOpinion))
        assert(isinstance(terms, list))
        assert(isinstance(config, DefaultNetworkConfig))

        subj_ind = TextOpinionHelper.extract_entity_sentence_level_term_index(text_opinion, EntityEndType.Source)
        obj_ind = TextOpinionHelper.extract_entity_sentence_level_term_index(text_opinion, EntityEndType.Target)
        frame_inds = [index for index, _ in TextOpinionHelper.iter_frame_variants_with_indices_in_sentence(text_opinion)]
        frame_roles = [
            InputSample.__extract_frame_variant_sentiment_role(
                text_frame_variant=variant,
                frames_collection=config.RuSentiFramesCollectionInstance)
            for _, variant in TextOpinionHelper.iter_frame_variants_with_indices_in_sentence(text_opinion)]

        pos_indices = indices.calculate_pos_indices_for_terms(
            terms=terms,
            pos_tagger=config.PosTagger)

        x_indices = indices.calculate_embedding_indices_for_terms(
            terms=terms,
            term_embedding_matrix=config.TermEmbeddingMatrix,
            word_embedding=config.WordEmbedding,
            missed_word_embedding=config.MissedWordEmbedding,
            token_embedding=config.TokenEmbedding,
            frames_embedding=config.FrameEmbedding)

        term_type = InputSample.__create_term_types(terms)

        sentence_len = len(x_indices)

        pad_size = config.TermsPerContext

        if sentence_len < pad_size:
            cls.__pad_right_inplace(pos_indices, pad_size=pad_size, filler=cls.POS_PAD_VALUE)
            cls.__pad_right_inplace(x_indices, pad_size=pad_size, filler=cls.X_PAD_VALUE)
            # TODO. Provide it correct.
            cls.__pad_right_inplace(term_type, pad_size=pad_size, filler=cls.TERM_TYPE_PAD_VALUE)
        else:
            b, e, subj_ind, obj_ind = cls.__crop_bounds(
                sentence_len=sentence_len,
                window_size=config.TermsPerContext,
                e1=subj_ind,
                e2=obj_ind)

            frame_inds = map(lambda frame_index: cls.__shift_frame_index(w_b=b, w_e=e,
                                                                         frame_index=frame_index,
                                                                         placeholder=cls.FRAMES_PAD_VALUE),
                             frame_inds)

            frame_inds = cls.__shift_position_indices(begin=b, end=e,
                                                      inds=frame_inds,
                                                      pad_value=cls.FRAMES_PAD_VALUE)

            cls.__crop_inplace([x_indices, pos_indices, term_type], begin=b, end=e)

        cls.__fit_frames_dependent_indices_inplace(inds=frame_inds, frames_per_context=config.FramesPerContext)
        cls.__fit_frames_dependent_indices_inplace(inds=frame_roles, frames_per_context=config.FramesPerContext)

        assert(len(pos_indices) ==
               len(x_indices) ==
               len(term_type) ==
               config.TermsPerContext)

        dist_from_subj = InputSample.__dist(subj_ind, config.TermsPerContext)
        dist_from_obj = InputSample.__dist(obj_ind, config.TermsPerContext)

        return cls(X=np.array(x_indices),
                   subj_ind=subj_ind,
                   obj_ind=obj_ind,
                   dist_from_subj=dist_from_subj,
                   dist_from_obj=dist_from_obj,
                   pos_indices=np.array(pos_indices),
                   term_type=np.array(term_type),
                   frame_indices=np.array(frame_inds),
                   text_opinion_id=text_opinion.TextOpinionID)

    # endregion

    # region private methods

    @staticmethod
    def __fit_frames_dependent_indices_inplace(inds, frames_per_context):
        if len(inds) < frames_per_context:
            InputSample.__pad_right_inplace(lst=inds,
                                            pad_size=frames_per_context,
                                            filler=InputSample.FRAMES_PAD_VALUE)
        else:
            del inds[frames_per_context:]

    @staticmethod
    def __shift_position_indices(inds, begin, end, pad_value):
        return map(lambda frame_index: InputSample.__shift_frame_index(w_b=begin, w_e=end,
                                                                       frame_index=frame_index,
                                                                       placeholder=pad_value),
                   inds)

    @staticmethod
    # TODO. Fix dependency from source.
    # TODO. Implement in different file.
    def __extract_frame_variant_sentiment_role(text_frame_variant, frames_collection):
        assert(isinstance(text_frame_variant, TextFrameVariant))
        assert(isinstance(frames_collection, RuSentiFramesCollection))
        frame_id = text_frame_variant.Variant.FrameID
        return frames_collection.try_get_frame_polarity(frame_id=frame_id,
                                                        role_src=u'a0',
                                                        role_dest=u'a1')

    @staticmethod
    def __dist(pos, size):
        result = np.zeros(size)
        for i in xrange(len(result)):
            result[i] = i-pos if i-pos >= 0 else i-pos+size
        return result

    @staticmethod
    def __create_term_types(terms):
        assert(isinstance(terms, collections.Iterable))
        feature = []
        for term in terms:
            if isinstance(term, unicode):
                feature.append(0)
            elif isinstance(term, Entity):
                feature.append(1)
            else:
                feature.append(-1)

        return feature

    @staticmethod
    def __crop_inplace(lists, begin, end):
        for i, lst in enumerate(lists):
            if end < len(lst):
                del lst[end:]
            del lst[:begin]

    @staticmethod
    def check_ability_to_create_sample(window_size, text_opinion):
        return abs(TextOpinionHelper.calculate_distance_between_entities_in_terms(text_opinion)) < window_size

    @staticmethod
    def __crop_bounds(sentence_len, window_size, e1, e2):
        assert(isinstance(sentence_len, int))
        assert(isinstance(window_size, int) and window_size > 0)
        assert(isinstance(e1, int) and isinstance(e2, int))
        assert(e1 >= 0 and e2 >= 0)
        assert(e1 < sentence_len and e2 < sentence_len)
        w_begin = 0
        w_end = window_size
        while not (InputSample.__in_window(w_b=w_begin, w_e=w_end, i=e1) and
                   InputSample.__in_window(w_b=w_begin, w_e=w_end, i=e2)):
            w_begin += 1
            w_end += 1

        return w_begin, w_end, e1 - w_begin, e2 - w_begin

    @staticmethod
    def __in_window(w_b, w_e, i):
        return i >= w_b and i < w_e

    @staticmethod
    def __pad_right_inplace(lst, pad_size, filler):
        """
        Pad list ('lst') with additional elements (filler)

        lst: list
        pad_size: int
            result size
        filler: int
        returns: None
            inplace
        """
        assert(pad_size - len(lst) > 0)
        lst.extend([filler] * (pad_size - len(lst)))

    @staticmethod
    def __shift_frame_index(w_b, w_e, frame_index, placeholder):
        shifted = frame_index - w_b
        return placeholder if not InputSample.__in_window(w_b=w_b, w_e=w_e, i=frame_index) else shifted

    @staticmethod
    def iter_parameters():
        for var_name in dir(InputSample):
            if not var_name.startswith('I_'):
                continue
            yield getattr(InputSample, var_name)

    def __iter__(self):
        for key, value in self.values.iteritems():
            yield key, value

    # endregion

    # region public methods

    def save(self, filepath):
        raise NotImplementedError()

    def load(self, filepath):
        raise NotImplementedError()

    # endregion
