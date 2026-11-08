"""Reusable, explicitly committed Streamlit spreadsheet-style input tables."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable

import pandas as pd
import streamlit as st

from be_app.field_help import render_table_legend, table_column_config


def prepare_blq_editor(frame: pd.DataFrame, column_config: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Render recognized boolean BLQ columns as checkboxes with a new-row default.

    Preserve invalid source flags as text so QC can still report them; do not
    silently reinterpret an unrecognized source value as False. Empty/new cells
    are initialized with the default False (unchecked checkbox).
    """
    prepared = frame.copy(deep=True)
    config = dict(column_config or {})
    flag_values = {
        "true": True, "false": False, "1": True, "0": False,
        "yes": True, "no": False, "có": True, "không": False,
    }
    for column in prepared.columns:
        if normalized_header(column) not in {"blq", "blq_flag"}:
            continue
        original = prepared[column]
        if original.empty:
            prepared[column] = prepared[column].astype(bool)
            config[column] = st.column_config.CheckboxColumn("BLQ", default=False, required=True)
            continue
        invalid = False
        mapped_values = []
        for val in original:
            if val is None or pd.isna(val) or str(val).strip() == "":
                mapped_values.append(False)
            else:
                s = str(val).strip().lower()
                if s in flag_values:
                    mapped_values.append(flag_values[s])
                else:
                    invalid = True
                    break
        if invalid:
            continue
        prepared[column] = pd.Series(mapped_values, index=prepared.index, dtype=bool)
        config[column] = st.column_config.CheckboxColumn("BLQ", default=False, required=True)
    return prepared, config


def normalized_header(value: object) -> str:
    """Match the visible header without assuming a column's position."""
    return str(value).strip().casefold()


def suggest_column_mapping(source: Iterable[object], targets: Iterable[str]) -> dict[str, str]:
    """Infer only unambiguous matching headers; exact spellings need no rename."""
    names = [str(item) for item in source]
    allowed = list(targets)
    normalized = [normalized_header(name) for name in names]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Tên cột nguồn trùng nhau sau khi bỏ khoảng trắng và phân biệt hoa/thường.")
    target_lookup = {normalized_header(name): name for name in allowed}
    if len(target_lookup) != len(allowed):
        raise ValueError("Schema đích có tên cột trùng nhau.")
    return {
        name: target_lookup[key]
        for name, key in zip(names, normalized, strict=True)
        if key in target_lookup and name != target_lookup[key]
    }


def combine_column_mappings(
    automatic: dict[str, str],
    legacy: dict[str, str],
    manual: dict[str, str | None],
) -> dict[str, str]:
    """UI dropdown choices override saved JSON, while preserving legacy mappings.

    A None override intentionally retains the original source header.
    The import preflight performs authoritative schema and collision checks.
    """
    combined = {**automatic, **legacy}
    for source, target in manual.items():
        if target is None:
            combined.pop(source, None)
        else:
            combined[source] = target
    return combined


def validate_structure(frame: pd.DataFrame, *, required: Iterable[str] = (),
                       max_rows: int = 100_000) -> pd.DataFrame:
    """Check only table shape. Domain-specific checks belong to the caller."""
    if frame.empty:
        raise ValueError("Bảng cần ít nhất một dòng dữ liệu.")
    if len(frame) > max_rows:
        raise ValueError(f"Bảng vượt giới hạn {max_rows:,} dòng.")
    if frame.columns.duplicated().any():
        raise ValueError("Bảng có tên cột trùng nhau.")
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError("Thiếu cột: " + ", ".join(sorted(missing)))
    return frame.reset_index(drop=True).copy()


def _apply_editor_changes(base_df: pd.DataFrame, delta: dict) -> pd.DataFrame:
    """Apply st.data_editor delta dict (edited_rows, added_rows, deleted_rows) to base dataframe."""
    df = base_df.copy().reset_index(drop=True)

    # 1. Add added rows first so new row indices exist for edits and deletions
    added_rows = delta.get("added_rows", [])
    if added_rows:
        rows_to_add = []
        for new_row in added_rows:
            if isinstance(new_row, dict):
                row_data = {}
                for col in df.columns:
                    val = new_row.get(col, None)
                    if val is None or pd.isna(val) or str(val).strip() == "":
                        if normalized_header(col) in {"blq", "blq_flag"}:
                            val = False
                    row_data[col] = val
                rows_to_add.append(row_data)
        if rows_to_add:
            add_df = pd.DataFrame(rows_to_add, columns=df.columns).astype(df.dtypes)
            df = pd.concat([df, add_df], ignore_index=True)

    # 2. Update edited cells (works on both original and newly added rows)
    edited_rows = delta.get("edited_rows", {})
    if isinstance(edited_rows, dict):
        for row_idx_str, col_changes in edited_rows.items():
            row_idx = int(row_idx_str)
            if 0 <= row_idx < len(df) and isinstance(col_changes, dict):
                for col_name, new_val in col_changes.items():
                    if col_name in df.columns:
                        if normalized_header(col_name) in {"blq", "blq_flag"}:
                            if new_val is None or pd.isna(new_val) or str(new_val).strip() == "":
                                new_val = False
                            elif str(new_val).strip().lower() in ("true", "1", "yes", "có"):
                                new_val = True
                            elif str(new_val).strip().lower() in ("false", "0", "no", "không"):
                                new_val = False
                        df.at[row_idx, col_name] = new_val

    # 3. Delete deleted rows (can delete both original and newly added rows)
    deleted_rows = delta.get("deleted_rows", [])
    if deleted_rows:
        valid_del = [int(i) for i in deleted_rows if 0 <= int(i) < len(df)]
        if valid_del:
            df = df.drop(index=valid_del).reset_index(drop=True)

    return df.reset_index(drop=True)


