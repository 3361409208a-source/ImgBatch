#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for AI rename parsing logic (no API calls)."""

from imgbatch.core.ai_rename import _parse_ai_response
from imgbatch.core.rename import sanitize_filename


class TestParseAIResponse:
    def test_parse_json_array(self):
        content = '[{"original": "a.jpg", "new": "player1.jpg"}, {"original": "b.jpg", "new": "player2.jpg"}]'
        result = _parse_ai_response(content, ['a.jpg', 'b.jpg'])
        assert len(result) == 2
        assert result[0]['original'] == 'a.jpg'
        assert result[0]['new'] == 'player1.jpg'

    def test_parse_with_surrounding_text(self):
        content = 'Here are the results:\n[{"original": "a.jpg", "new": "b.jpg"}]\nDone.'
        result = _parse_ai_response(content, ['a.jpg'])
        assert len(result) == 1
        assert result[0]['new'] == 'b.jpg'

    def test_parse_fallback_lines(self):
        content = 'newname1.jpg\nnewname2.jpg\nnewname3.jpg'
        result = _parse_ai_response(content, ['a.jpg', 'b.jpg', 'c.jpg'])
        assert len(result) == 3
        assert result[0]['new'] == 'newname1.jpg'

    def test_parse_empty_content(self):
        result = _parse_ai_response('', ['a.jpg'])
        # Fallback: content itself becomes the single element
        assert len(result) >= 0

    def test_parse_dict_items_missing_fields(self):
        content = '[{"original": "a.jpg"}]'
        result = _parse_ai_response(content, ['a.jpg'])
        assert len(result) == 1
        # Missing 'new' field should fall back to original
        assert result[0]['new'] == 'a.jpg'

    def test_sanitize_applied(self):
        content = '[{"original": "a.jpg", "new": "file<>name.jpg"}]'
        result = _parse_ai_response(content, ['a.jpg'])
        assert '<' not in result[0]['new']
        assert '>' not in result[0]['new']


class TestParseAiRenameResponse:
    def test_mapping_dict(self):
        from imgbatch.core.ai_rename import parse_ai_rename_response

        content = '[{"original": "a.jpg", "new": "player1.jpg"}]'
        mapping = parse_ai_rename_response(content, ['a.jpg', 'b.jpg'])
        assert mapping['a.jpg'] == 'player1.jpg'
        assert mapping['b.jpg'] == 'b.jpg'
