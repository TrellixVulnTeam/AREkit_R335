from arekit.common.entities.base import Entity
from arekit.common.labels.provider.base import BasePairLabelProvider
from arekit.common.news.parsed.base import ParsedNews
from arekit.common.news.parsed.providers.base import BaseParsedNewsServiceProvider


class BasePairProvider(BaseParsedNewsServiceProvider):

    def __init__(self):
        self._entities = None

    @property
    def Name(self):
        raise NotImplementedError()

    def init_parsed_news(self, parsed_news):
        assert(isinstance(parsed_news, ParsedNews))
        self._entities = parsed_news.iter_entities()

    def _create_pair(self, source_entity, target_entity, label):
        raise NotImplementedError()

    # region private methods

    def _iter_from_entities(self, source_entities, target_entities, label_provider, filter_func=None):
        assert(isinstance(label_provider, BasePairLabelProvider))
        assert(callable(filter_func) or filter_func is None)

        for source_entity in source_entities:
            for target_entity in target_entities:
                assert(isinstance(source_entity, Entity))
                assert(isinstance(target_entity, Entity))

                if filter_func is not None and not filter_func:
                    continue

                if source_entity == target_entity:
                    continue

                label = label_provider.provide(source=source_entity,
                                               target=target_entity)

                yield self._create_pair(source_entity=source_entity,
                                        target_entity=target_entity,
                                        label=label)

    # endregion

    def iter_from_all(self, label_provider, filter_func):
        assert(isinstance(label_provider, BasePairLabelProvider))

        return self._iter_from_entities(source_entities=self._entities,
                                        target_entities=self._entities,
                                        label_provider=label_provider,
                                        filter_func=filter_func)