def render_persistent_editor(
    table_id: str,
    initial: pd.DataFrame,
    source_id: str,
    *,
    validator: Callable[[pd.DataFrame], pd.DataFrame] | None = None,
    submit_label: str = "Áp dụng chỉnh sửa bảng",
    max_rows: int = 100_000,
    on_commit: Callable[[pd.DataFrame], None] | None = None,
    **editor_kwargs,
) -> pd.DataFrame:
    """Keep committed values separate from the Streamlit widget's unsent draft.

    A source/sheet/mapping change explicitly replaces the working table. Values
    returned by the editor on form submission already include added/deleted rows.
    """
    key = f"table::{table_id}"
    identity = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:20]
    saved = st.session_state.get(key)
    if saved is None or saved["source_id"] != source_id:
        saved = dict(source_id=source_id, committed=initial.copy(deep=True),
                     draft=initial.copy(deep=True), generation=0)
        st.session_state[key] = saved

    editor_widget_key = f"table_editor::{table_id}::{identity}::{saved['generation']}"
    form_key = f"table_form::{table_id}::{identity}"

    err_key = f"_editor_error::{table_id}"
    last_err = st.session_state.get(err_key)
    if last_err and hasattr(st, "error"):
        st.error(f"⚠️ Chưa áp dụng được bảng: {last_err}")
        if hasattr(st, "caption"):
            st.caption("Dữ liệu bạn vừa chỉnh sửa đang được giữ trong bảng bên dưới. Hãy sửa lại hoặc hoàn tác.")
        def _discard():
            saved["draft"] = saved["committed"].copy(deep=True)
            saved["generation"] += 1
            st.session_state.pop(err_key, None)
        if hasattr(st, "button"):
            st.button("↩️ Hoàn tác về dữ liệu hợp lệ gần nhất", key=f"discard::{table_id}::{saved['generation']}", on_click=_discard)

    with st.form(key=form_key):
        if hasattr(st, "caption"):
            st.caption(
                "💡 **Hướng dẫn nhập liệu:** Có thể sao chép và dán trực tiếp vùng ô từ Excel (`Ctrl+V`), "
                "thêm hoặc chọn dòng để xóa. Sau khi sửa, **bắt buộc bấm nút Áp dụng** để xác nhận lưu bảng."
            )
        editor_frame, column_config = prepare_blq_editor(saved["draft"], editor_kwargs.get("column_config"))
        column_config = table_column_config(editor_frame.columns, column_config)
        editor_kwargs["column_config"] = column_config
        edited = st.data_editor(
            editor_frame, num_rows="dynamic", hide_index=True,
            key=editor_widget_key,
            **editor_kwargs,
        )
        submitted = st.form_submit_button(submit_label)
    if hasattr(st, "expander"):
        render_table_legend(saved["committed"].columns, title="ℹ️ Chú thích tiêu đề cột bảng dữ liệu")
    if submitted:
        delta = st.session_state.get(editor_widget_key)
        if isinstance(delta, dict) and any(delta.get(k) for k in ("edited_rows", "added_rows", "deleted_rows")):
            candidate = _apply_editor_changes(editor_frame, delta)
        else:
            candidate = edited.copy().reset_index(drop=True)

        # Drop completely blank rows (e.g. from empty Excel lines, cleared rows, or trailing blank rows)
        if not candidate.empty:
            def _is_cell_blank(val: object) -> bool:
                if val is None or pd.isna(val):
                    return True
                s = str(val).strip()
                return s == "" or s.lower() in ("none", "nan")

            def _is_row_blank(row: pd.Series) -> bool:
                non_flag_cols = [c for c in row.index if normalized_header(c) not in {"blq", "blq_flag"}]
                cols_to_check = non_flag_cols if non_flag_cols else row.index
                return all(_is_cell_blank(row[c]) for c in cols_to_check)

            blank_mask = candidate.apply(_is_row_blank, axis=1)
            if blank_mask.any() and not blank_mask.all():
                candidate = candidate[~blank_mask].reset_index(drop=True)

        # Normalize BLQ columns to clean boolean values
        for col in candidate.columns:
            if normalized_header(col) in {"blq", "blq_flag"}:
                candidate[col] = candidate[col].map(
                    lambda v: True if str(v).strip().lower() in ("true", "1", "yes", "có") else False
                ).astype(bool)

        try:
            candidate = validate_structure(candidate, max_rows=max_rows)
            if validator is not None:
                candidate = validator(candidate)
            # A valid commit is the only way to change the canonical table.
            saved["committed"] = candidate.copy(deep=True)
            saved["draft"] = candidate.copy(deep=True)
            saved["generation"] += 1
            st.session_state.pop(err_key, None)
            if on_commit is not None:
                on_commit(saved["committed"])
            if hasattr(st, "toast"):
                st.toast("✅ Đã áp dụng bảng thành công!", icon="✅")
            if hasattr(st, "success"):
                st.success("Đã áp dụng bảng, bao gồm các ô dán và dòng thêm/xóa.")
            if hasattr(st, "rerun"):
                st.rerun()
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            # Preserve invalid cells for repair without publishing to analyses.
            saved["draft"] = candidate.copy(deep=True)
            saved["generation"] += 1
            st.session_state[err_key] = str(exc)
            if hasattr(st, "error"):
                st.error(f"Chưa áp dụng bảng: {exc}")
            if hasattr(st, "rerun"):
                st.rerun()
    return saved["committed"].copy(deep=True)
