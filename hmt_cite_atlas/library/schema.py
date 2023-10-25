from graphene import ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Book, CITELibrary, CTSCatalog, Line, Scholion, Section


class LibraryNode(DjangoObjectType):
    metadata = generic.GenericScalar()
    catalogs = DjangoFilterConnectionField(lambda: CatalogNode)
    books = DjangoFilterConnectionField(lambda: BookNode)
    scholia = DjangoFilterConnectionField(lambda: ScholionNode)
    sections = DjangoFilterConnectionField(lambda: SectionNode)
    lines = DjangoFilterConnectionField(lambda: LineNode)

    class Meta:
        model = CITELibrary
        interfaces = (relay.Node,)
        filter_fields = ["name", "urn"]


class CatalogNode(DjangoObjectType):

    class Meta:
        model = CTSCatalog
        interfaces = (relay.Node,)
        filter_fields = ["urn", "citelibrary__urn"]


class BookNode(DjangoObjectType):
    label = String()

    scholia = DjangoFilterConnectionField(lambda: ScholionNode)
    sections = DjangoFilterConnectionField(lambda: SectionNode)
    lines = DjangoFilterConnectionField(lambda: LineNode)

    class Meta:
        model = Book
        interfaces = (relay.Node,)
        filter_fields = [
            "urn",
            "position",
            "ctscatalog__urn",
            "citelibrary__urn",
        ]


class ScholionNode(DjangoObjectType):
    label = String()

    sections = DjangoFilterConnectionField(lambda: SectionNode)

    class Meta:
        model = Scholion
        interfaces = (relay.Node,)
        filter_fields = [
            "urn",
            "position",
            "book__urn"
            "book__position",
            "ctscatalog__urn",
            "citelibrary__urn",
        ]


class SectionNode(DjangoObjectType):
    label = String()

    class Meta:
        model = Section
        interfaces = (relay.Node,)
        filter_fields = [
            "urn",
            "position",
            "text_content",
            "scholion__urn",
            "scholion__position",
            "book__urn",
            "book__position",
            "ctscatalog__urn",
            "citelibrary__urn",
        ]


class LineNode(DjangoObjectType):
    label = String()

    class Meta:
        model = Line
        interfaces = (relay.Node,)
        filter_fields = [
            "urn",
            "position",
            "text_content",
            "book__urn",
            "book__position",
            "ctscatalog__urn",
            "citelibrary__urn",
        ]


class Query(ObjectType):
    library = relay.Node.Field(LibraryNode)
    libraries = DjangoFilterConnectionField(LibraryNode)

    catalog = relay.Node.Field(CatalogNode)
    catalogs = DjangoFilterConnectionField(CatalogNode)

    book = relay.Node.Field(BookNode)
    books = DjangoFilterConnectionField(BookNode)

    scholion = relay.Node.Field(ScholionNode)
    scholia = DjangoFilterConnectionField(ScholionNode)

    section = relay.Node.Field(SectionNode)
    sections = DjangoFilterConnectionField(SectionNode)

    line = relay.Node.Field(LineNode)
    lines = DjangoFilterConnectionField(LineNode)
