from .models import CITEDatum, CTSCatalog, CTSDatum


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
    folio_cite_datum = CITEDatum.objects.filter(
        fields__contains={"urn:cite2:hmt:va_dse.v1.surface:": folio.urn}
    )

    # @@@ what a hack, but is there another way to know the "work"
    # vs commentaries?
    catalog_obj = CTSCatalog.objects.get(work_title="Iliad")
    book_line_urn = catalog_obj.urn

    # @@@ might be a way we can do some db-level "icontains" against `urn:cite2:hmt:va_dse.v1.passage:`
    line_cite_datum = folio_cite_datum.filter(fields__icontains=book_line_urn)
    # @@@ might be a way we can use a subquery against the values in `urn:cite2:hmt:va_dse.v1.passage:`
    line_urns = [l.fields["urn:cite2:hmt:va_dse.v1.passage:"] for l in line_cite_datum]
    return CTSDatum.objects.filter(urn__in=line_urns)
