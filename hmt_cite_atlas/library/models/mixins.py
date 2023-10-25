from django.contrib.contenttypes.fields import GenericRelation
from django.db import models


class GenericRelationMixin(models.Model):
    subject_relations = GenericRelation(
        "library.Relation",
        content_type_field="subject_content_type",
        object_id_field="subject_id",
        related_query_name="subject_obj",
    )
    object_relations = GenericRelation(
        "library.Relation",
        content_type_field="object_content_type",
        object_id_field="object_id",
        related_query_name="object_obj",
    )

    class Meta:
        abstract = True
