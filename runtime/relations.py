from core.source.news import News
from core.env import stemmer
from core.source.opinion import Opinion
from core.source.synonyms import SynonymsCollection


class RelationCollection:

    def __init__(self, relation_list=[]):
        assert(type(relation_list) == list)
        self.relations = relation_list

    @staticmethod
    def from_news_opinion(news, opinion, synonyms, ignored_entity_values=[], debug=False):
        assert(isinstance(news, News))
        assert(isinstance(opinion, Opinion))
        assert(isinstance(synonyms, SynonymsCollection))

        left_values = RelationCollection._get_appropriate_entity_values(
            opinion.value_left, news.entities, synonyms)
        right_values = RelationCollection._get_appropriate_entity_values(
            opinion.value_right, news.entities, synonyms)

        # TODO. We guarantee that these left and right values are not lemmatized
        if len(left_values) == 0:
            if debug:
                print "Appropriate entity for '{}'->'...' has not been found".format(
                    opinion.value_left.encode('utf-8'))
            return RelationCollection()

        if len(right_values) == 0:
            if debug:
                print "Appropriate entity for '...'->'{}' has not been found".format(
                    opinion.value_right.encode('utf-8'))
            return RelationCollection()

        relations = []
        for entity_left in left_values:
            for entity_right in right_values:

                if RelationCollection._is_ignored(entity_left, stemmer, ignored_entity_values):
                    continue
                if RelationCollection._is_ignored(entity_right, stemmer, ignored_entity_values):
                    continue

                entities_left_ids = news.entities.get_entity_by_value(entity_left)
                entities_right_ids = news.entities.get_entity_by_value(entity_right)

                for e1_ID in entities_left_ids:
                    for e2_ID in entities_right_ids:
                        e1 = news.entities.get_entity_by_id(e1_ID)
                        e2 = news.entities.get_entity_by_id(e2_ID)
                        r = Relation(e1.ID, e2.ID, news)
                        relations.append(r)

        return RelationCollection(relations)

    def apply_filter(self, filter_function):
        self.relations = [r for r in self.relations if filter_function(r)]

    @staticmethod
    def _is_ignored(entity_value, stemmer, ignored_entitiy_values):
        assert(type(ignored_entitiy_values) == list)
        entity_value = stemmer.lemmatize_to_str(entity_value)
        if entity_value in ignored_entitiy_values:
            # print "ignored: '{}'".format(entity_value.encode('utf-8'))
            return True
        return False

    @staticmethod
    def _get_appropriate_entity_values(opinion_value, entities, synonyms):
        if synonyms.has_synonym(opinion_value):
            return filter(
                lambda s: entities.has_entity_by_value(s),
                synonyms.get_synonyms_list(opinion_value))
        elif entities.has_entity_by_value(opinion_value):
            return [opinion_value]
        else:
            return []

    def __getitem__(self, item):
        """
        item: int
        """
        assert(type(item) == int)
        return self.relations[item]

    def __len__(self):
        return len(self.relations)

    def __iter__(self):
        for r in self.relations:
            yield r


class Relation:
    """ Strict Relation between two Entities
    """

    def __init__(self, entity_left_ID, entity_right_ID, news):
        assert(type(entity_left_ID) == unicode)
        assert(type(entity_right_ID) == unicode)
        assert(isinstance(news, News))
        self.entity_left_ID = entity_left_ID
        self.entity_right_ID = entity_right_ID
        self.news = news


    def get_left_entity_value(self):
        """
        returns: unicode
        """
        entity = self.news.entities.get_entity_by_id(self.entity_left_ID)
        return entity.value

    def get_right_entity_value(self):
        """
        returns: unicode
        """
        entity = self.news.entities.get_entity_by_id(self.entity_right_ID)
        return entity.value
