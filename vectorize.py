#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import logging
import numpy as np
from gensim.models.word2vec import Word2Vec

import core.environment as env

from core.source.opinion import OpinionCollection
from core.source.entity import EntityCollection
from core.source.news import News
from core.source.relations import Relation
from core.source.vectors import CommonRelationVectorCollection, CommonRelationVector

from core.features.distance import DistanceFeature
from core.features.similarity import SimilarityFeature
from core.features.lexicon import LexiconFeature
from core.features.pattern import PatternFeature
from core.features.entities import EntitiesBetweenFeature
from core.features.prepositions import PrepositionsCountFeature
from core.features.frequency import EntitiesFrequency

from core.processing.prefix import SentimentPrefixProcessor

import io_utils


def is_ignored(entity_value):
    ignored = io_utils.get_ignored_entity_values()
    entity_value = env.stemmer.lemmatize_to_str(entity_value)
    if entity_value in ignored:
        print "ignored: '{}'".format(entity_value.encode('utf-8'))
        return True
    return False


def vectorize_train(news, entities, opinion_collections, features):
    """ Vectorize news of train collection that has opinion labeling
    """
    collection = CommonRelationVectorCollection()
    sentiment_to_int = {'pos': 1, 'neg': -1, 'neu': 0}
    for opinions in opinion_collections:
        for opinion in opinions:

            if not entities.has_enity_by_value(opinion.entity_left):
                continue

            if not entities.has_enity_by_value(opinion.entity_right):
                continue

            if is_ignored(opinion.entity_left):
                continue

            if is_ignored(opinion.entity_right):
                continue

            entities_left_IDs = entities.get_by_value(opinion.entity_left)
            entities_right_IDs = entities.get_by_value(opinion.entity_right)

            r_features = None
            r_count = len(entities_left_IDs) * len(entities_right_IDs)
            for e1_ID in entities_left_IDs:
                for e2_ID in entities_right_IDs:
                    e1 = entities.get_by_ID(e1_ID)
                    e2 = entities.get_by_ID(e2_ID)
                    r = Relation(e1.ID, e2.ID, news)
                    features = np.concatenate([f.create(r) for f in FEATURES])

                    if r_features is None:
                        r_features = features
                    else:
                        r_features += features

            if r_count == 0:
                continue

            r_features = r_features/r_count

            vector = CommonRelationVector(
                opinion.entity_left, opinion.entity_right,
                r_features, sentiment_to_int[opinion.sentiment])

            collection.add_vector(vector)

    return collection


def vectorize_test(news, entities, features):
    """ Vectorize news of test collection
    """
    def create_key(e1, e2):
        key = "{}_{}".format(
            env.stemmer.lemmatize_to_str(e1.value).encode('utf-8'),
            env.stemmer.lemmatize_to_str(e2.value).encode('utf-8')).decode('utf-8')
        assert(type(key) == unicode)
        return key

    collection = CommonRelationVectorCollection()

    r_entities = {}
    r_features = {}
    r_count = {}

    for e1 in entities:
        for e2 in entities:

            if e1.ID == e2.ID:
                continue

            if is_ignored(e1.value):
                continue

            if is_ignored(e2.value):
                continue

            s1 = news.get_sentence_by_entity(e1)
            s2 = news.get_sentence_by_entity(e2)

            # If entites from different sentences
            if not s1 == s2:
                continue

            r = Relation(e1.ID, e2.ID, news)
            r_key = create_key(e1, e2)
            features = np.concatenate([f.create(r) for f in FEATURES])

            # update features vector
            if r_key in r_features:
                r_features[r_key] += features
            else:
                r_features[r_key] = features

            # update count of such relations
            if r_key not in r_count:
                r_count[r_key] = 1
            else:
                r_count[r_key] += 1

            # set entity values
            if r_key not in r_entities:
                r_entities[r_key] = (e1.value, e2.value)

    for key, features in r_features.iteritems():
        left, right = r_entities[key]
        vector = CommonRelationVector(left, right, features/r_count[key])

        collection.add_vector(vector)

    return collection


#
# Main
#

root = "data/Texts/"
preps_filepath = "data/prepositions.txt"
rusentilex_filepath = "data/rusentilex.csv"
w2v_model_filepath = "../tone-classifier/data/w2v/news_rusvectores2.bin.gz"

# w2v_model = Word2Vec.load_word2vec_format(w2v_model_filepath, binary=True)
prefix_processor = SentimentPrefixProcessor.from_file("data/prefixes.csv")
prepositions_list = io_utils.read_prepositions(preps_filepath)

FEATURES = [
    DistanceFeature(),
    # SimilarityFeature(w2v_model),
    LexiconFeature(rusentilex_filepath, prefix_processor),
    PatternFeature([',']),
    EntitiesBetweenFeature(),
    PrepositionsCountFeature(prepositions_list),
    EntitiesFrequency()
]

#
# Train collection
#
root = io_utils.train_root()
for n in io_utils.train_indices():
    entity_filepath = root + "art{}.ann".format(n)
    opin_filepath = root + "art{}.opin.txt".format(n)
    neutral_filepath = root + "art{}.neut.txt".format(n)
    news_filepath = root + "art{}.txt".format(n)
    vector_output = root + "art{}.vectors.txt".format(n)

    print vector_output

    entities = EntityCollection.from_file(entity_filepath)
    news = News.from_file(news_filepath, entities)
    sentiment_opins = OpinionCollection.from_file(opin_filepath)
    neutral_opins = OpinionCollection.from_file(neutral_filepath)
    neutral_opins.limit(5)

    vectors = vectorize_train(
        news, entities, [sentiment_opins, neutral_opins], FEATURES)
    vectors.save(vector_output)

#
# Test collection
#
print 'test'
root = io_utils.test_root()
for n in io_utils.test_indices():
    entity_filepath = root + "art{}.ann".format(n)
    news_filepath = root + "art{}.txt".format(n)
    vector_output = root + "art{}.vectors.txt".format(n)

    print vector_output

    entities = EntityCollection.from_file(entity_filepath)
    news = News.from_file(news_filepath, entities)

    vectors = vectorize_test(news, entities, FEATURES)
    vectors.save(vector_output)
