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
    assert catalog['total_count'] >= 2
    lo = next(x for x in catalog['extensions'] if x['id'] == 'libreoffice')
    assert lo['name']
    assert lo['download_url']
    ff = next(x for x in catalog['extensions'] if x['id'] == 'ffmpeg')
    assert 'ffmpeg' in ff['download_url'].lower() or 'gyan' in ff['download_url'].lower()


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
    ff = next(x for x in catalog['extensions'] if x['id'] == 'ffmpeg')
    assert ff['install_dir']
    assert ff['download_url'].startswith('https://')


def test_ffmpeg_already_installed_short_circuits(monkeypatch):
    monkeypatch.setattr(
        'imgbatch.core.extensions.is_ffmpeg_installed',
        lambda: True,
    )
    monkeypatch.setattr(
        'imgbatch.core.extensions.find_ffmpeg_extension',
        lambda: r'C:\ffmpeg\bin\ffmpeg.exe',
    )
    res = start_install_extension('ffmpeg')
    assert res['already_installed'] is True
    assert res['started'] is False
