import pandas as pd

from arekit.common.experiment.input.formatters.sample import BaseSampleFormatter
from arekit.common.experiment.input.providers.row_ids.base import BaseIDProvider
from arekit.common.experiment.input.readers.base import BaseInputReader


class InputSampleReader(BaseInputReader):

    ID = BaseSampleFormatter.ID

    def __init__(self, df, row_ids_provider):
        assert(isinstance(row_ids_provider, BaseIDProvider))
        super(InputSampleReader, self).__init__(df)
        self.__row_ids_provider = row_ids_provider

    @classmethod
    def from_tsv(cls, filepath, row_ids_provider):
        df = pd.read_csv(filepath,
                         compression='gzip',
                         sep='\t')

        return cls(df=df, row_ids_provider=row_ids_provider)

    def extract_ids(self):
        return self._df[self.ID].astype(unicode).tolist()

    def iter_rows_linked_by_text_opinions(self):
        """
        TODO. This might be improved, i.e. generalized.
        """
        undefined = -1

        linked = []

        current_news_id = undefined
        current_opinion_id = undefined

        for row_index, sample_id in enumerate(self._df[self.ID]):
            news_id = self.__row_ids_provider.parse_news_in_sample_id(sample_id)
            opinion_id = self.__row_ids_provider.parse_opinion_in_sample_id(sample_id)

            if current_news_id != undefined and current_opinion_id != undefined:
                if news_id != current_news_id or opinion_id != current_opinion_id:
                    yield linked
                    linked = []
                    continue

            linked.append(self._df.iloc[row_index])

