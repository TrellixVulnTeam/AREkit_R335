#!/usr/bin/python2.7
import logging
import sys
import unittest
from tqdm import tqdm

sys.path.append('../../../../')

from arekit.common.opinions.base import Opinion
from arekit.common.entities.base import Entity
from arekit.common.utils import progress_bar_iter

from arekit.contrib.source.ruattitudes.synonyms_helper import RuAttitudesSynonymsCollectionHelper
from arekit.contrib.source.ruattitudes.news.helper import RuAttitudesNewsHelper
from arekit.contrib.source.ruattitudes.sentence.opinion import SentenceOpinion
from arekit.contrib.source.ruattitudes.io_utils import RuAttitudesVersions
from arekit.contrib.source.ruattitudes.collection import RuAttitudesCollection
from arekit.contrib.source.ruattitudes.news.base import RuAttitudesNews
from arekit.contrib.source.ruattitudes.news.parse_options import RuAttitudesParseOptions
from arekit.contrib.source.ruattitudes.sentence.base import RuAttitudesSentence

from arekit.processing.text.token import Token
from arekit.processing.lemmatization.mystem import MystemWrapper
from arekit.processing.text.parser import TextParser

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class TestRuAttitudes(unittest.TestCase):

    ra_version = RuAttitudesVersions.V20Large

    def test_indices(self):
        ids = set()
        for news in tqdm(RuAttitudesCollection.iter_news(version=self.ra_version,
                                                         get_news_index_func=lambda _: len(ids),
                                                         return_inds_only=False)):
            assert(isinstance(news, RuAttitudesNews))
            assert(news.ID not in ids)
            ids.add(news.ID)

    def test_synonyms_collection_reading(self):
        # Initializing stemmer
        stemmer = MystemWrapper()

        # Synonyms collection reading test
        return RuAttitudesSynonymsCollectionHelper.load_collection(stemmer=stemmer,
                                                                   version=TestRuAttitudes.ra_version)

    def test_parsing(self):
        # Initializing stemmer
        stemmer = MystemWrapper()

        options = RuAttitudesParseOptions(stemmer=stemmer,
                                          frame_variants_collection=None)

        # iterating through collection
        news_readed = 0

        news_it = RuAttitudesCollection.iter_news(version=self.ra_version,
                                                  get_news_index_func=lambda _: news_readed,
                                                  return_inds_only=False)

        for news in tqdm(news_it):

            # parse news
            parsed_news = TextParser.parse_news(news=news, parse_options=options)
            terms = parsed_news.iter_sentence_terms(sentence_index=0,
                                                    return_id=False)

            str_terms = []
            for t in terms:
                if isinstance(t, Entity):
                    str_terms.append(u"E")
                elif isinstance(t, Token):
                    str_terms.append(t.get_token_value())
                else:
                    str_terms.append(t)

            for t in str_terms:
                self.assertIsInstance(t, unicode)

            news_readed += 1

    def test_iter_news_inds(self):
        # iterating through collection
        news_ids_it = RuAttitudesCollection.iter_news(version=self.ra_version,
                                                      get_news_index_func=lambda ind: ind + 1,
                                                      return_inds_only=True)

        it = progress_bar_iter(iterable=news_ids_it,
                               desc=u"Extracting document ids",
                               unit=u"docs")

        print u"Total documents count: {}".format(max(it))

    def test_reading(self):

        # iterating through collection
        news_readed = 0
        news_it = RuAttitudesCollection.iter_news(version=self.ra_version,
                                                  get_news_index_func=lambda _: news_readed,
                                                  return_inds_only=False)
        for news in news_it:
            assert(isinstance(news, RuAttitudesNews))

            logger.debug(u"News: {}".format(news.ID))

            for sentence in news.iter_sentences(return_text=False):
                assert(isinstance(sentence, RuAttitudesSentence))
                # text
                logger.debug(sentence.Text.encode('utf-8'))
                # objects
                logger.debug(u",".join([object.Value for object in sentence.iter_objects()]))
                # attitudes
                for sentence_opin in sentence.iter_sentence_opins():
                    assert(isinstance(sentence_opin, SentenceOpinion))

                    source, target = sentence.get_objects(sentence_opin)
                    s = u"{src}->{target} ({label}) (t:[{src_type},{target_type}]) tag=[{tag}]".format(
                        src=source.Value,
                        target=target.Value,
                        label=str(sentence_opin.Sentiment.to_class_str()),
                        tag=sentence_opin.Tag,
                        src_type=source.Type,
                        target_type=target.Type).encode('utf-8')

                    logger.debug(sentence.SentenceIndex)
                    logger.debug(s)

                # Providing aggregated opinions.
                logger.info("Providing information for opinions with the related sentences:")
                for o, sentences in RuAttitudesNewsHelper.iter_opinions_with_related_sentences(news):
                    assert(isinstance(o, Opinion))
                    assert(isinstance(sentences, list))
                    logger.debug(u"'{source}'->'{target}' ({s_count})".format(
                        source=o.SourceValue,
                        target=o.TargetValue,
                        s_count=len(sentences)).encode('utf-8'))

            news_readed += 1


if __name__ == '__main__':
    unittest.main()
