import csv
import json
import os
import re
from pathlib import Path

from django.db.models import Q

from hmt_cite_atlas.iiif import IIIFResolver
from hmt_cite_atlas.library.models import CITEDatum, CTSCatalog, CTSDatum


CITATION_SCHEME_SCHOLION = "scholion"


def get_scholion_for_dse_scholion(scholion_cite_datum):
    # FIXME: There might be a way we can use a subquery against the values in `urn:cite2:hmt:va_dse.v1.passage:`
    scholion_urns = [
        l.fields["urn:cite2:hmt:va_dse.v1.passage:"] for l in scholion_cite_datum
    ]
    scholion_urns = [f"{su}." for su in scholion_urns]
    predicate = Q()
    for su in scholion_urns:
        predicate.add(Q(urn__startswith=su), Q.OR)

    # prefer returning this data in position order
    datum = list(CTSDatum.objects.filter(predicate).order_by("position"))
    return datum


def extract_folios_range(urn):
    _, ref = urn.rsplit(":", maxsplit=1)
    pieces = ref.split("-")
    for pos, piece in enumerate(pieces):
        pieces[pos] = piece.split(".", maxsplit=1)[0]
    folio_datum_urn = "urn:cite2:hmt:msA.v1:"
    return [f"{folio_datum_urn}{piece}" for piece in pieces]


def get_folios_in_range(urns):
    first = CITEDatum.objects.get(urn=urns[0])
    last = CITEDatum.objects.get(urn=urns[1])
    folio_datum_urn = "urn:cite2:hmt:msA.v1:"
    # @@@ prefer idx
    return CITEDatum.objects.filter(
        urn__startswith=folio_datum_urn, id__gte=first.pk, id__lte=last.pk
    )


def folio_sort_key(ref):
    folio = ref.split(":").pop()
    folio_int = int(re.sub("\D", "", folio))
    recto_verso_part = 0 if folio.endswith("r") else 1
    return (folio_int, recto_verso_part)


def get_lines_for_folio(folio_urn):
    """
    get_lines_for_folio("urn:cite2:hmt:msA.v1:12r")
    """
    try:
        folio = CITEDatum.objects.get(urn=folio_urn)
    except CITEDatum.DoesNotExist as e:
        print(f'Could not resolve folio [urn="{folio_urn}""]')
        raise e

    # @@@ this will break in SQLite for the time being, but not in the future:
    # https://code.djangoproject.com/ticket/12990
    # https://github.com/laymonage/django-jsonfield-backport/pull/13
    # kwargs = {"fields__contains": {"urn:cite2:hmt:va_dse.v1.surface:": folio.urn}}
    kwargs = {f"fields__urn:cite2:hmt:va_dse.v1.surface:": folio.urn}
    folio_cite_datum = CITEDatum.objects.filter(**kwargs)

    # kwargs = {"citation_scheme__contains": [CITATION_SCHEME_SCHOLION]}
    # kwargs = {"citation_scheme": ["book", "line"]}
    kwargs = {"citation_scheme__icontains": CITATION_SCHEME_SCHOLION}
    catalog_obj = CTSCatalog.objects.exclude(**kwargs).get()
    version_urn = catalog_obj.urn

    # @@@ might be a way we can do some db-level "icontains" against `urn:cite2:hmt:va_dse.v1.passage:`
    line_cite_datum = folio_cite_datum.filter(fields__icontains=version_urn)
    # @@@ might be a way we can use a subquery against the values in `urn:cite2:hmt:va_dse.v1.passage:`
    line_urns = [l.fields["urn:cite2:hmt:va_dse.v1.passage:"] for l in line_cite_datum]
    return CTSDatum.objects.filter(urn__in=line_urns)


def get_dse_scholion_for_folio(folio_urn):
    """
    get_dse_scholion_for_folio("urn:cite2:hmt:msA.v1:12r")
    """
    try:
        folio = CITEDatum.objects.get(urn=folio_urn)
    except CITEDatum.DoesNotExist as e:
        print(f'Could not resolve folio [urn="{folio_urn}""]')
        raise e

    # @@@ this will break in SQLite for the time being, but not in the future:
    # https://code.djangoproject.com/ticket/12990
    # kwargs = {"fields__contains": {"urn:cite2:hmt:va_dse.v1.surface:": folio.urn}}
    kwargs = {f"fields__urn:cite2:hmt:va_dse.v1.surface:": folio.urn}
    return CITEDatum.objects.filter(**kwargs)


