# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/03_data_sources.ipynb (unless otherwise specified).

__all__ = ['DataSource', 'WidgetSource', 'InputFilesWidget']

# Cell

from abc import ABCMeta, abstractmethod
from typing import Any
from ipywidgets import Widget, FileUpload
from traitlets import HasTraits
from ..modules.core import DharpaModule

class DataSource(metaclass=ABCMeta):

    def __init__(self, module: DharpaModule):

        self._connect_inputs(module.inputs)

    @abstractmethod
    def _connect_inputs(self, inputs: HasTraits) -> None:
        pass


class WidgetSource(DataSource):

    def __init__(self, module: DharpaModule):

        self._widget: Widget = None
        super().__init__(module)

    def _connect_inputs(self, inputs: HasTraits) -> None:

        self._widget = self._create_input_widget(inputs)

    @abstractmethod
    def _create_input_widget(self) -> Widget:
        pass


class InputFilesWidget(WidgetSource):

    def _create_input_widget(self, inputs: HasTraits) -> Widget:
        print("Creating widget")

        # uploaded_file_details = Output()
        file_upload = FileUpload(accept=".csv", multiple=False)

        def set_module_value(change):

            # inputs.files = list(change.new.values())
            inputs.files = change.new
            # file_upload.value.clear()
            file_upload._counter = 0


        file_upload.observe(set_module_value, names="value")
        return file_upload