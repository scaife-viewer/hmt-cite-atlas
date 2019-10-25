from django.contrib.postgres.fields import JSONField
from django.db import models


class CITELibrary(models.Model):
    """
    urn:cite2:hmt:publications.cex.2018e:all
    """

    urn = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    metadata = JSONField(encoder="", default=dict, blank=True)
    """
    {
        "cex_version": "",
        "library_urn": "",
        "library_title": "",
        "license": "",
        "type": "library",
        "namespaces": ""
    }
    """

    class Meta:
        ordering = ["urn"]
        verbose_name_plural = "citelibraries"

    def __str__(self):
        return self.name


class CITECollection(models.Model):
    """
    urn:cite2:hmt:msA.v1:
    """

    urn = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    license = models.CharField(max_length=255, blank=True, null=True)

    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="citecollections", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["urn"]

    def __str__(self):
        return self.urn

    @property
    def ordered_collection(self):
        return self.citeproperties.filter(ordering_property=True).exists()


class Datamodel(models.Model):
    """
    urn:cite2:cite:datamodels.v1:binaryimg
    """

    urn = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    citecollection = models.ForeignKey(
        "library.CITECollection", related_name="datamodels", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="datamodels", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["urn"]

    def __str__(self):
        return self.urn


class CITEProperty(models.Model):
    """
    urn:cite2:hmt:msA.v1.urn:
    """

    STRING = "String"
    CTSURN = "CtsUrn"
    CITE2URN = "Cite2Urn"
    NUMBER = "Number"
    BOOLEAN = "Boolean"
    PROPERTY_TYPE_CHOICES = (
        (STRING, "string"),
        (CTSURN, "ctsurn"),
        (CITE2URN, "cite2urn"),
        (NUMBER, "number"),
        (BOOLEAN, "boolean"),
    )
    urn = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=255, blank=True, null=True)
    property_type = models.CharField(max_length=8, choices=PROPERTY_TYPE_CHOICES)
    authority_list = JSONField(encoder="", default=list, blank=True, null=True)
    # TODO: These should always be unique per the data but it might be worth
    # enforcing some kind of key on them... Needs to be done in `save`.
    labelling_property = models.BooleanField()
    ordering_property = models.BooleanField()

    citecollection = models.ForeignKey(
        "library.CITECollection",
        related_name="citeproperties",
        on_delete=models.CASCADE,
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="citeproperties", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["urn"]
        verbose_name_plural = "citeproperties"

    def __str__(self):
        return self.urn


class CITEDatum(models.Model):
    """
    urn:cite2:hmt:msA.v1.sequence:
    """

    urn = models.CharField(max_length=255, unique=True)
    fields = JSONField(encoder="", default=dict, blank=True)

    citecollection = models.ForeignKey(
        "library.CITECollection", related_name="citedata", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="citedata", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["urn"]
        verbose_name_plural = "citedata"

    def __str__(self):
        if self.labelling_property:
            return self.fields[self.labelling_property.urn]
        return self.urn

    @property
    def schema(self):
        return {obj.urn: obj.property_type for obj in self.citeproperties}

    @property
    def citeproperties(self):
        return self.citecollection.citeproperties.filter(
            urn__in=self.fields.keys()
        ).order_by("pk")

    @property
    def labelling_property(self):
        qs = self.citeproperties.filter(labelling_property=True)
        return qs.first() if qs.exists() else None

    @property
    def ordering_property(self):
        qs = self.citeproperties.filter(ordering_property=True)
        return qs.first() if qs.exists() else None


class CTSCatalog(models.Model):
    """
    urn:cts:greekLit:tlg5026.msAext.va_dipl
    """

    urn = models.CharField(max_length=255, unique=True)
    citation_scheme = JSONField(encoder="", default=list, blank=True, null=True)
    group_name = models.CharField(max_length=255, blank=True, null=True)
    work_title = models.CharField(max_length=255, blank=True, null=True)
    version_label = models.CharField(max_length=255, blank=True, null=True)
    exemplar_label = models.CharField(max_length=255, blank=True, null=True)
    online = models.BooleanField()
    lang = models.CharField(max_length=255, blank=True, null=True)

    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="ctscatalogs", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["urn"]

    @property
    def label(self):
        return f"{self.group_name}: {self.work_title}"

    def __str__(self):
        return f"{self.group_name}: {self.work_title}"


class CTSDatum(models.Model):
    """
    urn:cts:greekLit:tlg5026.msAext.va_dipl:1.135.comment
    """

    urn = models.CharField(max_length=255, unique=True)
    text_content = models.TextField(blank=True, null=True)

    position = models.IntegerField()
    idx = models.IntegerField(help_text="0-based index")

    ctscatalog = models.ForeignKey(
        "library.CTSCatalog", related_name="ctsdata", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="ctsdata", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["idx"]
        verbose_name_plural = "ctsdata"

    @property
    def label(self):
        return f"{self.position}"

    def __str__(self):
        return f"{self.version} [line={self.position}]"