def munge_urn(version_urn, urn, folio_urn):
    if version_urn in urn:
        return urn
    version_part, ref = urn.rsplit(":", maxsplit=1)
    _, folio_ref = folio_urn.rsplit(":", maxsplit=1)
    return f"{version_urn}{folio_ref}.{ref}"


def extract_text_annotations(folio_urn, version_urn=None):
    if version_urn is None:
        version_urn = "urn:cts:greekLit:tlg0012.tlg001.msA"

    # e.g. urn:cite2:hmt:va_dse.v1:il4382
    dse_scholion = get_dse_scholion_for_folio(folio_urn)
    if not dse_scholion:
        raise IndexError

    # e.g. urn:cts:greekLit:tlg5026.msAint.hmt:7.3007.comment
    scholion = get_scholion_for_dse_scholion(dse_scholion)
    scholion_by_passage = {}
    for d in dse_scholion:
        key = d.fields["urn:cite2:hmt:va_dse.v1.passage:"]
        scholion_by_passage[key] = d

    text_annotations = {}
    for scholia in scholion:
        s = scholia
        simplified_urn, kind = s.urn.rsplit(".", maxsplit=1)
        data = text_annotations.setdefault(simplified_urn, {"urn": simplified_urn})
        data[kind] = s.text_content
        if "dse" not in data:
            d = scholion_by_passage[simplified_urn]
        data["dse"] = {
            "urn": d.urn,
            "image_roi": d.fields["urn:cite2:hmt:va_dse.v1.imageroi:"],
        }
        data.setdefault("references", [])
        if data["references"]:
            continue

        for sr in s.subject_relations.all():
            if sr.object_content_object:
                data["references"].append(
                    munge_urn(version_urn, sr.object_content_object.urn, folio_urn)
                )
            else:
                # TODO:
                pass
        # TODO: Add a flag to include / exclude comment only things like urn:cts:greekLit:tlg5026.msAint.hmt:1.32"

    return text_annotations


def extract_textual_annotations(outdir, version_part, version_urn, folio):
    try:
        annotations = extract_text_annotations(folio.urn, version_urn=version_urn)
    except IndexError:
        print(f"no annotations found for {folio.urn}")
        return

    urn, folio = folio.urn.rsplit(":", maxsplit=1)
    outf = outdir / f"text_annotations_{version_part}-{folio}.json"
    json.dump(
        list(annotations.values()),
        outf.open("w", encoding="utf-8"),
        indent=2,
        ensure_ascii=False,
    )


def do_textual_annotation_extraction(outdir):
    # TODO: Run this against a single folio via debug flag
    # NOTE: This passage covers _all_ folios
    passage = "urn:cts:greekLit:tlg0012.tlg001.msA-folios:12r.1.1-326v.24.804"
    version_urn, _ = passage.rsplit(":", maxsplit=1)
    pieces = [p for p in version_urn.rsplit(":") if p]
    version_part = pieces[-1]
    version_urn = f"{version_urn}:"

    urns = extract_folios_range(passage)
    folios = get_folios_in_range(urns)
    folio_urns = [f.urn for f in folios]

    folio_urns = sorted(folio_urns, key=folio_sort_key)

    for folio in folios:
        extract_textual_annotations(outdir, version_part, version_urn, folio)


