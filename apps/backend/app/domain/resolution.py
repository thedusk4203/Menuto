"""Typed failure at source-domain resolution boundaries, not validation authority."""


class ResolutionError(ValueError):
    def __init__(self, code, detail, *, rejected=False):
        super().__init__(detail)
        self.code, self.detail, self.rejected = code, detail, rejected
