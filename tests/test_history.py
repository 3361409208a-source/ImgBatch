#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for history and undo system."""

import os
import tempfile

from imgbatch.history import HistoryManager, OperationRecord, undo_operation


class TestHistoryManager:
    def test_push_and_pop(self, monkeypatch, tmp_path):
        monkeypatch.setattr('imgbatch.history.HISTORY_FILE', tmp_path / 'history.json')
        monkeypatch.setattr('imgbatch.history.CONFIG_DIR', tmp_path)

        mgr = HistoryManager()
        record = OperationRecord(op_type='rename', folder='/tmp', rename_map={'a.jpg': 'b.jpg'})
        mgr.push(record)

        assert mgr.can_undo
        popped = mgr.pop()
        assert popped is not None
        assert popped.op_type == 'rename'
        assert not mgr.can_undo

    def test_persistence(self, monkeypatch, tmp_path):
        monkeypatch.setattr('imgbatch.history.HISTORY_FILE', tmp_path / 'history.json')
        monkeypatch.setattr('imgbatch.history.CONFIG_DIR', tmp_path)

        mgr1 = HistoryManager()
        mgr1.push(OperationRecord(op_type='compress', folder='/tmp', files=['a.jpg']))

        mgr2 = HistoryManager()
        assert mgr2.can_undo
        assert mgr2.peek().op_type == 'compress'

    def test_max_history(self, monkeypatch, tmp_path):
        monkeypatch.setattr('imgbatch.history.HISTORY_FILE', tmp_path / 'history.json')
        monkeypatch.setattr('imgbatch.history.CONFIG_DIR', tmp_path)

        mgr = HistoryManager()
        for i in range(30):
            mgr.push(OperationRecord(op_type=f'op_{i}'))

        assert len(mgr.records) <= 20


class TestUndoOperation:
    def test_undo_rename(self, tmp_path):
        # Create files and rename them
        old_path = tmp_path / 'old.jpg'
        new_path = tmp_path / 'new.jpg'
        old_path.write_text('test')

        os.rename(old_path, new_path)

        record = OperationRecord(
            op_type='rename',
            folder=str(tmp_path),
            rename_map={'old.jpg': 'new.jpg'},
        )

        result = undo_operation(record)
        assert result['success']
        assert old_path.exists()
        assert not new_path.exists()

    def test_undo_no_method(self):
        record = OperationRecord(op_type='unknown', folder='/nonexistent')
        result = undo_operation(record)
        assert not result['success']
