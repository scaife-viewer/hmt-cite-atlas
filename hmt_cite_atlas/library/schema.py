from graphene import ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import CITELibrary, CTSCatalog, CTSDatum


class CITELibraryNode(DjangoObjectType):
    metadata = generic.GenericScalar()
    ctscatalogs = DjangoFilterConnectionField(lambda: CTSCatalogNode)
    ctsdata = DjangoFilterConnectionField(lambda: CTSDatumNode)

    class Meta:
        model = CITELibrary
        interfaces = (relay.Node,)
        filter_fields = ["name", "urn"]


class CTSCatalogNode(DjangoObjectType):
    label = String()
    ctsdata = DjangoFilterConnectionField(lambda: CTSDatumNode)

    class Meta:
        model = CTSCatalog
        interfaces = (relay.Node,)
        filter_fields = [
            "urn",
            # "citation_scheme",  # TODO: Is a JSONField, punt for now.
            "group_name",
            "work_title",
            "version_label",
            "exemplar_label",
            "online",
            "lang",
            "library__urn",
        ]


class CTSDatumNode(DjangoObjectType):
    label = String()

    class Meta:
        model = CTSDatum
        interfaces = (relay.Node,)
        filter_fields = [
            "text_content",
            "urn",
            "position",
            "version__urn",
            "library__urn",
        ]


class Query(ObjectType):
    citelibrary = relay.Node.Field(CITELibraryNode)
    citelibraries = DjangoFilterConnectionField(CITELibraryNode)

    ctscatalog = relay.Node.Field(CTSCatalogNode)
    ctscatalogs = DjangoFilterConnectionField(CTSCatalogNode)

    ctsdatum = relay.Node.Field(CTSDatumNode)
    ctsdata = DjangoFilterConnectionField(CTSDatumNode)
