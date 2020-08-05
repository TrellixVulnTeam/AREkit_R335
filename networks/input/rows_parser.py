import pandas as pd

from arekit.common.experiment import const
from arekit.common.experiment.scales.base import BaseLabelScaler
from arekit.common.utils import filter_whitespaces, split_by_whitespaces
import const as network_input_const

empty_list = []

parse_value = {
    const.ID: lambda value: value,
    const.S_IND: lambda value: value,
    const.T_IND: lambda value: value,
    network_input_const.FrameVariantIndices: lambda value:
        value.split(network_input_const.ArgsSep) if isinstance(value, unicode) else empty_list,
    network_input_const.FrameRoles: lambda value:
        value.split(network_input_const.ArgsSep) if isinstance(value, unicode) else empty_list,
    network_input_const.SynonymObject: lambda value: value.split(network_input_const.ArgsSep),
    network_input_const.SynonymSubject: lambda value: value.split(network_input_const.ArgsSep),
    "text_a": lambda value: filter_whitespaces([term for term in split_by_whitespaces(value)])
}


class ParsedSampleRow(object):
    """
    Provides a parsed information for a sample row.
    TODO. Use this class as API
    """

    def __init__(self, row, labels_scaler):
        assert(isinstance(row, pd.Series))
        assert(isinstance(labels_scaler, BaseLabelScaler))

        self.__sentiment = None
        self.__params = {}

        for key, value in row.iteritems():

            if key == const.LABEL:
                self.__sentiment = labels_scaler.uint_to_label(value)
                continue

            if key not in parse_value:
                continue

            self.__params[key] = parse_value[key](value)

    @property
    def SampleID(self):
        return self.__params[const.ID]
    
    @property
    def Terms(self):
        return self.__params["text_a"]

    @property
    def SubjectIndex(self):
        return self.__params[const.S_IND]

    @property
    def ObjectIndex(self):
        return self.__params[const.T_IND]

    @property
    def Sentiment(self):
        return self.__sentiment

    @property
    def TextFrameVariantIndices(self):
        return self.__params[network_input_const.FrameVariantIndices]

    @property
    def TextFrameVariantRoles(self):
        return self.__params[network_input_const.FrameRoles]

    @property
    def SynonymObjectInds(self):
        return self.__params[network_input_const.SynonymObject]

    @property
    def SynonymSubjectInds(self):
        return self.__params[network_input_const.SynonymSubject]

    @classmethod
    def parse(cls, row, labels_scaler):
        return cls(row=row, labels_scaler=labels_scaler)
