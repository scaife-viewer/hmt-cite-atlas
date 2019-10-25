from unittest import mock

import pytest

from hmt_cite_atlas.library.importers import Parser
from tests import constants


@pytest.mark.parametrize("value,expected", constants.COLUMN_VARIANTS)
def test_normalize_columns(value, expected):
    assert Parser.normalize_column(value) == expected


@pytest.mark.parametrize("urn,line", constants.CITE_PROPERTIES.items())
def test_handle_citeproperties(urn, line):
    parser = Parser("some_path", mock.MagicMock())
    parser.columns = {
        "#!citeproperties": ["Property", "Label", "Type", "Authority list"]
    }
    parser.current_block = "#!citeproperties"
    parser.handle_citeproperties(line)
    obj_urn = line.split("#")[0]
    assert obj_urn in parser.columns[urn]
    assert obj_urn in parser.index
