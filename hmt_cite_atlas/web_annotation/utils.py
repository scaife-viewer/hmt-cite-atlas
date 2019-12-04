from django.db.models import Q
from django.utils.functional import cached_property

from ..iiif import IIIFResolver
from ..library.models import CITEDatum


def as_zero_based(int_val):
    """
    https://www.w3.org/TR/annotation-model/#model-35
    The relative position of the first Annotation in the items list, relative to the Annotation Collection. The first entry in the first page is considered to be entry 0.
    Each Page should have exactly 1 startIndex, and must not have more than 1. The value must be an xsd:nonNegativeInteger.

    JHU seems to be using zero-based pagination too, so we're matching that.
    """
    return int_val - 1


def map_dimensions_to_integers(dimensions):
    """
    FragmentSelector requires percentages expressed as integers.

    https://www.w3.org/TR/media-frags/#naming-space
    """
    int_dimensions = {}
    for k, v in dimensions.items():
        int_dimensions[k] = round(v)
    return int_dimensions


class WebAnnotationGenerator:
    def __init__(self, folio_urn, alignment):
        self.urn = folio_urn
        self.alignment = alignment
        self.idx = alignment["idx"]

    @cached_property
    def folio_image_urn(self):
        datum = CITEDatum.objects.get(urn=self.urn)
        return datum.fields["urn:cite2:hmt:msA.v1.image:"]

    @property
    def greek_lines(self):
        return self.alignment["items"][0]

    @property
    def english_lines(self):
        return self.alignment["items"][1]

    def as_text(self, lines):
        return "\n".join([f"{l[0]}) {l[1]}" for l in lines])

    def as_html(self, lines):
        # @@@ this could be rendered via Django if we need fancier HTML
        return "<ul>" + "".join([f"<li>{l[0]}) {l[1]}</li>" for l in lines]) + "</ul>"

    @property
    def alignment_urn(self):
        # @@@ what if we have multiple alignments covering a single line?
        # @@@ we can use the idx, but no too helpful downstream
        version_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:"
        return f'{version_urn}{self.alignment["citation"]}'

    def get_urn_coordinates(self, urns):
        # @@@ support a single URN
        predicate = Q()
        for urn in urns:
            predicate.add(
                Q(fields__contains={"urn:cite2:hmt:va_dse.v1.passage:": urn}), Q.OR
            )
        results = CITEDatum.objects.filter(predicate).order_by("pk")
        coordinates = []
        for result in results:
            if result.fields["urn:cite2:hmt:va_dse.v1.surface:"] != self.urn:
                # @@@ validates that the URNs are found within the current folio
                continue

            _, roi = result.fields["urn:cite2:hmt:va_dse.v1.imageroi:"].rsplit(
                "@", maxsplit=1
            )
            coords = [float(part) for part in roi.split(",")]
            coordinates.append(coords)
        return coordinates

    def get_bounding_box_dimensions(self, coords):
        dimensions = {}
        y_coords = []
        for x, y, w, h in coords:
            dimensions["x"] = min(dimensions.get("x", 100.0), x * 100)
            dimensions["y"] = min(dimensions.get("y", 100.0), y * 100)
            dimensions["w"] = max(dimensions.get("w", 0.0), w * 100)
            y_coords.append(y * 100)

        dimensions["h"] = y_coords[-1] - y_coords[0] + h * 100
        return dimensions

    @cached_property
    def common_obj(self):
        cite_version_urn = "urn:cts:greekLit:tlg0012.tlg001.msA:"
        urns = []
        # @@@ this is a giant hack, would be better to resolve the citation ref
        for ref, _, _ in self.greek_lines:
            urns.append(f"{cite_version_urn}{ref}")
        urn_coordinates = self.get_urn_coordinates(urns)
        precise_bb_dimensions = self.get_bounding_box_dimensions(urn_coordinates)
        bb_dimensions = map_dimensions_to_integers(precise_bb_dimensions)

        dimensions_str = ",".join(
            [
                str(bb_dimensions["x"]),
                str(bb_dimensions["y"]),
                str(bb_dimensions["w"]),
                str(bb_dimensions["h"]),
            ]
        )
        fragment_selector_val = f"xywh=percent:{dimensions_str}"

        image_urn = self.folio_image_urn
        iiif_obj = IIIFResolver(image_urn)
        image_api_selector_region = iiif_obj.get_region_by_pct(bb_dimensions)

        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "Annotation",
            "target": [
                self.alignment_urn,
                {
                    "type": "SpecificResource",
                    "source": {"id": f"{iiif_obj.canvas_url}", "type": "Canvas"},
                    "selector": {
                        "type": "FragmentSelector",
                        "region": fragment_selector_val,
                    },
                },
                {
                    "type": "SpecificResource",
                    "source": {"id": f"{iiif_obj.identifier}", "type": "Image"},
                    "selector": {
                        "type": "ImageApiSelector",
                        "region": image_api_selector_region,
                    },
                },
                iiif_obj.build_image_request_url(region=image_api_selector_region),
            ],
        }

    def get_textual_bodies(self, body_format):
        bodies = [
            {"type": "TextualBody", "language": "el"},
            {"type": "TextualBody", "language": "en"},
        ]
        if body_format == "text":
            for body, lines in zip(bodies, [self.greek_lines, self.english_lines]):
                body["format"] = "text/plain"
                body["value"] = self.as_text(lines)
        elif body_format == "html":
            for body, lines in zip(bodies, [self.greek_lines, self.english_lines]):
                body["format"] = "text/plain"
                body["value"] = self.as_html(lines)
        return bodies

    @property
    def text_obj(self):
        obj = {
            "body": self.get_textual_bodies("text"),
            "id": f"/wa/{self.urn}/translation-alignment/{self.idx}/text/",
        }
        obj.update(self.common_obj)
        return obj

    @property
    def html_obj(self):
        obj = {
            "body": self.get_textual_bodies("html"),
            "id": f"/wa/{self.urn}/translation-alignment/{self.idx}/html/",
        }
        obj.update(self.common_obj)
        return obj


class WebAnnotationCollectionGenerator:
    def __init__(self, urn, alignments, format):
        self.alignments = alignments
        self.format = format
        self.urn = urn
        self.item_list = []

    def append_to_item_list(self, data):
        # strip @context key
        data.pop("@context", None)
        self.item_list.append(data)

    @property
    def items(self):
        for alignment in self.alignments:
            wa = WebAnnotationGenerator(self.urn, alignment)
            if self.format == "html":
                self.append_to_item_list(wa.html_obj)
            elif self.format == "text":
                self.append_to_item_list(wa.text_obj)
        return self.item_list