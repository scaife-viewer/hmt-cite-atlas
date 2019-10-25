import json
import os

from django.conf import settings

import stringcase

from . import constants
from .models import Library, Line, Version


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")
LIBRARY_METADATA_PATH = os.path.join(LIBRARY_DATA_PATH, "metadata.json")


class VersionFactory:
    model = Version

    def get(self, **kwargs):
        instance, _ = self.model.objects.get_or_create(**kwargs)
        return instance


class Importer:
    def __init__(self, full_content_path, library_obj):
        self.full_content_path = full_content_path
        self.library_obj = library_obj
        self.current_block = None
        # TODO: Temporary until CITE data import.
        self.use_blocks = ["#!ctscatalog", "#!ctsdata"]
        self.factory_lookup = {"version": VersionFactory()}
        self.model_lookup = {key: dict() for key in self.factory_lookup.keys()}
        self.fields = {}
        self.to_create = []

    @staticmethod
    def get_version_urn(urn):
        version_urn, _ = urn.rsplit(":", maxsplit=1)
        return version_urn

    @staticmethod
    def split_line(line):
        return line.split(constants.DELIMITER)

    @staticmethod
    def is_comment(line):
        return line.startswith(constants.COMMENT)

    @staticmethod
    def is_block_tag(line):
        return line in constants.BLOCKS

    def block_has_columns(self):
        return self.current_block != "#!ctsdata"

    def is_column_data(self, line):
        return self.split_line(line) in self.fields.values()

    def transform_fields(self, fields):
        return [stringcase.snakecase(field) for field in fields]

    def get_fields(self, urn=None):
        key = urn if urn else self.current_block
        return self.transform_fields(self.fields[key])

    def yield_data(self):
        with open(self.full_content_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line or self.is_comment(line):
                    continue

                block_tag = self.is_block_tag(line)
                if block_tag:
                    self.current_block = line
                    line_ref = 0
                    continue

                # TODO: Temporary until CITE data import.
                if self.current_block not in self.use_blocks:
                    continue

                if not block_tag and self.block_has_columns():
                    if not self.fields.get(self.current_block):
                        self.fields[self.current_block] = self.split_line(line)
                        continue

                if self.current_block == "#!ctscatalog":
                    if not self.is_column_data(line):
                        yield {"line": line}

                if self.current_block == "#!ctsdata":
                    line_ref += 1
                    line_idx = line_ref - 1
                    yield {"line_idx": line_idx, "line_ref": line_ref, "line": line}

    def handle_version(self, line, **data):
        fields = self.get_fields()
        values = [x if x else None for x in self.split_line(line)]
        version_kwargs = {
            "library": self.library_obj,
            **dict(zip(fields, values)),
        }

        # TODO: Stripping the trailing ":" on the URN but I think that needs to
        # be there, canonically speaking. Need to discuss overall policy.
        version_kwargs.update({"urn": version_kwargs["urn"][:-1]})
        version_kwargs.update({"online": bool(version_kwargs["online"])})
        if version_kwargs["citation_scheme"] is not None:
            version_kwargs.update(
                {"citation_scheme": version_kwargs["citation_scheme"].split(",")}
            )

        version_ref = version_kwargs["urn"]
        version_obj = self.model_lookup["version"].get(version_ref)
        if version_obj is None:
            version_obj = self.factory_lookup["version"].get(**version_kwargs)
            self.model_lookup["version"][version_ref] = version_obj

    def handle_line(self, line_idx, line_ref, line, **data):
        urn, tokens = self.split_line(line)
        version_ref = self.get_version_urn(urn)
        version_obj = self.model_lookup["version"][version_ref]
        line_kwargs = {
            "urn": urn,
            "text_content": tokens,
            "position": line_ref,
            "idx": line_idx,
            "version": version_obj,
            "library": self.library_obj,
        }
        self.to_create.append(Line(**line_kwargs))

    @property
    def handle(self):
        return {
            "#!cexversion": None,
            "#!citelibrary": None,
            "#!ctsdata": self.handle_line,
            "#!ctscatalog": self.handle_version,
            "#!citecollections": None,
            "#!citeproperties": None,
            "#!citedata": None,
            "#!imagedata": None,
            "#!relations": None,
            "#!datamodels": None,
        }[self.current_block]

    def apply(self):
        for data in self.yield_data():
            try:
                self.handle(**data)
            except TypeError:
                raise NotImplementedError(self.current_block)
        return self.to_create


def _import_library(data):
    full_content_path = os.path.join(LIBRARY_DATA_PATH, data["content_path"])
    library_obj, _ = Library.objects.update_or_create(
        urn=data["urn"],
        defaults=dict(
            name=data["metadata"]["library_title"], metadata=data["metadata"]
        ),
    )

    to_create = Importer(full_content_path, library_obj).apply()
    Line.objects.bulk_create(to_create)


def import_libraries(reset=True):
    if reset:
        Library.objects.all().delete()

    library_metadata = json.load(open(LIBRARY_METADATA_PATH))
    for library_data in library_metadata["libraries"]:
        _import_library(library_data)
