from django.contrib import admin

from .models import (
    Book,
    CITECollection,
    CITEDatum,
    CITELibrary,
    CITEProperty,
    CTSCatalog,
    Datamodel,
    Line,
    Scholion,
    Section
)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "position", "idx")
    list_filter = ("ctscatalog", "citelibrary")


@admin.register(Scholion)
class ScholionAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "position", "idx")
    list_filter = ("book", "ctscatalog", "citelibrary")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "position", "idx", "text_content")
    list_filter = ("scholion", "book", "ctscatalog", "citelibrary")


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "position", "idx", "text_content")
    list_filter = ("book", "ctscatalog", "citelibrary")


@admin.register(CITELibrary)
class CITELibraryAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "name", "metadata")


@admin.register(CITECollection)
class CITECollectionAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "description", "license")
    list_filter = ("citelibrary",)


@admin.register(Datamodel)
class DatamodelAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "label", "description")
    list_filter = ("citecollection", "citelibrary")


@admin.register(CITEProperty)
class CITEPropertyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "urn",
        "label",
        "property_type",
        "authority_list",
        "labelling_property",
        "ordering_property",
    )
    list_filter = ("citecollection", "citelibrary")


@admin.register(CITEDatum)
class CITEDatumAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "fields")
    list_filter = ("citecollection", "citelibrary")


@admin.register(CTSCatalog)
class CTSCatalogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "urn",
        "work_title",
        "group_name",
        "citation_scheme",
        "version_label",
        "exemplar_label",
        "online",
        "lang",
        "citelibrary",
    )
    list_filter = ("citelibrary",)
