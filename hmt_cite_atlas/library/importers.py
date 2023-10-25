import json
import os
import re
import sys

from django.conf import settings

import case_conversion
import tqdm

from . import constants, factories, models


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")
LIBRARY_METADATA_PATH = os.path.join(LIBRARY_DATA_PATH, "metadata.json")

IGNORE_BLOCKS = ["#!cexversion", "#!citelibrary", "#!imagedata"]

RE_BOOK_RANGE = re.compile(r":[0-9]*$")

NODE_STRATEGY_NONE = 1
NODE_STRATEGY_ITER_KEYS = 2
NODE_STRATEGY_DSE = 3
NODE_STRATEGY = NODE_STRATEGY_DSE



def log(*objs):
    print(*objs, file=sys.stderr, sep="\n")


class Visitor:
    def __init__(self, index):
        self.keys = tuple(index.keys())
        self.index = index
        self.factory_lookup = {
            "#!citecollections": factories.CITECollectionFactory(),
            "#!citeproperties": factories.CITEPropertyFactory(),
            "#!citedata": factories.CITEDatumFactory(),
            "#!ctscatalog": factories.CTSCatalogFactory(),
            "#!ctsdata": factories.CTSDatumFactory(),
            "#!datamodels": factories.DatamodelFactory(),
            "#!relations": factories.RelationFactory(),
            "#!imagedata": None,
        }
        self.visited = 0
        self.problems = []

    @staticmethod
    def is_urn(value):
        try:
            return "urn:" in value
        except TypeError:
            return False

    def get_urn_position(self, field, urn, obj_kwargs):
        return next(idx for idx, item in enumerate(obj_kwargs[field]) if item == urn)

    def get_urn_permutation(self, urn):
        return next(
            key for key in self.index.keys() if isinstance(key, str) and urn in key
        )

    def get_node_data(self, urn, obj_kwargs):
        try:
            return self.index[urn]
        except KeyError:
            if NODE_STRATEGY == NODE_STRATEGY_NONE:
                return None
            elif NODE_STRATEGY == NODE_STRATEGY_ITER_KEYS:
                try:
                    return self.index[self.get_urn_permutation(urn)]
                except StopIteration:
                    return None
            elif NODE_STRATEGY == NODE_STRATEGY_DSE:
                lemma_urn = f"{urn}.lemma"
                permutation = self.index.get(lemma_urn)
                if permutation is None:
                    comment_urn = f"{urn}.comment"
                    permutation = self.index.get(comment_urn)
                if not permutation:
                    print(f"\t{urn}")
                return permutation

    def expand_book_lines(self, book, field):
        # We need to do some massaging here in case the object doesn't refer to
        # either a single line or a range of line but an entire 'book'.
        # Because, whatever those values might be they cannot be extracted from
        # the URN itself and we need to build them from the index.
        line_re = r":" + re.escape(book) + r".[0-9]+"
        for urn in self.index.keys():
            # Relation rows are keyed over their S-V-O triple (as a tuple) so
            # we can skip those immediately.
            if isinstance(urn, tuple):
                continue
            if re.search(line_re, urn):
                yield field, urn

    def filter_urn_nodes(self, obj_kwargs):
        for field, value in obj_kwargs.items():
            if field != "urn" and not self.is_urn(field):
                if isinstance(value, list):
                    for item in value:
                        if self.is_urn(item):
                            book_range = re.search(RE_BOOK_RANGE, item)
                            if book_range:
                                book = book_range.group()[1:]
                                yield from self.expand_book_lines(book, field)
                            else:
                                yield field, item

                elif self.is_urn(value):
                    yield field, value

    def resolve_related_node(self, urn, field, data, obj_kwargs):
        if isinstance(data, tuple):
            data = self.resolve_node(urn, data)
            if not data:
                return

        if isinstance(obj_kwargs[field], list):
            # We need to account for whether the list was pre-existing in its
            # entirety or if we are building it up dynamically as a book range.
            # In the first case, we can cleanly insert objects by their index.
            try:
                idx = self.get_urn_position(field, urn, obj_kwargs)
                obj_kwargs[field][idx] = data
            except StopIteration:
                # Book ranges will only ever have one value in them as we
                # didn't do any prior destructuring during the parse-stage.
                # So let's eliminate that value here first before accumulating
                # the objects in order.
                if isinstance(obj_kwargs[field][0], str):
                    obj_kwargs[field] = []
                obj_kwargs[field].append(data)
        else:
            obj_kwargs[field] = data

    def resolve_node(self, key, data):
        block, obj_kwargs = data
        for field, urn in self.filter_urn_nodes(obj_kwargs):
            data = self.get_node_data(urn, obj_kwargs)
            if not data:
                self.problems.append(
                    (f"URN (or permutations) not in index: {urn}", obj_kwargs)
                )
                continue
            self.resolve_related_node(urn, field, data, obj_kwargs)

        instance, created = self.factory_lookup[block].get(**obj_kwargs)
        if instance:
            if created:
                self.visited += 1
                self.index[key] = instance
            return instance

        self.problems.append(("Unable to instantiate obj:", obj_kwargs))
        return False

    def apply(self):
        print("Visitor.apply")
        for key in tqdm.tqdm(self.keys):
            data = self.index[key]
            if isinstance(data, tuple):
                self.resolve_node(key, data)
        return self.visited, self.problems


