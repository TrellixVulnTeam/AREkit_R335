import logging
from collections import OrderedDict
from arekit.contrib.bert.core.input.providers.label.binary import BinaryLabelProvider
from arekit.contrib.bert.core.input.providers.row_ids.binary import BinaryIDProvider
from arekit.common.experiment import const
from arekit.common.experiment.input.formatters.base_row import BaseRowsFormatter
from arekit.common.experiment.input.formatters.helper.balancing import SampleRowBalancerHelper
from arekit.common.experiment.input.providers.label.base import LabelProvider
from arekit.common.experiment.input.providers.label.multiple import MultipleLabelProvider
from arekit.common.experiment.input.providers.opinions import OpinionProvider
from arekit.common.experiment.input.providers.row_ids.multiple import MultipleIDProvider
from arekit.common.experiment.input.providers.text.single import BaseSingleTextProvider
from arekit.common.experiment.data_type import DataType
from arekit.common.labels.base import Label
from arekit.common.linked.text_opinions.wrapper import LinkedTextOpinionsWrapper
from arekit.common.news.parsed.base import ParsedNews
from arekit.common.news.parsed.term_position import TermPositionTypes
from arekit.common.text_opinions.base import TextOpinion

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BaseSampleFormatter(BaseRowsFormatter):
    """
    Custom Processor with the following fields

    [id, label, text_a] -- for train
    [id, text_a] -- for test
    """

    def __init__(self, data_type, label_provider, text_provider, balance):
        assert(isinstance(label_provider, LabelProvider))
        assert(isinstance(text_provider, BaseSingleTextProvider))
        assert(isinstance(balance, bool))

        self._label_provider = label_provider
        self.__text_provider = text_provider
        self.__row_ids_provider = self.__create_row_ids_provider(label_provider)
        self.__balance = balance

        super(BaseSampleFormatter, self).__init__(data_type=data_type)

    @staticmethod
    def formatter_type_log_name():
        return u"sample"

    # region Private methods

    @staticmethod
    def __create_row_ids_provider(label_provider):
        if isinstance(label_provider, BinaryLabelProvider):
            return BinaryIDProvider()
        if isinstance(label_provider, MultipleLabelProvider):
            return MultipleIDProvider()

    def __is_train(self):
        return self._data_type == DataType.Train

    def _get_columns_list_with_types(self):
        """
        Composing df with the following columns:
            [id, label, type, text_a]
        """
        dtypes_list = super(BaseSampleFormatter, self)._get_columns_list_with_types()

        dtypes_list.append((const.ID, unicode))

        # insert labels
        if self.__is_train():
            dtypes_list.append((const.LABEL, 'int32'))

        # insert text columns
        for col_name in self.__text_provider.iter_columns():
            dtypes_list.append((col_name, unicode))

        # insert indices
        dtypes_list.append((const.S_IND, 'int32'))
        dtypes_list.append((const.T_IND, 'int32'))

        return dtypes_list

    @staticmethod
    def __get_opinion_end_indices(parsed_news, text_opinion):
        assert(isinstance(parsed_news, ParsedNews))
        assert(isinstance(text_opinion, TextOpinion))

        s_ind = parsed_news.get_entity_position(text_opinion.SourceId).get_index(
            position_type=TermPositionTypes.IndexInSentence)

        t_ind = parsed_news.get_entity_position(text_opinion.TargetId).get_index(
            position_type=TermPositionTypes.IndexInSentence)

        return (s_ind, t_ind)

    @staticmethod
    def _iter_sentence_terms(parsed_news, sentence_ind):
        return parsed_news.iter_sentence_terms(sentence_index=sentence_ind, return_id=False)

    def _fill_row_core(self, row, opinion_provider, linked_wrap, index_in_linked, etalon_label,
                       parsed_news, sentence_ind, s_ind, t_ind):

        row[const.ID] = self.__row_ids_provider.create_sample_id(
            opinion_provider=opinion_provider,
            linked_opinions=linked_wrap,
            index_in_linked=index_in_linked,
            label_scaler=self._label_provider.LabelScaler)

        expected_label = linked_wrap.get_linked_label()

        if self.__is_train():
            row[const.LABEL] = self._label_provider.calculate_output_label(
                expected_label=expected_label,
                etalon_label=etalon_label)

        self.__text_provider.add_text_in_row(
            row=row,
            sentence_terms=list(self._iter_sentence_terms(parsed_news=parsed_news, sentence_ind=sentence_ind)),
            s_ind=s_ind,
            t_ind=t_ind,
            expected_label=expected_label)

        row[const.S_IND] = s_ind
        row[const.T_IND] = t_ind

    def __create_row(self, opinion_provider, linked_wrap, index_in_linked, etalon_label, idle_mode):
        """
        Composing row in following format:
            [id, label, type, text_a]

        returns: OrderedDict
            row with key values
        """
        assert(isinstance(opinion_provider, OpinionProvider))
        assert(isinstance(linked_wrap, LinkedTextOpinionsWrapper))
        assert(isinstance(index_in_linked, int))
        assert(isinstance(etalon_label, Label))
        assert(isinstance(idle_mode, bool))

        if idle_mode:
            return None

        text_opinion = linked_wrap[index_in_linked]

        parsed_news, sentence_ind = opinion_provider.get_opinion_location(text_opinion)
        s_ind, t_ind = self.__get_opinion_end_indices(parsed_news, text_opinion)

        row = OrderedDict()

        self._fill_row_core(row=row,
                            parsed_news=parsed_news,
                            sentence_ind=sentence_ind,
                            opinion_provider=opinion_provider,
                            linked_wrap=linked_wrap,
                            index_in_linked=index_in_linked,
                            etalon_label=etalon_label,
                            s_ind=s_ind,
                            t_ind=t_ind)
        return row

    def __provide_rows(self, opinion_provider, linked_wrap, index_in_linked, idle_mode):
        """
        Providing Rows depending on row_id_formatter type
        """
        assert(isinstance(linked_wrap, LinkedTextOpinionsWrapper))

        origin = linked_wrap.First
        if isinstance(self.__row_ids_provider, BinaryIDProvider):
            """
            Enumerate all opinions as if it would be with the different label types.
            """
            for label in self._label_provider.SupportedLabels:
                yield self.__create_row(opinion_provider=opinion_provider,
                                        linked_wrap=self.__copy_modified_linked_wrap(linked_wrap, label),
                                        index_in_linked=index_in_linked,
                                        etalon_label=origin.Sentiment,
                                        idle_mode=idle_mode)

        if isinstance(self.__row_ids_provider, MultipleIDProvider):
            yield self.__create_row(opinion_provider=opinion_provider,
                                    linked_wrap=linked_wrap,
                                    index_in_linked=index_in_linked,
                                    etalon_label=origin.Sentiment,
                                    idle_mode=idle_mode)

    @staticmethod
    def __copy_modified_linked_wrap(linked_wrap, label):
        assert(isinstance(linked_wrap, LinkedTextOpinionsWrapper))
        linked_opinions = [o for o in linked_wrap]

        copy = TextOpinion.create_copy(other=linked_opinions[0])
        copy.set_label(label=label)

        linked_opinions[0] = copy

        return LinkedTextOpinionsWrapper(linked_text_opinions=linked_opinions)

    def _iter_by_rows(self, opinion_provider, idle_mode):
        """
        Iterate by rows that is assumes to be added as samples, using opinion_provider information
        """
        assert(isinstance(opinion_provider, OpinionProvider))
        assert(isinstance(idle_mode, bool))

        linked_iter = opinion_provider.iter_linked_opinion_wrappers(
            balance=self.__balance,
            supported_labels=self._label_provider.SupportedLabels)

        for linked_wrap in linked_iter:

            for i in range(len(linked_wrap)):

                rows_it = self.__provide_rows(
                    opinion_provider=opinion_provider,
                    linked_wrap=linked_wrap,
                    index_in_linked=i,
                    idle_mode=idle_mode)

                for row in rows_it:
                    yield row

    # endregion

    def _create_blank_df(self, size):
        df = self._create_empty_df()
        self._fast_init_df(df=df, rows_count=size)
        return df

    def _fast_init_df(self, df, rows_count):
        df[self.ROW_ID] = range(rows_count)
        df.set_index(self.ROW_ID, inplace=True)

    def save(self, filepath, write_header):
        assert(isinstance(filepath, unicode))

        if self.__balance:
            logger.info(u"Start balancing...")
            SampleRowBalancerHelper.balance_oversampling(
                df=self._df,
                create_blank_df=lambda size: self._create_blank_df(size),
                label_provider=self._label_provider)
            logger.info(u"Balancing completed!")

        logger.info(u"Saving... : {}".format(filepath))
        self._df.to_csv(filepath,
                        sep='\t',
                        encoding='utf-8',
                        columns=[c for c in self._df.columns if c != self.ROW_ID],
                        index=False,
                        float_format="%.0f",
                        compression='gzip',
                        header=write_header)
        logger.info(u"Saving completed!")

    def __len__(self):
        return len(self._df.index)
