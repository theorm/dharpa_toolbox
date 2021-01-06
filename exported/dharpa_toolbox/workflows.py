# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/05_workflows.ipynb (unless otherwise specified).

__all__ = ['DharpaWorkflow', 'modules_to_load', 'ALL_MODULE_CLASSES']

# Cell
import collections
import copy

from functools import partial
from typing import Set, Mapping
import typing
from .modules.core import DharpaModule, ModuleInputValues, ModuleOutputValues

from .utils import get_subclass_map, get_module_name_from_class
import networkx as nx

#export

modules_to_load = ["dharpa_toolbox.modules.core", "dharpa_toolbox.modules.files"]
ALL_MODULE_CLASSES = get_subclass_map(DharpaModule, preload_modules=modules_to_load, key_func=get_module_name_from_class)


class DharpaWorkflow(DharpaModule):

    def __init__(self, **config: typing.Any):

        self._module_details: Mapping[str, Mapping[str, typing.Any]] = {}

        self._execution_graph: nx.DiGraph = None
        self._dependency_graph: nx.DiGraph = None

        self._workflow_inputs: Mapping = None

        super().__init__(**config)

    def _input_updated(self, change) -> typing.Any:

        print(f"Input updated for workflow ({self.id}): {change}")

        if change.name not in self._input_staging.keys():
            self._input_staging[change.name] = {"old": change.old, "new": change.new}
        else:
            self._input_staging[change.name]["new"] = change.new

        module_obj, input_name = self._workflow_inputs[change.name]

        trait = module_obj.inputs.traits().get(input_name)
        trait.set(module_obj.inputs, change.new)

        self._check_stale()

    def _preprocess_config(self, **config: typing.Any):

        print("PREPROCESSING")

        modules = config.get("modules", None)
        if not modules:
            raise ValueError("Can't create workflow: no modules specified")

        missing_inputs = {}
        self._execution_graph = nx.DiGraph()

        no_modules_yet = len(self._module_details) == 0

        # TODO: re-use already existing modules
        self._module_details.clear()
        self._workflow_inputs = {}

        module_ids = set()

        for m in modules:

            module_type = m["type"]
            module_config = m.get("config", {})
            module_id = m.get("id", None)
            module_input_map = m.get("input_map", {})

            if isinstance(module_type, str):
                module_cls = ALL_MODULE_CLASSES.get(module_type)
            elif isinstance(module_type, type):
                module_cls = module_type
            else:
                raise TypeError(f"Invalid class for module type: {type(module_type)}")

            if module_id is None:
                if not no_modules_yet:
                    raise Exception(f"Module config without 'id' property not allowed after initial creation of workflow: {m}")
                module_obj = module_cls(**module_config)
                module_id = module_obj.id
                self._module_details[module_id] = {
                    "module": module_obj,
                }
                m["id"] = module_id
            elif module_id not in self._module_details.keys():
                if module_id in module_ids:
                    raise Exception(f"Duplicate module id: {module_id}")
                module_obj = module_cls(id=module_id, **module_config)
                self._module_details[module_id] = {
                    "module": module_obj,
                }
            else:
                if module_id in module_ids:
                    raise Exception(f"Duplicate module id: {module_id}")

                module_obj = self._module_details[module_id]["module"]
                module_obj.set_config(module_config)
                # TODO: remove current input map

            module_ids.add(module_id)

            full_input_map = {}
            for name in module_obj.inputs.trait_names():
                mapped_input = module_input_map.get(name, None)
                if not mapped_input:
                    output_name = f"{module_id}__{name}"
                    missing_inputs[output_name] = (module_id, name)
                    full_input_map[name] = ("__workflow__", output_name)
                    self._workflow_inputs[output_name] = (module_obj, name)
                else:
                    if isinstance(mapped_input, str):
                        mapped_input = (mapped_input, name)
                        full_input_map[name] = mapped_input
                    elif isinstance(mapped_input, collections.abc.Iterable) and len(mapped_input) == 2:
                        # TODO: check format of mapped_input
                        full_input_map[name] = tuple(*mapped_input)
                    else:
                        raise ValueError(f"Invalid value for input mapping: {mapped_input}")


            self._module_details[module_id]["input_map"] = full_input_map

            dep_modules = set()
            for d in full_input_map.values():
                dep_modules.add(d[0])

            if not dep_modules or (len(dep_modules) == 1 and "__workflow__" in dep_modules):
                self._execution_graph.add_edge("__workflow__", module_id)

            for d in dep_modules:
                if d != "__workflow__":
                    self._execution_graph.add_edge(d, module_id)

        self._dependency_graph = nx.DiGraph()

        for module_id, module_details in self._module_details.items():

            module_obj = module_details["module"]
            for inp in module_obj.inputs.trait_names():
                self._dependency_graph.add_edge(f"{module_id}.input '{inp}'", module_obj)
            for out in module_obj.outputs.trait_names():
                self._dependency_graph.add_edge(module_obj, f"{module_id}.output '{out}'")

            for input_name, connected_output in module_details["input_map"].items():
                if connected_output[0] == "__workflow__":
                    self._dependency_graph.add_edge("__user_input__", f"{module_id}.input '{input_name}'")
                else:
                    self._dependency_graph.add_edge(f"{connected_output[0]}.output '{connected_output[1]}", f"{module_id}.input '{input_name}'")

        return config

    def _process(self, **inputs) -> Mapping[str, typing.Any]:

        print("PROCESSING WORKFLOW WITH INPUTS")
        print(inputs)

    @property
    def execution_graph(self) -> nx.DiGraph:

        return self._execution_graph

    @property
    def dependency_graph(self) -> nx.DiGraph:

        return self._dependency_graph


    def _create_inputs(self, **config) -> ModuleInputValues:

        print("CREATE WORKFLOW INPUTS")

        class WorkflowModelInputValues(ModuleInputValues):
            pass

        # inputs = ModuleInputValues()
        inputs = WorkflowModelInputValues()

        traits = {}

        for name, module_input in self._workflow_inputs.items():

            m: DharpaModule = module_input[0]
            trait_name = module_input[1]
            trait = m.inputs.traits().get(trait_name)

            traits[name] = copy.deepcopy(trait)

        inputs.add_traits(**traits)

        return inputs

    def _output_udpated(self, output_name: str, change):

        print("OUTPUT_UPDATED")
        print(f"trait: {output_name}")
        print(change)

    def _create_outputs(self, **config) -> ModuleOutputValues:

        outputs = ModuleOutputValues()

        traits = {}

        for module_name, module in self.modules.items():

            for output_name in module.outputs.trait_names():
                trait = module.outputs.traits().get(output_name)
                output_trait_name = f"{module_name}__{output_name}"
                traits[output_trait_name] = copy.deepcopy(trait)
                update_func = partial(self._output_udpated, output_trait_name)
                module.outputs.observe(update_func, names=output_name)

        outputs.add_traits(**traits)
        return outputs

    @property
    def modules(self) -> typing.Mapping[str, DharpaModule]:
        return {m_name: m_details["module"] for m_name, m_details in self._module_details.items()}

    def get_module(self, id: str) -> DharpaModule:

        md = self._module_details.get(id, None)
        if md is None:
            raise Exception(f"No module '{id}' in workflow '{self.id}'.")

        return md["module"]

    @property
    def module_ids(self) -> typing.Iterable[str]:

        return self._module_details.keys()

    def _check_stale(self):

        for m in self._module_details.values():
            if m["module"].stale:
                self._state.stale = True
                return True

        self._state.stale = False
        return False

    def _module_input_updated(self, source_module: DharpaModule, source_input_name: str, change):

        # raise Exception(change)

        # print("-------------------")
        # print(f"MODULE INPUT UPDATED: {source_module}")
        # print(f"INPUT NAME: {source_input_name}")
        # # print(change)
        # # print(change.new)
        # print("-------------------")
        self._state.stale = True
        # deps = self.dependencies.get(source_module.id)
        # print(f"Dependencies: {self.dependencies.get(source_module.id)}")
        # for d in deps:
        #     dep_module = self.get_module(d)
        #     print(dep_module.input_mapping)

        # source_module.process()


    def _module_output_updated(self, source_module: DharpaModule, source_output_name: str, change):

        pass

    def execute(self):

        self.busy = True

        mg = self._module_execution_graph()
        print(mg)

        print("---")

        print(graph_to_ascii(mg))

        path_lengths = nx.single_source_shortest_path_length(mg, "__root__")

        max_length = max(path_lengths.values())

        modules_executed = set()

        modules_to_execute = None
        modules_next = None

        for i in range(1, max_length+1):

            modules_to_execute = [m for m, l in path_lengths.items() if l == i]

            print(f"Executing: {modules_to_execute}")

            modules_executed.update(modules_to_execute)

            for m in modules_to_execute:
                deps = self._dependencies.get(m)
                for d in deps:
                    if d in modules_executed:
                        raise Exception(f"Can't set dependency value from {m} to {d}: module {d} already executed")
                    print(f"ADDING INPUT FROM {m} TO {d}")

        print("Executing workflow")
        print("----------------")
        print("dependencies:")
        print(self._dependencies)
        print("----------------")
        print("dependencies reverse:")
        print(self._dependencies_reverse)

        print(self.modules)





        self._check_stale()
        self.busy = False


    # def add_module(self, module: DharpaModule):
    #
    #     if self._state.initialized:
    #         raise Exception(f"Can't add module '{module.id}': workflow already initialized")
    #     self.modules.append(module)
    #     self._state.stale = True
    #
    # def add_modules(self, *modules: DharpaModule):
    #
    #     for module in modules:
    #         self.add_module(module)
    #
    # def get_module(self, module_id: str) -> Optional[DharpaModule]:
    #
    #     result = None
    #     for m in self.modules:
    #         if m.id == module_id:
    #             result = m
    #             break
    #
    #     if result is None:
    #         raise Exception(f"Worfklow does not have module with id {module_id}.")
    #     return result

    @property
    def current_state(self):

        result = {"modules": {}}
        for module_id, module in self.modules.items():
            result["modules"][module_id] = module.current_state
        result["stale"] = self._state.stale
        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.id}' input_names={self.inputs.trait_names()} output_names={self.outputs.trait_names()}) modules={self.modules} config={self._config_raw}"

