#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for rename logic."""

import os

from imgbatch.core.rename import (
    generate_rename_map, resolve_conflict, sanitize_filename,
    ConflictResolution, RenameMode,
)


class TestGenerateRenameMap:
    def test_prefix_mode(self):
        files = [{'name': 'a.jpg'}, {'name': 'b.png'}]
        mapping = generate_rename_map(files, 'prefix', prefix='photo_')
        assert mapping == {'a.jpg': 'photo_a.jpg', 'b.png': 'photo_b.png'}

    def test_suffix_mode(self):
        files = [{'name': 'a.jpg'}, {'name': 'b.png'}]
        mapping = generate_rename_map(files, 'suffix', suffix='_x')
        assert mapping == {'a.jpg': 'a_x.jpg', 'b.png': 'b_x.png'}

    def test_replace_mode(self):
        files = [{'name': 'old_name.jpg'}, {'name': 'no_match.png'}]
        mapping = generate_rename_map(files, 'replace', find='old', replace='new')
        assert mapping == {'old_name.jpg': 'new_name.jpg'}

    def test_seq_mode(self):
        files = [{'name': 'a.jpg'}, {'name': 'b.jpg'}, {'name': 'c.jpg'}]
        mapping = generate_rename_map(files, 'seq', seq_template='img_{num}',
                                       seq_start=1, seq_digits=3)
        assert mapping == {'a.jpg': 'img_001.jpg', 'b.jpg': 'img_002.jpg', 'c.jpg': 'img_003.jpg'}

    def test_case_lower(self):
        files = [{'name': 'Photo.JPG'}]
        mapping = generate_rename_map(files, 'case', lowercase=True)
        assert mapping == {'Photo.JPG': 'photo.JPG'}

    def test_case_upper(self):
        files = [{'name': 'photo.jpg'}]
        mapping = generate_rename_map(files, 'case', uppercase=True)
        assert mapping == {'photo.jpg': 'PHOTO.jpg'}

    def test_no_change_excluded(self):
        files = [{'name': 'a.jpg'}]
        mapping = generate_rename_map(files, 'prefix', prefix='')
        assert mapping == {}


class TestSanitizeFilename:
    def test_removes_illegal_chars(self):
        assert sanitize_filename('file<name>') == 'filename'
        assert sanitize_filename('a:b/c\\d') == 'abcd'

    def test_removes_control_chars(self):
        assert sanitize_filename('file\x00name') == 'filename'

    def test_strips_dots_spaces(self):
        assert sanitize_filename('  ..file..  ') == 'file'

    def test_empty_input(self):
        assert sanitize_filename('') == ''

    def test_removes_braces_quotes(self):
        assert sanitize_filename("{file}'name\"") == 'filename'


class TestResolveConflict:
    def test_no_conflict(self):
        assert resolve_conflict('new.jpg', set(), ConflictResolution.SKIP) == 'new.jpg'

    def test_skip(self):
        assert resolve_conflict('exists.jpg', {'exists.jpg'}, ConflictResolution.SKIP) is None

    def test_overwrite(self):
        assert resolve_conflict('exists.jpg', {'exists.jpg'}, ConflictResolution.OVERWRITE) == 'exists.jpg'

    def test_auto_number(self):
        result = resolve_conflict('exists.jpg', {'exists.jpg'}, ConflictResolution.AUTO_NUMBER)
        assert result == 'exists_1.jpg'

    def test_auto_number_multiple(self):
        existing = {'exists.jpg', 'exists_1.jpg', 'exists_2.jpg'}
        result = resolve_conflict('exists.jpg', existing, ConflictResolution.AUTO_NUMBER)
        assert result == 'exists_3.jpg'
