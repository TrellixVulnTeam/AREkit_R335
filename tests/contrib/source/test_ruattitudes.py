import logging
import sys
import unittest
from tqdm import tqdm


sys.path.append('../../../../')

from arekit.common.opinions.base import Opinion
from arekit.common.entities.base import Entity
from arekit.common.text.options import TextParseOptions
from arekit.common.utils import progress_bar_iter

from arekit.contrib.source.ruattitudes.text_object import TextObject
from arekit.contrib.source.ruattitudes.news.helper import RuAttitudesNewsHelper
from arekit.contrib.source.ruattitudes.sentence.opinion import SentenceOpinion
from arekit.contrib.source.ruattitudes.io_utils import RuAttitudesVersions
from arekit.contrib.source.ruattitudes.collection import RuAttitudesCollection
from arekit.contrib.source.ruattitudes.news.base import RuAttitudesNews
from arekit.contrib.source.ruattitudes.sentence.base import RuAttitudesSentence

from arekit.processing.text.token import Token
from arekit.processing.lemmatization.mystem import MystemWrapper
from arekit.processing.text.parser import DefaultTextParser

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class TestRuAttitudes(unittest.TestCase):

    __ra_versions = [
        RuAttitudesVersions.V12,
        RuAttitudesVersions.V20Base,
        RuAttitudesVersions.V20Large,
        RuAttitudesVersions.V20BaseNeut,
        RuAttitudesVersions.V20LargeNeut,
    ]

    # region private methods

    def __check_entities(self, news):
        for sentence in news.iter_sentences():
            assert (isinstance(sentence, RuAttitudesSentence))
            for s_obj in sentence.iter_objects():
                assert (isinstance(s_obj, TextObject))
                entity = s_obj.to_entity(lambda in_id: in_id)
                assert (isinstance(entity, Entity))
                self.assertTrue(entity.GroupIndex is not None,
                                "Group index [{doc_id}] is None!".format(doc_id=news.ID))

    def __iter_indices(self, ra_version):
        ids = set()
        for news in tqdm(RuAttitudesCollection.iter_news(version=ra_version,
                                                         get_news_index_func=lambda _: len(ids),
                                                         return_inds_only=False)):
            assert(isinstance(news, RuAttitudesNews))
            assert(news.ID not in ids)

            # Perform check for every entity.
            self.__check_entities(news)

            ids.add(news.ID)

    def __test_parsing(self, ra_version):
        # Initializing stemmer
        stemmer = MystemWrapper()
        parse_options = TextParseOptions(skip_entities=True,
                                         stemmer=stemmer,
                                         frame_variants_collection=None)
        text_parser = DefaultTextParser(parse_options)

        # iterating through collection
        news_read = 0

        news_it = RuAttitudesCollection.iter_news(version=ra_version,
                                                  get_news_index_func=lambda _: news_read,
                                                  return_inds_only=False)

        for news in tqdm(news_it):

            # parse news
            parsed_news = text_parser.parse_news(news=news)
            terms = parsed_news.iter_sentence_terms(sentence_index=0,
                                                    return_id=False)

            str_terms = []
            for t in terms:
                if isinstance(t, Entity):
                    str_terms.append("E")
                elif isinstance(t, Token):
                    str_terms.append(t.get_token_value())
                else:
                    str_terms.append(t)

            for t in str_terms:
                self.assertIsInstance(t, str)

            news_read += 1

    def __test_iter_news_inds(self, ra_version):
        # iterating through collection
        doc_ids_it = RuAttitudesCollection.iter_news(version=ra_version,
                                                     get_news_index_func=lambda ind: ind + 1,
                                                     return_inds_only=True)

        it = progress_bar_iter(iterable=doc_ids_it,
                               desc="Extracting document ids",
                               unit="docs")

        print("Total documents count: {}".format(max(it)))

    def __test_reading(self, ra_version, do_printing=True):

        # iterating through collection
        news_read = 0
        news_it = RuAttitudesCollection.iter_news(version=ra_version,
                                                  get_news_index_func=lambda _: news_read,
                                                  return_inds_only=False)

        if not do_printing:
            news_it = tqdm(news_it)

        for news in news_it:
            assert(isinstance(news, RuAttitudesNews))

            if not do_printing:
                continue

            logger.debug("News: {}".format(news.ID))

            for sentence in news.iter_sentences():
                assert(isinstance(sentence, RuAttitudesSentence))
                # text
                logger.debug(sentence.Text)
                # objects
                logger.debug(",".join([object.Value for object in sentence.iter_objects()]))
                # attitudes
                for sentence_opin in sentence.iter_sentence_opins():
                    assert(isinstance(sentence_opin, SentenceOpinion))

                    source, target = sentence.get_objects(sentence_opin)
                    s = "{src}->{target} ({label}) (t:[{src_type},{target_type}]) tag=[{tag}]".format(
                        src=source.Value,
                        target=target.Value,
                        label=str(sentence_opin.Sentiment.to_class_str()),
                        tag=sentence_opin.Tag,
                        src_type=str(source.Type),
                        target_type=str(target.Type))

                    logger.debug(sentence.SentenceIndex)
                    logger.debug(s)

                # Providing aggregated opinions.
                logger.info("Providing information for opinions with the related sentences:")
                for o, sentences in RuAttitudesNewsHelper.iter_opinions_with_related_sentences(news):
                    assert(isinstance(o, Opinion))
                    assert(isinstance(sentences, list))
                    logger.debug("'{source}'->'{target}' ({s_count})".format(
                        source=o.SourceValue,
                        target=o.TargetValue,
                        s_count=len(sentences)))

            news_read += 1

    # endregion

    def test_indices(self):
        self.__iter_indices(ra_version=self.__ra_versions[2])

    def test_parsing(self):
        self.__test_parsing(ra_version=self.__ra_versions[2])

    def test_iter_news_inds(self):
        self.__test_iter_news_inds(ra_version=self.__ra_versions[2])

    def test_reading(self):
        self.__test_reading(ra_version=self.__ra_versions[2])

    def test_quick_reading_of_all_version(self):
        for version in self.__ra_versions:
            print("Testing version: {version}".format(version=version))
            self.__test_reading(ra_version=version, do_printing=False)


if __name__ == '__main__':
    unittest.main()