class Parser:
    def __init__(self, full_content_path, library_obj):
        self.full_content_path = full_content_path
        self.library_obj = library_obj
        self.current_block = None
        self.dynamic_columns = {}
        self.property_flags = {}
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

    def index_obj(self, obj_kwargs, key=None):
        self.index[key if key else obj_kwargs["urn"]] = (self.current_block, obj_kwargs)

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
        self.property_flags[urn] = {
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

        property_flags = {
            key: (value == urn)
            for key, value in self.property_flags.get(collection_urn, {}).items()
        }

        obj_kwargs.update(
            {
                "urn": urn,
                "property_type": obj_kwargs.pop("type"),
                "citecollection": collection_urn,
                **property_flags,
            }
        )
        self.index_obj(obj_kwargs)

    def handle_citedata(self, line, **data):
        urns = [item for item in self.split_line(line) if "urn:" in item]

        if not urns:
            return

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

    def handle_relations(self, line, **data):
        transform = {
            # "urn:cts:greekLit:tlg0012.tlg001.msA:4",
            # "urn:cts:greekLit:tlg0012.tlg001.msA:8",
            # "urn:cts:greekLit:tlg0012.tlg001.msA:9",
            # "urn:cts:greekLit:tlg0012.tlg001.msA:10",
            # "urn:cts:greekLit:tlg0012.tlg001.msA:11",
            # "urn:cts:greekLit:tlg0012.tlg001.msA:95",
            # "urn:cts:greekLit:tlg0012.tlg001.msA:311",
            "urn:cts:greekLit:tlg0012.tlg001.msA:18.604_605": "urn:cts:greekLit:tlg0012.tlg001.msA:18.603-18.604",
            "urn:cts:greekLit:tlg0012.tlg001.msA:18.603-18.604_605": "urn:cts:greekLit:tlg0012.tlg001.msA:18.604-18.605",
        }
        split = self.split_line(line)
        subject_urn, verb_urn, object_urn = self.split_line(line)

        if object_urn in transform:
            object_urn = transform[object_urn]

        # Verbs are usually defined in themselves as citedata nodes but that's
        # not the case for urn:cite2:hmt:verbs.v1:appearsIn. I think it is
        # supposed to be: urn:cite2:cite:verbs.v1:appearsIn, which is defined
        # but never used at all. So let's work around that.
        if verb_urn == "urn:cite2:hmt:verbs.v1:appearsIn":
            verb_urn = "urn:cite2:cite:verbs.v1:appearsIn"

        object_urn_stem, positions = object_urn.rsplit(":", maxsplit=1)

        object_at = None
        if "@" in positions:
            positions, object_at = positions.split("@")

        is_passage = False
        passage_range = positions.split("-")
        if len(passage_range) > 1:
            is_passage = True
            references = [reference.split(".") for reference in passage_range]
            # Detect and fix malformed passage URNs like:
            # urn:cts:greekLit:tlg0012.tlg001.msA:1.13-14
            # It should have the 'book' in each case:
            # urn:cts:greekLit:tlg0012.tlg001.msA:1.13-1.14
            try:
                assert all(len(reference) == 2 for reference in references)
            except AssertionError:
                first = references[0][0]
                fixed = []
                for reference in references:
                    if len(reference) == 1:
                        fixed.append([first, reference[0]])
                    else:
                        fixed.append(reference)
                assert all(len(reference) == 2 for reference in fixed)
                references = fixed

            book = set([reference[0] for reference in references])
            assert len(book) == 1
            book = book.pop()
            start, end = [int(reference[1]) for reference in references]
            passage = [
                f"{object_urn_stem}:{book}.{line}" for line in range(start, end + 1)
            ]

        obj_kwargs = {
            "subject_obj": subject_urn,
            "verb": verb_urn,
            "object_obj": [object_urn] if not is_passage else passage,
            "object_at": object_at,
            "citelibrary": self.library_obj,
        }
        self.index_obj(key=tuple(split), obj_kwargs=obj_kwargs)

    def handle_imagedata(self, line, **data):
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
        print("Parser.apply")
        for data in tqdm.tqdm(self.yield_data()):
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
    visited, problems = Visitor(index).apply()

    failed = len(problems)
    plural = f"object{'s' if failed > 1 else ''}"
    log(*(f"{urn}:\n{obj}" for urn, obj in problems))
    log(f"Visited {visited} {plural}.")
    log(f"Could not create {failed} {plural}.")


def import_libraries(reset=True):
    if reset:
        models.CITELibrary.objects.all().delete()

    library_metadata = json.load(open(LIBRARY_METADATA_PATH))
    for library_data in library_metadata["libraries"]:
        _import_library(library_data)
