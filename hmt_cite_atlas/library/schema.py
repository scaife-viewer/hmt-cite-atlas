from graphene import ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import (
    CITECollection,
    CITEDatum,
    CITELibrary,
    CITEProperty,
    CTSCatalog,
    CTSDatum,
    Datamodel,
    Relation
)


class CITELibraryNode(DjangoObjectType):
    metadata = generic.GenericScalar()
    citecollections = DjangoFilterConnectionField(lambda: CITECollectionNode)
    datamodels = DjangoFilterConnectionField(lambda: DatamodelNode)
    citeproperties = DjangoFilterConnectionField(lambda: CITEPropertyNode)
    citedata = DjangoFilterConnectionField(lambda: CITEDatumNode)
    ctscatalogs = DjangoFilterConnectionField(lambda: CTSCatalogNode)
    ctsdata = DjangoFilterConnectionField(lambda: CTSDatumNode)

    class Meta:
        model = CITELibrary
        interfaces = (relay.Node,)
        filter_fields = ["name", "urn"]


class CITECollectionNode(DjangoObjectType):
    citeproperties = DjangoFilterConnectionField(lambda: CITEPropertyNode)
    citedata = DjangoFilterConnectionField(lambda: CITEDatumNode)

    class Meta:
        model = CITECollection
        interfaces = (relay.Node,)
        filter_fields = ["urn", "citelibrary__urn"]


class DatamodelNode(DjangoObjectType):
    class Meta:
        model = Datamodel
        interfaces = (relay.Node,)
        filter_fields = ["urn", "citecollection__urn", "citelibrary__urn"]


class CITEPropertyNode(DjangoObjectType):
    authority_list = generic.GenericScalar()
    citedata = DjangoFilterConnectionField(lambda: CITEDatumNode)

    class Meta:
        model = CITEProperty
        interfaces = (relay.Node,)
        filter_fields = ["urn", "citecollection__urn", "citelibrary__urn"]


class CITEDatumNode(DjangoObjectType):
    label = String()
    fields = generic.GenericScalar()

    class Meta:
        model = CITEDatum
        interfaces = (relay.Node,)
        filter_fields = ["urn", "citecollection__urn", "citelibrary__urn"]


class CTSCatalogNode(DjangoObjectType):
    citation_scheme = generic.GenericScalar()
    ctsdata = DjangoFilterConnectionField(lambda: CTSDatumNode)

    class Meta:
        model = CTSCatalog
        interfaces = (relay.Node,)
        filter_fields = ["urn", "citelibrary__urn"]


class CTSDatumNode(DjangoObjectType):
    label = String()
    citation_scheme = generic.GenericScalar()

    class Meta:
        model = CTSDatum
        interfaces = (relay.Node,)
        filter_fields = [
            "urn",
            "text_content",
            "postition",
            "index",
            "ctscatalog__urn",
            "citelibrary__urn",
        ]


class RelationNode(DjangoObjectType):
    class Meta:
        model = Relation
        interfaces = (relay.Node,)
        filter_fields = ["urn", "citelibrary__urn"]


class Query(ObjectType):
    citelibrary = relay.Node.Field(CITELibraryNode)
    citelibraries = DjangoFilterConnectionField(CITELibraryNode)

    citecollection = relay.Node.Field(CITECollectionNode)
    citecollections = DjangoFilterConnectionField(CITECollectionNode)

    datamodel = relay.Node.Field(DatamodelNode)
    datamodels = DjangoFilterConnectionField(DatamodelNode)

    citeproperty = relay.Node.Field(CITEPropertyNode)
    citeproperties = DjangoFilterConnectionField(CITEPropertyNode)

    citedatum = relay.Node.Field(CITEDatumNode)
    citedata = DjangoFilterConnectionField(CITEDatumNode)

    ctscatalog = relay.Node.Field(CTSCatalogNode)
    ctscatalogs = DjangoFilterConnectionField(CTSCatalogNode)

    ctsdatum = relay.Node.Field(CTSDatumNode)
    ctsdata = DjangoFilterConnectionField(CTSDatumNode)

    relation = relay.Node.Field(RelationNode)
    relations = relay.Node.Field(RelationNode)
