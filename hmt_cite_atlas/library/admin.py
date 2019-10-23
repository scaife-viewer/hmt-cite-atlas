from django.contrib import admin

from .models import Library, Line, Version


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ("id", "urn", "name", "metadata")


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
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
        "library",
    )
    list_filter = ("library",)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "urn",
        "text_content",
        "position",
        "idx",
        "version",
        "library",
    )
    list_filter = ("version", "library")
