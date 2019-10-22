from graphene import ObjectType, String, relay
from graphene.types import generic
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Library, Line, Version


class LibraryNode(DjangoObjectType):
    metadata = generic.GenericScalar()

    versions = DjangoFilterConnectionField(lambda: VersionNode)
    lines = DjangoFilterConnectionField(lambda: LineNode)

    class Meta:
        model = Library
        interfaces = (relay.Node,)
        filter_fields = ["name", "urn"]


class VersionNode(DjangoObjectType):
    metadata = generic.GenericScalar()

    lines = DjangoFilterConnectionField(lambda: LineNode)

    class Meta:
        model = Version
        interfaces = (relay.Node,)
        filter_fields = ["name", "urn", "library__urn"]


class LineNode(DjangoObjectType):
    label = String()

    class Meta:
        model = Line
        interfaces = (relay.Node,)
        filter_fields = [
            "text_content",
            "urn",
            "position",
            "version__urn",
            "library__urn",
        ]


class Query(ObjectType):
    library = relay.Node.Field(LibraryNode)
    libraries = DjangoFilterConnectionField(LibraryNode)

    version = relay.Node.Field(VersionNode)
    versions = DjangoFilterConnectionField(VersionNode)

    line = relay.Node.Field(LineNode)
    lines = DjangoFilterConnectionField(LineNode)
