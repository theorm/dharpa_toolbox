# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/10_modules_text.ipynb (unless otherwise specified).

__all__ = ['TextPreprocessSettingsModule', 'TextPreprocessingModule']

# Cell

# export
import collections

import typing
import traitlets
from traitlets import HasTraits, Dict, Any, Unicode, Integer, Bytes, Instance, Bool
from .core import DharpaModule
from .files import DharpaFiles


class TextPreprocessSettingsModule(DharpaModule):

    _module_name = "text_preprocess_settings"

    def _create_inputs(self, **config) -> HasTraits:

        class TextPreprocessingInput(HasTraits):
            file_set = Instance(klass=DharpaFiles, allow_none=True)
            lowercase = Bool(default_value=True)

        return TextPreprocessingInput()

    def _create_outputs(self, **config) -> HasTraits:

        class TextPreprocessingSettings(HasTraits):
            settings = Dict(allow_none=False)

        return TextPreprocessingSettings()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        return {"settings": {"lowercase": inputs["lowercase"]}}


class TextPreprocessingModule(DharpaModule):

    _module_name = "text_preprocessing"

    def _create_inputs(self, **config) -> HasTraits:

        class TextPreprocessingInput(HasTraits):
            file_set = Instance(klass=DharpaFiles, allow_none=True)
            settings = Dict(allow_none=False)

        return TextPreprocessingInput()

    def _create_outputs(self, **config):

        class TextPreprocessingOutput(HasTraits):
            preprocessed_text = Dict(allow_none=False)

        return TextPreprocessingOutput()

    def _process(self, **inputs) -> typing.Mapping[str, typing.Any]:

        result = {}
        file_set: DharpaFiles = inputs["file_set"]
        if file_set is None:
            file_set = DharpaFiles()

        for f in file_set.files:
            result[f.name] = f.content.lower()

        return result