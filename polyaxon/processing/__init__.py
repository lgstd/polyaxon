# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from polyaxon.processing.image import IMAGE_PROCESSORS
from .categorical import CategoricalVocabulary, CategoricalProcessor
from .data_decoders import (
    DataDecoder,
    TFExampleDecoder,
    SplitTokensDecoder,
    TFSequenceExampleDecoder
)
from .data_providers import Dataset, DataProvider, DatasetDataProvider, ParallelDatasetProvider
from . import image
from .input_data import create_input_data_fn
from .text import VocabularyProcessor
from . import pipelines


PROCESSORS = IMAGE_PROCESSORS
