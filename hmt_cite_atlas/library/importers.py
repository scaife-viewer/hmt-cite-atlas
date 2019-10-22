import abc
import json
import os

from django.conf import settings

from .models import Library, Line, Version


LIBRARY_DATA_PATH = os.path.join(settings.PROJECT_ROOT, "data", "library")
LIBRARY_METADATA_PATH = os.path.join(LIBRARY_DATA_PATH, "metadata.json")


class AbstractFactory(abc.ABC):
    idx = 0
    position = 1

    @abc.abstractmethod
    def get(self, **kwargs):
        instance, _ = self.model.objects.get_or_create(
            **{"idx": self.idx, "position": self.position, **kwargs}
        )
        self.idx += 1
        self.position += 1
        return instance


class VersionFactory:
    model = Version

    def get(self, **kwargs):
        instance, _ = self.model.objects.get_or_create(**kwargs)
        return instance


class LineFactory(AbstractFactory):
    model = Line

    def get(self, **kwargs):
        return super().get(**kwargs)


def _import_library(data):
    library_obj, _ = Library.objects.update_or_create(
        urn=data["urn"],
        defaults=dict(
            name=data["metadata"]["library_title"], metadata=data["metadata"]
        ),
    )
    full_content_path = os.path.join(LIBRARY_DATA_PATH, data["content_path"])

    factory_lookup = {"line": LineFactory(), "version": VersionFactory()}
    model_lookup = {key: dict() for key in factory_lookup.keys()}
    to_create = []

    with open(full_content_path, "r", encoding="utf-8") as handle:
        raise NotImplementedError()


def import_libraries(reset=False):
    if reset:
        Library.objects.all().delete()

    library_metadata = json.load(open(LIBRARY_METADATA_PATH))
    for library_data in library_metadata["libraries"]:
        _import_library(library_data)
