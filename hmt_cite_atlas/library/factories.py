import abc

from .models import (
    CITECollection,
    CITEDatum,
    CITEProperty,
    CTSCatalog,
    CTSDatum,
    Datamodel,
)


class AbstractFactory(abc.ABC):
    def get(self, **kwargs):
        instance, _ = self.model.objects.get_or_create(**kwargs)
        return instance


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
