from silly_engine.text_tools import Title, Color


def test_title_builds_and_string():
    t = Title('ab')
    s = str(t)
    assert '\n' in s


def test_color_attributes_exist():
    c = Color()
    assert hasattr(c, 'info')
    assert hasattr(c, 'end')
