from arekit.common.experiment.input.readers.base import BaseInputReader


class InputOpinionReader(BaseInputReader):

    def __init__(self, df):
        self.__df = df

    @classmethod
    def from_tsv(cls, experiment):
        pass
