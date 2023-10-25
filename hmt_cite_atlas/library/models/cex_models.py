from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django_jsonfield_backport.models import JSONField
from django.db import models

from .mixins import GenericRelationMixin


class CITELibrary(models.Model):
    """
    urn:cite2:hmt:publications.cex.2018e:all
    """

    urn = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    metadata = JSONField(default=dict, blank=True)
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
        verbose_name = "CITELibrary"
        verbose_name_plural = "CITElibraries"

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
        verbose_name = "CITECollection"
        verbose_name_plural = "CITECollections"
        ordering = ["urn"]

    def __str__(self):
        return self.urn

    @property
    def ordered_collection(self):
        return self.citeproperties.filter(ordering_property=True).exists()

    @property
    def labelling_property(self):
        qs = self.citeproperties.filter(labelling_property=True)
        return qs.first() if qs.exists() else None

    @property
    def ordering_property(self):
        qs = self.citeproperties.filter(ordering_property=True)
        return qs.first() if qs.exists() else None


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
    authority_list = JSONField(default=list, blank=True, null=True)
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
        verbose_name = "CITEProperty"
        verbose_name_plural = "CITEProperties"
        ordering = ["urn"]

    def __str__(self):
        return self.urn


class CITEDatum(GenericRelationMixin):
    """
    urn:cite2:hmt:msA.v1.sequence:
    """

    urn = models.CharField(max_length=255, unique=True)
    fields = JSONField(default=dict, blank=True)

    citecollection = models.ForeignKey(
        "library.CITECollection", related_name="citedata", on_delete=models.CASCADE
    )
    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="citedata", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "CITEDatum"
        verbose_name_plural = "CITEData"
        ordering = ["urn"]

    def __str__(self):
        return self.urn

    @property
    def label(self):
        return self.fields.get(self.label_by) or self.urn

    @property
    def schema(self):
        return {obj.urn: obj.property_type for obj in self.citeproperties}

    @property
    def citeproperties(self):
        return self.citecollection.citeproperties.filter(
            urn__in=self.fields.keys()
        ).order_by("pk")

    @property
    def label_by(self):
        if self.citecollection.labelling_property:
            return self.citecollection.labelling_property.urn
        return None


class CTSCatalog(models.Model):
    """
    urn:cts:greekLit:tlg5026.msAext.va_dipl
    """

    urn = models.CharField(max_length=255, unique=True)
    citation_scheme = JSONField(default=list, blank=True, null=True)
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
        verbose_name = "CTSCatalog"
        verbose_name_plural = "CTSCatalogs"
        ordering = ["urn"]

    def __str__(self):
        return self.urn


class Relation(models.Model):
    """
    A unique triple of URNs combining to create a S-V-O relationship.
    """

    subject_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="subject_relations",
        null=True,
        blank=True,
    )
    subject_id = models.PositiveIntegerField(null=True, blank=True)
    subject_content_object = GenericForeignKey("subject_content_type", "subject_id")
    verb = models.ForeignKey(
        "library.CITEDatum", related_name="relations", on_delete=models.CASCADE
    )
    object_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="object_relations",
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_content_object = GenericForeignKey("object_content_type", "object_id")
    object_at = models.CharField(max_length=255, null=True, blank=True)

    citelibrary = models.ForeignKey(
        "library.CITELibrary", related_name="relations", on_delete=models.CASCADE
    )

    def __str__(self):
        subject_obj = self.subject_content_object
        object_obj = self.object_content_object
        return f"{subject_obj} - {self.verb} - {object_obj}"
