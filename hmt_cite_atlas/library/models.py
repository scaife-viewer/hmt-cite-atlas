from django.contrib.postgres.fields import JSONField
from django.db import models


class Library(models.Model):
    """
    urn:cite2:hmt:publications.cex.2018e:all
    """

    urn = models.CharField(max_length=255, unique=True)
    name = models.CharField(blank=True, null=True, max_length=255)

    metadata = JSONField(encoder="", default=dict, blank=True)
    """
    {
        "library_urn": "",
        "library_title": "",
        "licence": "",
        "type": "library",
        "namespaces": ""
    }
    """

    class Meta:
        ordering = ["urn"]
        verbose_name_plural = "libraries"

    def __str__(self):
        return self.name


class Version(models.Model):
    """
    urn:cts:greekLit:tlg5026.msAext.va_dipl
    """

    urn = models.CharField(max_length=255, unique=True)
    citation_scheme = JSONField(encoder="", default=list, blank=True)
    group_name = models.CharField(blank=True, null=True, max_length=255)
    work_title = models.CharField(blank=True, null=True, max_length=255)
    version_label = models.CharField(blank=True, null=True, max_length=255)
    exemplar_label = models.CharField(blank=True, null=True, max_length=255)
    online = models.BooleanField(blank=True, null=True)
    lang = models.CharField(blank=True, null=True, max_length=255)

    library = models.ForeignKey(
        "library.Library", related_name="versions", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["urn"]

    @property
    def label(self):
        return f"{self.group_name}: {self.work_title}"

    def __str__(self):
        return f"{self.group_name}: {self.work_title}"


class Line(models.Model):
    """
    urn:cts:greekLit:tlg5026.msAext.va_dipl:1.135.comment
    """

    urn = models.CharField(max_length=255, unique=True)
    text_content = models.TextField()

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    version = models.ForeignKey(
        "library.Version", related_name="lines", on_delete=models.CASCADE
    )
    library = models.ForeignKey(
        "library.Library", related_name="lines", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["idx"]

    @property
    def label(self):
        return f"{self.position}"

    def __str__(self):
        return f"{self.version} [line={self.position}]"
