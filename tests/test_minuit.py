from silly_engine.minuit import TextField, MenuItem, AutoArray, FieldError


def test_textfield_builds_display():
    tf = TextField('hello world', width=5)
    s = str(tf)
    assert '\n' in s


def test_menu_item_calls_callback():
    called = {'v': False}

    def cb():
        called['v'] = True

    mi = MenuItem('1', 'lbl', cb)
    mi()
    assert called['v'] is True


def test_autoarray_and_get():
    arr = AutoArray([{'a': 1}, {'a': 2}], width=40)
    s = str(arr)
    assert 'index' in s
    assert arr.get(1) == {'a': 2}
    assert arr.get(10) is None


def test_listfield_invalid_choices_raises():
    from silly_engine.minuit import ListField
    with __import__('pytest').raises(FieldError):
        ListField('name', choices=[(1, 2, 3)])
