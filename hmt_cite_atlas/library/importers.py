import json
import os
import sys

from django.conf import settings

import case_conversion

from . import constants, factories, models


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")
LIBRARY_METADATA_PATH = os.path.join(LIBRARY_DATA_PATH, "metadata.json")

IGNORE_BLOCKS = ["#!cexversion", "#!citelibrary", "#!imagedata", "#!relations"]


class Visitor:
    def __init__(self, index):
        self.index = index
        self.factory_lookup = {
            "#!citecollections": factories.CITECollectionFactory(),
            "#!citeproperties": factories.CITEPropertyFactory(),
            "#!citedata": factories.CITEDatumFactory(),
            "#!ctscatalog": factories.CTSCatalogFactory(),
            "#!ctsdata": factories.CTSDatumFactory(),
            "#!datamodels": factories.DatamodelFactory(),
            "#!imagedata": None,
            "#!relations": None,
        }
        self.visited = 0

    @staticmethod
    def is_urn(value):
        try:
            return "urn:" in value
        except TypeError:
            return False

    def filter_nodes(self, obj_kwargs):
        for key, value in obj_kwargs.items():
            if key != "urn" and not self.is_urn(key):
                if self.is_urn(value):
                    yield key, value

    def resolve_node(self, urn, block, obj_kwargs):
        for key, value in self.filter_nodes(obj_kwargs):
            related_urn = value
            data = self.index[related_urn]
            if not isinstance(data, tuple):
                obj_kwargs[key] = data
            else:
                related_block, related_obj_kwargs = data
                resolved = self.resolve_node(
                    related_urn, related_block, related_obj_kwargs
                )
                obj_kwargs[key] = resolved

        instance = self.factory_lookup[block].get(**obj_kwargs)
        self.visited += 1
        self.index[urn] = instance
        return instance

    def apply(self):
        for urn, data in self.index.items():
            if isinstance(data, tuple):
                block, obj_kwargs = data
                self.resolve_node(urn, block, obj_kwargs)
        return self.visited


