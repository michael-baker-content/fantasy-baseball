import pytest
from publish_sheet import sheet_ids


def test_sheet_ids_selects_yes_and_sorts_ids(tmp_path):
    path = tmp_path / "sheet.csv"
    path.write_text("MLB ID,Sheet\n3,Yes\n2,No\n1, yes \n", encoding="utf-8-sig")
    assert sheet_ids(path) == [1, 3]


@pytest.mark.parametrize("content", ["Name,Sheet\nA,Yes\n", "MLB ID,Sheet\n1,Maybe\n", "MLB ID,Sheet\n1,Yes\n1,No\n", "MLB ID,Sheet\n0,Yes\n", "MLB ID,Sheet\n1\n", "MLB ID,Sheet\n1,Yes,extra\n"])
def test_invalid_sheet_rejected(tmp_path, content):
    path = tmp_path / "sheet.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        sheet_ids(path)
