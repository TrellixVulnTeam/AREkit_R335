import gc

import numpy as np
import pandas as pd

from arekit.common.data.input.providers.columns.base import BaseColumnsProvider
from arekit.common.data.storages.base import BaseRowsStorage, logger
from arekit.common.utils import progress_bar_iter


class PandasBasedRowsStorage(BaseRowsStorage):
    """ Storage Kernel functions implementation,
        based on the pandas DataFrames.
    """

    def __init__(self, df=None):
        assert(isinstance(df, pd.DataFrame) or df is None)
        self._df = df

    @property
    def DataFrame(self):
        # TODO. Temporary hack, however this should be removed in future.
        return self._df

    @staticmethod
    def __create_empty(cols_with_types):
        """ cols_with_types: list of pairs ("name", dtype)
        """
        assert(isinstance(cols_with_types, list))
        data = np.empty(0, dtype=np.dtype(cols_with_types))
        return pd.DataFrame(data)

    def __filter(self, column_name, value):
        return self._df[self._df[column_name] == value]

    @staticmethod
    def __iter_rows_core(df):
        assert(isinstance(df, pd.DataFrame))
        for row_index, row in df.iterrows():
            yield row_index, row

    def __fill_with_blank_rows(self, row_id_column_name, rows_count):
        assert(isinstance(row_id_column_name, str))
        assert(isinstance(rows_count, int))
        self._df[row_id_column_name] = list(range(rows_count))
        self._df.set_index(row_id_column_name, inplace=True)

    # region protected methods

    def _set_value(self, row_ind, column, value):
        self._df.at[row_ind, column] = value

    def _iter_rows(self):
        for row_index, row in self.__iter_rows_core(self._df):
            yield row_index, row

    def _get_rows_count(self):
        return len(self._df)

    ###################################################
    # TODO. #380 -- make this as a separate operation.
    ###################################################
    def _balance(self, column_name):
        """ Performs oversampled balancing.
        """
        assert (isinstance(self._df, pd.DataFrame))

        max_size = self._df[column_name].value_counts().max()

        dframes = [self._df]
        for class_index, group in self._df.groupby(column_name):
            dframes.append(group.sample(max_size - len(group), replace=True))

        # Clear resources
        self._df = pd.concat(dframes)
        for df in dframes:
            del df

        gc.collect()

    # endregion

    # region public methods

    def fill(self, iter_rows_func, columns_provider, rows_count=None, desc=""):
        """ NOTE: We provide the rows counting which is required
            in order to know an expected amount of rows in advace
            due to the specifics of the pandas memory allocation
            for the DataFrames.
            The latter allows us avoid rows appending, which
            may significantly affects on performance once the size
            of DataFrame becomes relatively large.
        """
        assert(isinstance(columns_provider, BaseColumnsProvider))

        logger.ino("Rows calculation process started. [Required by Pandas-Baased storage kernel]")
        logged_rows_it = progress_bar_iter(
            iterable=iter_rows_func(True),
            desc="Calculating rows count ({reason})".format(reason=desc),
            unit="rows")
        rows_count = sum(1 for _ in logged_rows_it)

        logger.info("Filling with blank rows: {}".format(rows_count))
        self.__fill_with_blank_rows(row_id_column_name=columns_provider.ROW_ID,
                                    rows_count=rows_count)
        logger.info("Completed!")

        super(PandasBasedRowsStorage, self).fill(iter_rows_func=iter_rows_func,
                                                 columns_provider=columns_provider,
                                                 rows_count=rows_count)

    def get_row(self, row_index):
        return self._df.iloc[row_index]

    def get_cell(self, row_index, column_name):
        return self._df.iloc[row_index][column_name]

    def iter_column_values(self, column_name, dtype=None):
        values = self._df[column_name]
        if dtype is None:
            return values
        return values.astype(dtype)

    def find_by_value(self, column_name, value):
        return self.__filter(column_name=column_name, value=value)

    def find_first_by_value(self, column_name, value):
        # TODO. Return new storage. (Encapsulation)
        rows = self.__filter(column_name=column_name, value=value)
        return rows.iloc[0]

    def init_empty(self, columns_provider):
        cols_with_types = columns_provider.get_columns_list_with_types()
        self._df = self.__create_empty(cols_with_types)

    def iter_shuffled(self):
        shuffled_df = self._df.sample(frac=1)
        return self.__iter_rows_core(shuffled_df)

    def free(self):
        del self._df
        super(PandasBasedRowsStorage, self).free()

    # endregion