# NOTE: These "munge" annotation scripts are used to populate our
# pseudo-version without the folios- prefix.
# These are currently not used
def munge_annotations(path):
    if not path.count("folios"):
        return

    new_path = path.replace("folios-", "")
    data = json.load(open(path))
    for row in data:
        new_references = []
        for reference in row.get("references", []):
            version, ref = reference.split("-folios")
            _, book, line = ref.split(".")
            new_references.append(f"{version}:{book}.{line}")
        row["references"] = new_references
    json.dump(data, open(new_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def munge_all(dir_path):
    paths = os.listdir(dir_path)
    for path in paths:
        munge_annotations(path)


def do_cex_folios_export(outdir):
    """
    Export an ATLAS compatible CEX file
    """
    folio_urns = CITEDatum.objects.filter(urn__startswith="urn:cite2:hmt:msA.v1:")
    lookup = {}
    for folio_urn in folio_urns:
        urn = folio_urn.urn
        lines = get_lines_for_folio(urn)
        if folio_urn in lookup:
            print(f"{urn}")
            lookup[urn].extend(lines)
        else:
            lookup[urn] = lines

    rows = []
    version_urn = "urn:cts:greekLit:tlg0012.tlg001.msA-folios"
    for folio_urn, lines in lookup.items():
        folio_label = folio_urn.rsplit(":", maxsplit=1)[1]
        for line in lines:
            ref = line.urn.rsplit(":", maxsplit=1)[1]
            rows.append(
                [line.idx, f"{version_urn}:{folio_label}.{ref}", line.text_content]
            )
    rows = sorted(rows)
    outf = outdir / "tlg0012.tlg001.msA-folios.cex"
    with outf.open("w", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="#")
        for row in rows:
            writer.writerow(row[1:])


def extract_image_annotation(folio, version_urn):
    folio_image_urn = folio.fields["urn:cite2:hmt:msA.v1.image:"]
    folio_image = CITEDatum.objects.get(urn=folio_image_urn)
    lines = get_lines_for_folio(folio.urn)
    urns = [l.urn for l in lines]
    predicate = Q()
    for urn in urns:
        predicate.add(
            # @@@ this will break in SQLite for the time being, but not in the future:
            # https://code.djangoproject.com/ticket/12990
            # https://github.com/laymonage/django-jsonfield-backport/pull/13
            # Q(fields__contains={"urn:cite2:hmt:va_dse.v1.passage:": urn}), Q.OR
            Q(**{"fields__urn:cite2:hmt:va_dse.v1.passage:": urn}),
            Q.OR,
        )
    # @@@ this could be other scholion too
    results = CITEDatum.objects.filter(predicate).order_by("pk")
    ref = folio.urn.rsplit(":", maxsplit=1)[1]

    iiif_obj = IIIFResolver(folio_image.urn)
    image_annotation = {
        "data": folio_image.fields,
        "urn": folio_image.fields["urn:cite2:hmt:vaimg.2017a.urn:"],
        "canvas_url": iiif_obj.canvas_url,
        "image_url": f"{iiif_obj.identifier}/",
        # @@@ this might be able to be expanded in the future
        "references": [f"{version_urn}{ref}"],
    }
    rois = []
    for result in results:
        passage_urn = result.fields["urn:cite2:hmt:va_dse.v1.passage:"]
        _, passage_ref = passage_urn.rsplit(":", maxsplit=1)
        rois.append(
            {
                "data": result.fields,
                "urn": result.fields["urn:cite2:hmt:va_dse.v1.urn:"],
                "references": [f"{version_urn}{ref}.{passage_ref}"],
            }
        )
    image_annotation["regions_of_interest"] = rois
    return image_annotation


def extract_image_annotations(outdir, version_urn, version_part, folio):
    try:
        annotation = extract_image_annotation(folio, version_urn)
    except KeyError:
        print(f"no passages were found for {folio.urn}")
        return

    urn, image_name = annotation["urn"].rsplit(":", maxsplit=1)
    outf = outdir / f"image_annotation_{version_part}-{image_name}.json"
    with outf.open("w", encoding="utf-8") as f:
        json.dump([annotation], f, indent=2, ensure_ascii=False)


def do_extract_image_annotations(outdir):
    passage = "urn:cts:greekLit:tlg0012.tlg001.msA-folios:12r.1.1-326v.24.804"
    version_urn, _ = passage.rsplit(":", maxsplit=1)
    pieces = [p for p in version_urn.rsplit(":") if p]
    version_part = pieces[-1]
    version_urn = f"{version_urn}:"
    urns = extract_folios_range(passage)
    folios = get_folios_in_range(urns)
    for folio in folios:
        extract_image_annotations(outdir, version_urn, version_part, folio)
        break


def main():
    outdir = Path("output")
    outdir.mkdir(exist_ok=True, parents=True)
    # NOTE: Only two folios have no annotations as of data/library/hmt-2020g.cex
    # no annotations found for urn:cite2:hmt:msA.v1:211v
    # no annotations found for urn:cite2:hmt:msA.v1:272v
    do_textual_annotation_extraction(outdir)
    # do_cex_folios_export(outdir)
    # do_extract_image_annotations(outdir)


if __name__ == "__main__":
    main()
