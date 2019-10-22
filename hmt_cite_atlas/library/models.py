from django.contrib.postgres.fields import JSONField
from django.db import models


class Library(models.Model):
    """
    urn:cite2:hmt:publications.cex.2018e:all
    """

    urn = models.CharField(max_length=255)
    name = models.CharField(blank=True, null=True, max_length=255)
    namespaces = JSONField(encoder="", default=dict, blank=True)

    metadata = JSONField(encoder="", default=dict, blank=True)
    """
    {
        "library_urn": "",
        "library_title": "",
        "licence": "",
        "type": "library"
    }
    """

    class Meta:
        ordering = ["urn"]
        verbose_name_plural = "libraries"

    def __str__(self):
        return self.name


class Version(models.Model):
    """
    """

    urn = models.CharField(max_length=255)
    name = models.CharField(blank=True, null=True, max_length=255)

    library = models.ForeignKey(
        "library.Library", related_name="versions", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["urn"]

    def __str__(self):
        return self.name


class Line(models.Model):
    """
    """

    urn = models.CharField(max_length=255)
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
