#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import numpy as np
from gensim.models.word2vec import Word2Vec

from core.processing.stemmer import Stemmer
from core.source.entity import EntityCollection
from core.source.news import News
from core.source.opinion import OpinionCollection

IGNORED_ENTITIES = ["Author", "Unknown"]


# distance between two entities counted in sentences.
def sentences_between(e1, e2, news):

    if e1.value in IGNORED_ENTITIES or e2.value in IGNORED_ENTITIES:
        return -2

    if e1.ID == e2.ID:
        return -1

    s1_ind = None
    s2_ind = None
    for i, s in enumerate(news.sentences):
        if s.has_entity(e1.ID):
            s1_ind = i
            break

    for i, s in enumerate(news.sentences):
        if s.has_entity(e2.ID):
            s2_ind = i
            break

    return abs(s1_ind - s2_ind)


def relations_equal_diff(E, diff, news, opinions, w2v_model):

    def make_relation(e1, e2, mystem):
        return "{}_{}".format(mystem.lemmatize(e1), mystem.lemmatize(e2))

    def rus_vectores_lemmatize(e, mystem):
        """
        term presented as follows  <lemma>_<POS tag> based on 'mystem'
        """
        result = []
        analysis = mystem.analyze(e)

        for item in analysis:

            if len(item['analysis']) == 0:
                continue

            a = item['analysis'][0]
            lex = a['lex']
            pos = a['gr'].split(',')[0]

            result.append("%s_%s" % (lex, pos))

        return result

    def get_word2vec_vector(lemmas, w2v_model):
        v = np.zeros(w2v_model.vector_size, dtype=np.float32)
        for l in lemmas:
            if l in w2v_model:
                v = v + w2v_model[l]
        return v

    def rus_vectores_similarity(e1, e2, mystem, w2v_model):
        l1 = rus_vectores_lemmatize(e1, mystem)
        l2 = rus_vectores_lemmatize(e2, mystem)
        v1 = get_word2vec_vector(l1, w2v_model)
        v2 = get_word2vec_vector(l2, w2v_model)
        return sum(map(lambda x, y: x * y, v1, v2))

    count = 0
    mystem = Stemmer().mystem
    unique_relations = []
    entities = news.entities

    for i in range(E.shape[0]):
        for j in range(E.shape[1]):

            e1 = entities.get(i)
            e2 = entities.get(j)
            r = make_relation(e1.value, e2.value, mystem)
            d = min(abs(e1.end - e2.begin), abs(e2.end - e1.begin))

            if (e1.value in IGNORED_ENTITIES or e2.value in IGNORED_ENTITIES):
                continue

            if r in unique_relations:
                continue

            if E[i][j] == diff:
                s = opinions.has_opinion(e1.value, e2.value, lemmatize=True)

                # Filter sentiment relations
                # if s:
                #     continue

                cos = rus_vectores_similarity(e1.value, e2.value, mystem, w2v_model)

                logging.info("{} -> {}, d: {}, s: {}, cos: {}".format(
                    e1.value.encode('utf-8'), e2.value.encode('utf-8'),
                    d, s, cos))

                unique_relations.append(r)
                count += 1

    return count


i = 1
w2v_model_filepath = "../tone-classifier/data/w2v/news_rusvectores2.bin.gz"
entity_filepath = "data/Texts/art{}.ann".format(i)
news_filepath = 'data/Texts/art{}.txt'.format(i)
opin_filepath = 'data/Texts/art{}.opin.txt'.format(i)

logging.basicConfig(filemode='w',
                    format="",
                    level=logging.DEBUG,
                    filename="out.txt")

entities = EntityCollection.from_file(entity_filepath)
news = News.from_file(news_filepath, entities)
opinions = OpinionCollection.from_file(opin_filepath)

E = np.zeros((entities.count(), entities.count()), dtype='int32')

for e1 in entities:
    for e2 in entities:
        i = e1.get_int_ID()
        j = e2.get_int_ID()
        E[i-1][j-1] = sentences_between(e1, e2, news)

w2v_model = Word2Vec.load_word2vec_format(w2v_model_filepath, binary=True)

for diff in range(1):
    logging.info("d: {}, r: {}".format(
        diff, relations_equal_diff(E, diff, news, opinions, w2v_model)))
