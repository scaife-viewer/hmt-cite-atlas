from django.contrib import admin

from .models import (
    CITECollection,
    CITEDatum,
    CITELibrary,
    CITEProperty,
    CTSCatalog,
    CTSDatum,
    Datamodel,
)


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


@admin.register(CTSDatum)
class CTSDatumAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "urn",
        "text_content",
        "position",
        "idx",
        "ctscatalog",
        "citelibrary",
    )
    list_filter = ("ctscatalog", "citelibrary")
