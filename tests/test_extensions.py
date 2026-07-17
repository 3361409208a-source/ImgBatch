# -*- coding: utf-8 -*-
"""Tests for extension pack registry."""

from imgbatch.core.extensions import (
    get_extensions_catalog,
    get_install_status,
    set_extension_path,
    start_install_extension,
)


def test_extensions_catalog():
    catalog = get_extensions_catalog()
    assert catalog['total_count'] >= 1
    lo = next(x for x in catalog['extensions'] if x['id'] == 'libreoffice')
    assert lo['name']
    assert lo['download_url']


def test_start_install_rejects_unknown():
    try:
        start_install_extension('unknown')
        assert False
    except ValueError:
        pass


def test_install_status_default():
    st = get_install_status()
    assert st['running'] is False


def test_set_libreoffice_path_invalid(tmp_path):
    try:
        set_extension_path('libreoffice', str(tmp_path / 'missing.exe'))
        assert False, 'expected ValueError'
    except ValueError:
        pass


def test_catalog_has_direct_url_and_install_dir():
    catalog = get_extensions_catalog()
    lo = next(x for x in catalog['extensions'] if x['id'] == 'libreoffice')
    assert lo['download_url'].startswith('https://download.documentfoundation.org/')
    assert lo['install_dir']
