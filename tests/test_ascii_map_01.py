from silly_engine.core.components import ascii_map_01


def test_abc_map_has_letters_and_numbers():
    m = ascii_map_01.abc_map_01
    assert 'a' in m
    assert 'A' in m
    assert '0' in m
    assert isinstance(m['a'], list)
    assert len(m['a']) > 0