class Parser:
    def __init__(self, full_content_path, library_obj):
        self.full_content_path = full_content_path
        self.library_obj = library_obj
        self.current_block = None
        self.dynamic_columns = {}
        self.merge_to_row = {}
        self.columns = {}
        self.index = {}

    @staticmethod
    def split_line(line):
        return line.split(constants.DELIMITER)

    @staticmethod
    def is_block_tag(line):
        return line in constants.BLOCKS

    @staticmethod
    def is_empty_line(line):
        return not line or line.startswith(constants.COMMENT)

    @staticmethod
    def normalize_column(column):
        return case_conversion.snakecase(column)

    @staticmethod
    def get_urn_root(urn, delimiter=":"):
        return f"{urn.rsplit(delimiter, maxsplit=1)[0]}:"

    def ignore_block(self):
        return self.current_block in IGNORE_BLOCKS

    def use_block_columns(self):
        return self.current_block not in ["#!ctsdata", "#!citedata"]

    def is_column_definition(self, line):
        columns = self.split_line(line)
        return (
            columns in self.columns.values() or columns in self.dynamic_columns.values()
        )

    def index_obj(self, obj_kwargs):
        self.index[obj_kwargs["urn"]] = (self.current_block, obj_kwargs)

    def map_columns_to_model_fields(self, urn=None):
        if urn:
            return self.columns[urn]
        columns = self.columns[self.current_block]
        return [self.normalize_column(column) for column in columns]

    def destructure_line(self, line, urn=None):
        model_fields = self.map_columns_to_model_fields(urn)
        values = []
        for value in self.split_line(line):
            if not value:
                values.append(None)
            else:
                if value in {"true", "false"}:
                    value = bool(value)
                values.append(value)
        return {"citelibrary": self.library_obj, **dict(zip(model_fields, values))}

    def yield_data(self):
        with open(self.full_content_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if self.is_empty_line(line):
                    continue

                block_tag = self.is_block_tag(line)
                if block_tag:
                    self.current_block = line
                    line_ref = 0
                    continue

                if self.ignore_block():
                    continue

                if not block_tag and self.use_block_columns():
                    if not self.columns.get(self.current_block):
                        self.columns[self.current_block] = self.split_line(line)
                        continue

                if self.current_block == "#!ctsdata":
                    line_ref += 1
                    line_idx = line_ref - 1
                    yield {"line_idx": line_idx, "line_ref": line_ref, "line": line}
                    continue

                if not self.is_column_definition(line):
                    yield {"line": line}

    def handle_ctscatalog(self, line, **data):
        obj_kwargs = self.destructure_line(line)
        if obj_kwargs["citation_scheme"] is not None:
            obj_kwargs.update(
                {"citation_scheme": obj_kwargs["citation_scheme"].split(",")}
            )
        self.index_obj(obj_kwargs)

    def handle_ctsdata(self, line_idx, line_ref, line, **data):
        urn, tokens = self.split_line(line)
        obj_kwargs = {
            "urn": urn,
            "text_content": tokens,
            "position": line_ref,
            "idx": line_idx,
            "ctscatalog": self.get_urn_root(urn),
            "citelibrary": self.library_obj,
        }
        self.index_obj(obj_kwargs)

    def handle_citecollections(self, line, **data):
        obj_kwargs = self.destructure_line(line)
        urn = obj_kwargs["urn"]
        self.merge_to_row[urn] = {
            "labelling_property": obj_kwargs.pop("labelling_property"),
            "ordering_property": obj_kwargs.pop("ordering_property"),
        }
        self.index_obj(obj_kwargs)

    def handle_citeproperties(self, line, **data):
        obj_kwargs = self.destructure_line(line)
        urn = obj_kwargs.pop("property")

        collection_urn, column = urn.rsplit(".", maxsplit=1)
        collection_urn = f"{collection_urn}:"
        column = column.rstrip(":")

        if not self.columns.get(collection_urn):
            self.columns[collection_urn] = []
        self.columns[collection_urn].append(urn)
        if not self.dynamic_columns.get(collection_urn):
            self.dynamic_columns[collection_urn] = []
        self.dynamic_columns[collection_urn].append(column)

        if obj_kwargs["authority_list"] is not None:
            obj_kwargs.update(
                {"authority_list": obj_kwargs["authority_list"].split(",")}
            )

        values_to_merge = {
            key: (value == urn)
            for key, value in self.merge_to_row.get(collection_urn, {}).items()
        }

        obj_kwargs.update(
            {
                "urn": urn,
                "property_type": obj_kwargs.pop("type"),
                "citecollection": collection_urn,
                **values_to_merge,
            }
        )
        self.index_obj(obj_kwargs)

    def handle_citedata(self, line, **data):
        urns = [item for item in self.split_line(line) if "urn:" in item]
        collection_urn = next(
            self.get_urn_root(urn)
            for urn in urns
            if self.get_urn_root(urn) in self.columns
        )
        urn = next(urn for urn in urns if collection_urn in urn)
        obj_kwargs = self.destructure_line(line, urn=collection_urn)
        transformed_kwargs = {
            "urn": urn,
            "citelibrary": obj_kwargs.pop("citelibrary"),
            "citecollection": collection_urn,
            "fields": obj_kwargs,
        }
        self.index_obj(transformed_kwargs)

    def handle_datamodels(self, line, **data):
        obj_kwargs = self.destructure_line(line)
        obj_kwargs.update(
            {
                "urn": obj_kwargs.pop("model"),
                "citecollection": obj_kwargs.pop("collection"),
            }
        )
        self.index_obj(obj_kwargs)

    def handle_imagedata(self, line, **data):
        raise NotImplementedError()

    def handle_relations(self, line, **data):
        raise NotImplementedError()

    @property
    def handle(self):
        return {
            "#!ctscatalog": self.handle_ctscatalog,
            "#!ctsdata": self.handle_ctsdata,
            "#!citecollections": self.handle_citecollections,
            "#!citeproperties": self.handle_citeproperties,
            "#!citedata": self.handle_citedata,
            "#!datamodels": self.handle_datamodels,
            "#!imagedata": self.handle_imagedata,
            "#!relations": self.handle_relations,
        }[self.current_block]

    def apply(self):
        for data in self.yield_data():
            self.handle(**data)
        return self.index


def _import_library(data):
    full_content_path = os.path.join(LIBRARY_DATA_PATH, data["content_path"])
    library_obj, _ = models.CITELibrary.objects.update_or_create(
        urn=data["urn"],
        defaults=dict(
            name=data["metadata"]["library_title"], metadata=data["metadata"]
        ),
    )

    index = Parser(full_content_path, library_obj).apply()
    visited = Visitor(index).apply()
    print(f"Created {visited} objects.", file=sys.stderr)


def import_libraries(reset=True):
    if reset:
        models.CITELibrary.objects.all().delete()

    library_metadata = json.load(open(LIBRARY_METADATA_PATH))
    for library_data in library_metadata["libraries"]:
        _import_library(library_data)
