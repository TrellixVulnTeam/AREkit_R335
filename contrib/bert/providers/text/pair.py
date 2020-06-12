# -*- coding: utf-8 -*-
from arekit.common.entities.types import EntityType
from arekit.common.labels.base import Label
from arekit.common.labels.str_fmt import StringLabelsFormatter
from arekit.contrib.bert.providers.text.single import SingleTextProvider


class PairTextProvider(SingleTextProvider):
    """
    Provides additionally text_b parameter

    Considered to utilize an inner part in context, between opinion participants.
    """

    TEXT_B = u"text_b"

    def __init__(self, text_b_template, labels_formatter, entities_formatter, synonyms):
        """
        text_b_template: unicode
            assumes to include {context} in related template,
            and {label} (optional)
        labels_formatter: StringLabelsFormatter
        entities_formatter: StringEntitiesFormatter
        """
        assert(isinstance(text_b_template, unicode))
        assert(isinstance(labels_formatter, StringLabelsFormatter))
        super(PairTextProvider, self).__init__(
            entities_formatter=entities_formatter,
            synonyms=synonyms)
        self.__text_b_template = text_b_template
        self.__labels_formatter = labels_formatter

    def get_text_template(self):
        raise NotImplementedError()

    def iter_columns(self):
        for col_name in super(PairTextProvider, self).iter_columns():
            yield col_name
        yield self.TEXT_B

    def add_text_in_row(self, row, sentence_terms, s_ind, t_ind, expected_label):
        assert(isinstance(expected_label, Label))

        super(PairTextProvider, self).add_text_in_row(row=row,
                                                      sentence_terms=sentence_terms,
                                                      s_ind=s_ind,
                                                      t_ind=t_ind,
                                                      expected_label=expected_label)

        l = min(s_ind, t_ind) + 1
        r = max(s_ind, t_ind)
        inner_context = list(self._iterate_sentence_terms(sentence_terms[l:r]))

        row[self.TEXT_B] = self.__text_b_template.format(
            subject=self._entities_formatter.to_string(None, EntityType.Subject),
            object=self._entities_formatter.to_string(None, EntityType.Object),
            context=self._process_text(self.TERMS_SEPARATOR.join(inner_context)),
            label=self.__labels_formatter.label_to_str(expected_label))

        return row
