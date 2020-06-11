from arekit.common.context.terms_mapper import TextTermsMapper
from arekit.common.entities.base import Entity
from arekit.common.entities.str_mask_fmt import StringEntitiesFormatter
from arekit.common.entities.types import EntityType
from arekit.common.synonyms import SynonymsCollection
from arekit.common.text_frame_variant import TextFrameVariant
from arekit.processing.text.token import Token


class StringTextTermsMapper(TextTermsMapper):

    def __init__(self, entities_formatter, synonyms):
        assert(isinstance(entities_formatter, StringEntitiesFormatter))
        assert(isinstance(synonyms, SynonymsCollection))
        self.__entities_formatter = entities_formatter
        self.__synonyms = synonyms
        self.__s_ind = None
        self.__t_ind = None
        self.__s_group = None
        self.__t_group = None

    def __syn_group(self, entity):
        assert(isinstance(entity, Entity))

        if entity is None:
            return None

        if not self.__synonyms.contains_synonym_value(entity.Value):
            return None

        return self.__synonyms.get_synonym_group_index(entity.Value)

    def set_s_ind(self, s_ind):
        assert(isinstance(s_ind, int))
        self.__s_ind = s_ind

    def set_t_ind(self, t_ind):
        assert(isinstance(t_ind, int))
        self.__t_ind = t_ind

    def _after_mapping(self):
        """ In order to prevent bugs.
            Every index should be declared before mapping.
        """
        self.__s_ind = None
        self.__t_ind = None

    def iter_mapped(self, terms):
        terms_list = list(terms)
        self.__s_group = self.__syn_group(terms_list[self.__s_ind] if self.__s_ind is not None else None)
        self.__t_group = self.__syn_group(terms_list[self.__t_ind] if self.__t_ind is not None else None)

        for mapped in super(StringTextTermsMapper, self).iter_mapped(terms):
            yield mapped

    def map_entity(self, e_ind, entity):
        if e_ind == self.__s_ind:
            yield self.__entities_formatter.to_string(original_value=entity,
                                                      entity_type=EntityType.Subject)
        elif e_ind == self.__t_ind:
            yield self.__entities_formatter.to_string(original_value=entity,
                                                      entity_type=EntityType.Object)
        elif self.__syn_group(entity) == self.__s_group:
            yield self.__entities_formatter.to_string(original_value=entity,
                                                      entity_type=EntityType.SynonymSubject)
        elif self.__syn_group(entity) == self.__t_group:
            yield self.__entities_formatter.to_string(original_value=entity,
                                                      entity_type=EntityType.SynonymObject)
        else:
            yield self.__entities_formatter.to_string(original_value=entity,
                                                      entity_type=EntityType.Other)

    def map_word(self, w_ind, word):
        return word

    def map_text_frame_variant(self, fv_ind, text_frame_variant):
        assert(isinstance(text_frame_variant, TextFrameVariant))
        return text_frame_variant.Variant.get_value()

    def map_token(self, t_ind, token):
        assert(isinstance(token, Token))
        return token.get_meta_value()
