from posixpath import join as urljoin
from urllib.parse import quote_plus


class IIIFResolver:
    BASE_URL = "https://image.library.jhu.edu/iiif/"
    COLLETION_SUBDIR = "homer/VA"

    def __init__(self, urn):
        """
        IIIFResolver("urn:cite2:hmt:vaimg.2017a:VA012VN_0514")
        """
        self.urn = urn

    @property
    def munged_image_path(self):
        image_part = self.urn.rsplit(":", maxsplit=1).pop()
        return image_part.replace("_", "-")

    @property
    def iif_image_id(self):
        path = urljoin(self.COLLETION_SUBDIR, self.munged_image_path)
        return quote_plus(path)

    @property
    def base_url(self):
        return urljoin(self.BASE_URL, self.iif_image_id)

    @property
    def image_url(self):
        default_image_path = "full/full/0/default.jpg"
        return urljoin(self.base_url, default_image_path)

    @property
    def info_url(self):
        info_path = "image.json"
        return urljoin(self.base_url, info_path)
