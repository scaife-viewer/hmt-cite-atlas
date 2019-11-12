import abc
import copy

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


class AbstractFactory(abc.ABC):
    def get(self, **kwargs):
        instance, created = self.model.objects.get_or_create(**kwargs)
        return instance, created


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
        instance, created = self.model.objects.get_or_create(
            urn=urn, **{"idx": self.idx, "position": self.position, **kwargs}
        )
        self.idx += 1
        self.position += 1
        return instance


class BookFactory(IndexedAbstractFactory):
    model = Book


class ScholionFactory(IndexedAbstractFactory):
    model = Scholion
