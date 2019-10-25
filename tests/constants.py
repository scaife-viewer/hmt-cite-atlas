CITE_DATA = {
    "urn:cite2:cite:datamodels.v1:": "urn:cite2:cite:datamodels.v1:imagemodel#Citable Image#Model of a citable image.  See http://cite-architecture.github.io/imagemodel/.",
    "urn:cite2:hmt:msA.v1:": "-2#urn:cite2:hmt:msA.v1:insidefrontcover#verso#Venetus A (Marciana 454 = 822), inside front cover#urn:cite2:hmt:vaimg.2017a:VAMSInside_front_cover_versoN_0500",
    "urn:cite2:hmt:binaryimg.v1:": "urn:cite2:hmt:binaryimg.v1:vaimg_amphoreusIIF#Binary data for images of the Venetus A manuscript. IIIF Files at the University of Houson.#urn:cite2:hmt:vaimg.2017a:#iiifApi#/project/homer/pyramidal/VenA/#http://www.homermultitext.org/iipsrv?#Creative Commons Attribution Share-Alike.",
    "urn:cite2:hmt:compimg.v1:": "urn:cite2:hmt:compimg.v1:Comparetti_001recto016#Domenico Comparetti, Homeri Ilias cum Scholiis (1901 facsimile edition of Venetus A): folio 001 recto#Image Copyright 2013, The Center for Hellenic Studies. Licensed under the Creative Commons NC-BY 3.0 License.",
    "urn:cite2:hmt:vaimg.2017a:": "urn:cite2:hmt:vaimg.2017a:VA082RN_0083#Venetus A: Marcianus Graecus Z. 454 (= 822).  Photograph in natural light, folio 82, recto.#This image was derived from an original ©2007, Biblioteca Nazionale Marciana, Venezie, Italia. The derivative image is ©2010, Center for Hellenic Studies. Original and derivative are licensed under the Creative Commons Attribution-Noncommercial-Share Alike 3.0 License. The CHS/Marciana Imaging Project was directed by David Jacobs of the British Library.",
    "urn:cite2:hmt:critsigns.v1:": "urn:cite2:hmt:critsigns.v1:diple#diple#διπλῆ ἀπερίστικτος#003E#No distinct character:  substitute greater-than sign for display.",
    "urn:cite2:hmt:va_signs.v1:": "urn:cite2:hmt:va_signs.v1:cs0#diple on Iliad 1.2#urn:cts:greekLit:tlg0012.tlg001.msA:1.2#urn:cite2:hmt:critsigns.v1:diple#0",
    "urn:cite2:hmt:va_dse.v1:": "urn:cite2:hmt:va_dse.v1:schol0#DSE record for scholion msA 1.1#urn:cts:greekLit:tlg5026.msA.hmt:1.1#urn:cite2:hmt:vaimg.2017a:VA012RN_0013@0.09125620,0.11955275,0.70064910,0.06909404#urn:cite2:hmt:msA.v1:12r",
    "urn:cite2:cite:verbs.v1:": "urn:cite2:cite:verbs.v1:commentsOn#Subject (a CtsUrn) comments on the object (a second CtsUrn).",
    "urn:cite2:hmt:pers.v1:": "urn:cite2:hmt:pers.v1:pers1#Achilles#hero of the Iliad, greatest warrior of the Greeks at Troy#proposed#",
    "urn:cite2:hmt:place.v1:": "urn:cite2:hmt:place.v1:place1#Athens#city in Attica#pleiades.stoa.org/places/579885#proposed#",
}  # noqa


CITE_PROPERTIES = {
    "urn:cite2:cite:datamodels.v1:": "urn:cite2:cite:datamodels.v1.urn:#Data model#Cite2Urn#",
    "urn:cite2:hmt:msA.v1:": "urn:cite2:hmt:msA.v1.rv:#Recto or Verso#String#recto,verso",
    "urn:cite2:hmt:binaryimg.v1:": "urn:cite2:hmt:binaryimg.v1.protocol:#Protocol#String#iiifApi,localDeepZoom,JPG,iipDeepZoom",
    "urn:cite2:hmt:compimg.v1:": "urn:cite2:hmt:compimg.v1.urn:#URN#Cite2Urn#",
    "urn:cite2:hmt:vaimg.2017a:": "urn:cite2:hmt:vaimg.2017a.urn:#URN#Cite2Urn#",
    "urn:cite2:hmt:critsigns.v1:": "urn:cite2:hmt:critsigns.v1.urn:#Aristarchan sign#Cite2Urn#",
    "urn:cite2:hmt:va_signs.v1:": "urn:cite2:hmt:va_signs.v1.urn:#URN#Cite2Urn#",
    "urn:cite2:hmt:va_dse.v1:": "urn:cite2:hmt:va_dse.v1.urn:#DSE record#Cite2Urn#",
    "urn:cite2:cite:verbs.v1:": "urn:cite2:cite:verbs.v1.urn:#URN#Cite2Urn#",
}

COLUMN_VARIANTS = [
    ("URN", "urn"),
    ("urn", "urn"),
    ("Description", "description"),
    ("Labelling property", "labelling_property"),
    ("Ordering Property", "ordering_property"),
    ("groupName", "group_name"),
]
