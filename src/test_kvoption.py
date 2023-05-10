import optparse
from unittest.mock import patch, mock_open

import pytest

from kvoption import KVOption, KVOptionException


@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_kv_file_option(mock_file):
    o = KVOption("--var")
    values = optparse.Values()
    o.take_action(None, 'foo', None, 'f=file:foofile', values, None)
    mock_file.assert_called_with("foofile", 'r')
    print(values)
    assert values.foo == {'f': 'data'}

def test_kv_no_duplicate_option():
    o = KVOption("--var")
    values = optparse.Values()
    o.take_action(None, 'foo', None, 'f=bar', values, None)
    with pytest.raises(KVOptionException):
        o.take_action(None, 'foo', None, 'f=fly', values, None)

def test_kv_file_not_found_exception():
    o = KVOption("--var")
    values = optparse.Values()
    with pytest.raises(KVOptionException):
        o.take_action(None, 'foo', None, 'f=file:bar', values, None)

def test_kv_action_in_constructor_not_allowed():
    with pytest.raises(KVOptionException):
        KVOption("--var", action='foo')
