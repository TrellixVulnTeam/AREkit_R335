from arekit.common.experiment.input.terms_mapper import StringTextTermsMapper


class BertStringTextTermsMapper(StringTextTermsMapper):

    def map_text_frame_variant(self, fv_ind, text_frame_variant):
        raise NotImplementedError()
