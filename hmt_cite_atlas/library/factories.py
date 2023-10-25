import abc
import copy
from functools import cache

from .models import (
    Book,
    CITECollection,
    CITEDatum,
    CITEProperty,
    CTSCatalog,
    Datamodel,
    Relation,
    Scholion
)


MEMOIZED_BY_URN = {}


class AbstractFactory(abc.ABC):
    def get(self, **kwargs):
        key = kwargs["urn"]
        instance = MEMOIZED_BY_URN.get(key)
        if instance:
            return instance, False
        instance = self.model.objects.create(**kwargs)
        MEMOIZED_BY_URN[key] = instance
        return instance, True


class CITECollectionFactory(AbstractFactory):
    model = CITECollection


class CITEDatumFactory(AbstractFactory):
    model = CITEDatum


class CITEPropertyFactory(AbstractFactory):
    model = CITEProperty


class CTSCatalogFactory(AbstractFactory):
    model = CTSCatalog


class DatamodelFactory(AbstractFactory):
    model = Datamodel


class RelationFactory:
    model = Relation

    def get(self, **kwargs):
        new_kwargs = copy.deepcopy(kwargs)
        subject_obj = new_kwargs.pop("subject_obj")
        object_objs = new_kwargs.pop("object_obj")

        # Bail out due to unresolved URNs.
        objs = [subject_obj, *object_objs]
        if any(isinstance(obj, str) for obj in objs):
            return None, False

        instance = self.model.objects.create(**new_kwargs)

        subject_obj.subject_relations.add(instance)
        for obj in object_objs:
            obj.object_relations.add(instance)
        return instance, True


class IndexedAbstractFactory(abc.ABC):
    idx = 0
    position = 1

    def get(self, urn, **kwargs):
        key = urn
        instance = MEMOIZED_BY_URN.get(key)
        if instance:
            return instance

        instance = self.model.objects.create(
            urn=urn, **{"idx": self.idx, "position": self.position, **kwargs}
        )
        MEMOIZED_BY_URN[key] = instance
        self.idx += 1
        self.position += 1
        return instance


class BookFactory(IndexedAbstractFactory):
    model = Book


class ScholionFactory(IndexedAbstractFactory):
    model = Scholion
