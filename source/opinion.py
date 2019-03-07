# -*- coding: utf-8 -*-
import io

from core.processing.lemmatization.base import Stemmer
from core.evaluation.labels import Label
from core.source.synonyms import SynonymsCollection


class OpinionCollection:
    """ Collection of sentiment opinions between entities
    """

    def __init__(self, opinions, synonyms, debug_mode=False):
        assert(isinstance(opinions, list) or isinstance(opinions, type(None)))
        assert(isinstance(synonyms, SynonymsCollection))
        assert(isinstance(debug_mode, bool))
        self.debug_mode = debug_mode
        self.opinions = [] if opinions is None else opinions
        self.synonyms = synonyms
        self.by_synonyms = self.__create_index()

    def __add_synonym(self, value):
        if self.synonyms.IsReadOnly:
            raise Exception((u"Failed to add '{}'. Synonym collection is read only!".format(value)).encode('utf-8'))
        self.synonyms.add_synonym(value)

    def __create_index(self):
        index = {}
        for opinion in self.opinions:
            OpinionCollection.__add_opinion(opinion, index, self.synonyms, check=False)
        return index

    @classmethod
    def from_file(cls, filepath, synonyms, debug=False):
        assert(isinstance(synonyms, SynonymsCollection))

        opinions = []
        with io.open(filepath, "r", encoding='utf-8') as f:
            for i, line in enumerate(f.readlines()):

                if line == '\n':
                    continue

                args = line.strip().split(',')

                if len(args) < 3:
                    print "should be at least 3 arguments: {}, '{}'".format(
                        i, line.encode('utf-8'))
                    continue

                entity_left = args[0].strip()
                entity_right = args[1].strip()
                sentiment = Label.from_str(args[2].strip())

                o = Opinion(entity_left, entity_right, sentiment)
                opinions.append(o)

        return cls(opinions, synonyms, debug)

    def has_synonymous_opinion(self, opinion, sentiment=None):
        assert(isinstance(opinion, Opinion))
        assert(sentiment is None or isinstance(sentiment, Label))

        if not opinion.has_synonym_for_left(self.synonyms):
            return False
        if not opinion.has_synonym_for_right(self.synonyms):
            return False

        s_id = opinion.create_synonym_id(self.synonyms)
        if s_id in self.by_synonyms:
            f_o = self.by_synonyms[s_id]
            return True if sentiment is None else f_o.sentiment == sentiment

        return False

    def get_synonymous_opinion(self, opinion):
        assert(isinstance(opinion, Opinion))
        s_id = opinion.create_synonym_id(self.synonyms)
        return self.by_synonyms[s_id]

    def add_opinion(self, opinion):
        assert(isinstance(opinion, Opinion))

        if not opinion.has_synonym_for_left(self.synonyms):
            self.__add_synonym(opinion.value_left)

        if not opinion.has_synonym_for_right(self.synonyms):
            self.__add_synonym(opinion.value_right)

        self.__add_opinion(opinion, self.by_synonyms, self.synonyms)
        self.opinions.append(opinion)

    def save(self, filepath):
        sorted_ops = sorted(self.opinions, key=lambda o: o.value_left + o.value_right)
        with io.open(filepath, 'w') as f:
            for o in sorted_ops:
                f.write(o.to_unicode())
                f.write(u'\n')

    @staticmethod
    def __add_opinion(opinion, collection, synonyms, check=True):
        key = opinion.create_synonym_id(synonyms)

        assert(isinstance(key, unicode))
        if check:
            assert(key not in collection)
        if key in collection:
            return False
        collection[key] = opinion
        return True

    def iter_sentiment(self, sentiment):
        assert(isinstance(sentiment, Label))
        for o in self.opinions:
            if o.sentiment == sentiment:
                yield o

    def __len__(self):
        return len(self.opinions)

    def __iter__(self):
        for o in self.opinions:
            yield o


class Opinion:
    """ Source opinion description
    """

    def __init__(self, value_left, value_right, sentiment):
        assert(isinstance(value_left, unicode))
        assert(isinstance(value_right, unicode))
        assert(isinstance(sentiment, Label))
        assert(',' not in value_left)
        assert(',' not in value_right)
        self.value_left = value_left.lower()
        self.value_right = value_right.lower()
        self.sentiment = sentiment

    def to_unicode(self):
        return u"{}, {}, {}, current".format(
            self.value_left,
            self.value_right,
            self.sentiment.to_str())

    def create_synonym_id(self, synonyms):
        assert(isinstance(synonyms, SynonymsCollection))
        return u"{}_{}".format(
            synonyms.get_synonym_group_index(self.value_left),
            synonyms.get_synonym_group_index(self.value_right))

    def has_synonym_for_left(self, synonyms):
        assert(isinstance(synonyms, SynonymsCollection))
        return synonyms.has_synonym(self.value_left)

    def has_synonym_for_right(self, synonyms):
        assert(isinstance(synonyms, SynonymsCollection))
        return synonyms.has_synonym(self.value_right)
