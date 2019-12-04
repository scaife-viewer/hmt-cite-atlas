from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page

from ..library.models import CITEDatum
from .shims import AlignmentsShim
from .utils import (
    WebAnnotationCollectionGenerator,
    WebAnnotationGenerator,
    as_zero_based
)


PAGE_SIZE = 10


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_wa(request, urn, idx, format):
    # @@@ query alignments from Postgres
    alignment_by_idx = None
    alignments = AlignmentsShim(urn).get_alignment_data()
    for alignment in alignments:
        if alignment["idx"] == idx:
            alignment_by_idx = alignment
            break
    if not alignment_by_idx:
        raise Http404

    wa = WebAnnotationGenerator(urn, alignment)
    if format == "text":
        return JsonResponse(data=wa.text_obj)
    elif format == "html":
        return JsonResponse(data=wa.html_obj)
    else:
        raise Http404


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_web_annotation_collection(request, urn, format):
    get_object_or_404(CITEDatum, **{"urn": urn})
    # @@@ query alignments from Postgres
    alignments = AlignmentsShim(urn).get_alignment_data(fields=["idx"])
    paginator = Paginator(alignments, per_page=PAGE_SIZE)
    data = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": reverse_lazy("serve_web_annotation_collection", args=[urn, format]),
        "type": "AnnotationCollection",
        "label": f"Translation Alignments for {urn}",
        "total": paginator.count,
        "first": reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, format, as_zero_based(paginator.page_range[0])],
        ),
        "last": reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, format, as_zero_based(paginator.page_range[-1])],
        ),
    }
    return JsonResponse(data)


@cache_page(settings.DEFAULT_HTTP_CACHE_DURATION)
def serve_web_annotation_page(request, urn, format, zero_page_number):
    get_object_or_404(CITEDatum, **{"urn": urn})

    # @@@ query alignments from Postgres
    alignments = AlignmentsShim(urn).get_alignment_data()

    page_number = zero_page_number + 1
    paginator = Paginator(alignments, per_page=PAGE_SIZE)
    try:
        page = paginator.page(page_number)
    except EmptyPage:
        raise Http404
    collection = WebAnnotationCollectionGenerator(urn, page.object_list, format)
    data = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": reverse_lazy(
            "serve_web_annotation_page", args=[urn, format, as_zero_based(page_number)]
        ),
        "type": "AnnotationPage",
        "partOf": reverse_lazy("serve_web_annotation_collection", args=[urn, format]),
        "startIndex": as_zero_based(page.start_index()),
        "items": collection.items,
    }
    if page.has_previous():
        data["prev"] = reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, format, as_zero_based(page.previous_page_number())],
        )
    if page.has_next():
        data["next"] = reverse_lazy(
            "serve_web_annotation_page",
            args=[urn, format, as_zero_based(page.next_page_number())],
        )
    return JsonResponse(data)
