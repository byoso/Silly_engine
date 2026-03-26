import logging

from silly_engine.logger import CustomFormatter, Logger


def test_custom_formatter_returns_string():
    fmt = CustomFormatter()
    record = logging.LogRecord(name='n', level=logging.INFO, pathname=__file__, lineno=1, msg='hello', args=(), exc_info=None)
    out = fmt.format(record)
    assert 'hello' in out


def test_logger_set_level_and_handler():
    l = Logger('tst')
    l.setLevel('DEBUG')
    assert l.level == logging.DEBUG
    assert hasattr(l, 'console_handler')
