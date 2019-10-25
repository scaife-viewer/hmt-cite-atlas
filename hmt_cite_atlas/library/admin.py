from django.contrib import admin

from .models import CITELibrary, CTSCatalog, CTSDatum


@admin.register(CITELibrary)
class CTSLibraryAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "name", "metadata")


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
