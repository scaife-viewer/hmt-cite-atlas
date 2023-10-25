import abc
import copy
from functools import cache

from .models import (
    CITECollection,
    CITEDatum,
    CITEProperty,
    CTSCatalog,
    CTSDatum,
    Datamodel,
    Relation
)


MEMOIZED_BY_URN = {}


class AbstractFactory(abc.ABC):
    def get(self, **kwargs):
        key = kwargs["urn"]
        instance = MEMOIZED_BY_URN.get(key)
        if instance:
            return instance, False
        try:
            instance = self.model.objects.create(**kwargs)
        except:
            # urn:cts:greekLit:tlg0012.tlg001.msA.diplomatic:1.title|ἰλιάδος ἄλφα
            # looking for ctscatalog object urn:cts:greekLit:tlg0012.tlg001.msA.diplomatic:
            # e.g. in 2020h:
            # #!ctscatalog
            # urn#citationScheme#groupName#workTitle#versionLabel#exemplarLabel#online#lang
            # urn:cts:greekLit:tlg0012.tlg001.msA:#book,line#Homeric epic#Iliad#HMT project diplomatic edition##true#grc

            import ipdb; ipdb.set_trace()
            raise
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


class CTSDatumFactory(AbstractFactory):
    model = CTSDatum


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
