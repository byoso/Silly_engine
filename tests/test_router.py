from silly_engine.core.router import text_chunks, _formatting_incoming_route_width, Router


def test_text_chunks():
    assert text_chunks('abcdef', 2) == ['ab', 'cd', 'ef']


def test_formatting_incoming_route_width():
    out = _formatting_incoming_route_width(("cmd",  None, 'longtext'), 40)
    assert '->' in out


def test_router_add_and_query():
    r = Router(width=50)

    def handler(x=None):
        return x * 2 if x is not None else 'ok'

    r.add_route(['ping', lambda: 'pong', 'desc'])
    assert r.query(['ping']) == 'pong'

    r.add_route(['add <x:int>', handler, 'add desc'])
    assert r.query(['add', '3']) == 6
