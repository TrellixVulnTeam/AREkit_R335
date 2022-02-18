from arekit.common.bound import Bound
from arekit.common.entities.base import Entity
from arekit.common.news.objects_parser import SentenceObjectsParserPipelineItem
from arekit.common.pipeline.context import PipelineContext
from arekit.common.text.partitioning.terms import TermsPartitioning
from arekit.processing.entities.bert_ontonotes import BertOntonotesNER
from arekit.processing.entities.obj_desc import NerObjectDescriptor


class BertOntonotesNERPipelineItem(SentenceObjectsParserPipelineItem):

    def __init__(self):
        # Initialize bert-based model instance.
        self.__ontonotes_ner = BertOntonotesNER()
        super(BertOntonotesNERPipelineItem, self).__init__(TermsPartitioning())

    def _get_parts_provider_func(self, pipeline_ctx):
        assert(isinstance(pipeline_ctx, PipelineContext))
        terms_list = self._get_text(pipeline_ctx)
        return self.__iter_subs_values_with_bounds(terms_list)

    def _get_text(self, pipeline_ctx):
        assert(isinstance(pipeline_ctx, PipelineContext))
        assert(self.SOURCE_KEY in pipeline_ctx)
        return pipeline_ctx.provide(self.SOURCE_KEY)

    def __iter_subs_values_with_bounds(self, terms_list):
        assert(isinstance(terms_list, list))

        single_sequence = [terms_list]
        processed_sequences = self.__ontonotes_ner.extract(sequences=single_sequence)

        for p_sequence in processed_sequences:
            for s_obj in p_sequence:
                assert(isinstance(s_obj, NerObjectDescriptor))
                value = " ".join(terms_list[s_obj.Position:s_obj.Position + s_obj.Length])
                entity = Entity(value=value, e_type=s_obj.ObjectType)
                yield entity, Bound(pos=s_obj.Position, length=s_obj.Length)
