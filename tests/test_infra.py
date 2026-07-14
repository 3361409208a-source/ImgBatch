#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for infrastructure: settings, i18n, logger."""

import json
import os

from imgbatch.infra.settings import load_config, save_config, DEFAULT_CONFIG
from imgbatch.infra.i18n import get_i18n, tr, TRANSLATIONS


class TestSettings:
    def test_default_config(self, monkeypatch, tmp_path):
        monkeypatch.setattr('imgbatch.infra.settings.CONFIG_FILE', tmp_path / 'config.json')
        config = load_config()
        assert config['language'] == 'zh'
        assert config['compress_ratio'] == 75

    def test_save_and_load(self, monkeypatch, tmp_path):
        config_path = tmp_path / 'config.json'
        monkeypatch.setattr('imgbatch.infra.settings.CONFIG_FILE', config_path)
        monkeypatch.setattr('imgbatch.infra.settings.CONFIG_DIR', tmp_path)

        config = DEFAULT_CONFIG.copy()
        config['compress_ratio'] = 50
        config['language'] = 'en'
        save_config(config)

        assert config_path.exists()
        loaded = load_config()
        assert loaded['compress_ratio'] == 50
        assert loaded['language'] == 'en'

    def test_corrupt_config_falls_back(self, monkeypatch, tmp_path):
        config_path = tmp_path / 'config.json'
        config_path.write_text('not json {{{', encoding='utf-8')
        monkeypatch.setattr('imgbatch.infra.settings.CONFIG_FILE', config_path)

        config = load_config()
        assert config['compress_ratio'] == 75  # default


class TestI18n:
    def test_translation_keys_exist(self):
        """All keys in zh should exist in en and vice versa."""
        zh_keys = set(TRANSLATIONS['zh'].keys())
        en_keys = set(TRANSLATIONS['en'].keys())
        assert zh_keys == en_keys, f'Missing keys: zh-only={zh_keys-en_keys}, en-only={en_keys-zh_keys}'

    def test_switch_language(self):
        i18n = get_i18n()
        i18n.set_lang('zh')
        assert tr('ready') == '\u5c31\u7eea'
        i18n.set_lang('en')
        assert tr('ready') == 'Ready'

    def test_missing_key_returns_key(self):
        i18n = get_i18n()
        assert tr('nonexistent_key_xyz') == 'nonexistent_key_xyz'

    def test_format_substitution(self):
        i18n = get_i18n()
        i18n.set_lang('en')
        result = tr('confirm_rename', n=5)
        assert '5' in result
