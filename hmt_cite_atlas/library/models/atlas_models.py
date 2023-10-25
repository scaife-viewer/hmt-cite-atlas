from django.db import models

from .mixins import GenericRelationMixin


class Book(GenericRelationMixin):
    """
    urn:cts:greekLit:tlg5026.msA.va_dipl:1

    Text and scholia container model.
    """

    urn = models.CharField(max_length=255, unique=True)

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    ctscatalog = models.ForeignKey(
        "library.CTSCatalog", related_name="books", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="books", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["idx"]

    @property
    def label(self):
        return f"{self.ctscatalog}:{self.position}"

    def __str__(self):
        return f"{self.ctscatalog} [book={self.position}]"


class Scholion(models.Model):
    """
    urn:cts:greekLit:tlg5026.msA.va_dipl:1.1

    Scholia container model.
    """

    urn = models.CharField(max_length=255, unique=True)

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    book = models.ForeignKey(
        "library.Book", related_name="scholia", on_delete=models.CASCADE
    )
    ctscatalog = models.ForeignKey(
        "library.CTSCatalog", related_name="scholia", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="scholia", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "Scholia"
        ordering = ["idx"]

    @property
    def label(self):
        return f"{self.ctscatalog}:{self.book}:{self.position}"

    def __str__(self):
        return f"{self.ctscatalog} [scholia={self.position}]"


class Section(GenericRelationMixin):
    """
    urn:cts:greekLit:tlg5026.msA.va_dipl:1.1.lemma

    Scholia leaf model.
    """

    urn = models.CharField(max_length=255, unique=True)
    text_content = models.TextField(blank=True, null=True)

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    scholion = models.ForeignKey(
        "library.Scholion", related_name="sections", on_delete=models.CASCADE
    )
    book = models.ForeignKey(
        "library.Book", related_name="sections", on_delete=models.CASCADE
    )
    ctscatalog = models.ForeignKey(
        "library.CTSCatalog", related_name="sections", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="sections", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["idx"]

    @property
    def label(self):
        return f"{self.ctscatalog}:{self.book}:{self.scholion}:{self.position}"

    def __str__(self):
        return f"{self.ctscatalog} [section={self.position}]"


class Line(GenericRelationMixin):
    """
    urn:cts:greekLit:tlg0012.tlg001.msA:1.1

    Text leaf model.
    """

    urn = models.CharField(max_length=255, unique=True)
    text_content = models.TextField(blank=True, null=True)

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    book = models.ForeignKey(
        "library.Book", related_name="lines", on_delete=models.CASCADE
    )
    ctscatalog = models.ForeignKey(
        "library.CTSCatalog", related_name="lines", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="lines", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["idx"]

    @property
    def label(self):
        return f"{self.ctscatalog}:{self.book}:{self.position}"

    def __str__(self):
        return f"{self.ctscatalog} [line={self.position}]"
