from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "ai_platform/portal/execution/host_isolation.py",
    '''            if normalized_fields[0] == "qgroupid":\n                try:\n                    max_rfer_index = normalized_fields.index("max_rfer")\n                except ValueError:\n                    return None\n                continue\n''',
    '''            if normalized_fields[0] == "qgroupid":\n                if "max_rfer" in normalized_fields:\n                    max_rfer_index = normalized_fields.index("max_rfer")\n                else:\n                    max_rfer_index = next(\n                        (\n                            index\n                            for index in range(len(normalized_fields) - 1)\n                            if normalized_fields[index : index + 2] == ["max", "referenced"]\n                        ),\n                        None,\n                    )\n                    if max_rfer_index is None:\n                        return None\n                continue\n''',
)

replace_once(
    "tests/ai_platform/portal/execution/test_host_isolation.py",
    '''def _qgroup_output(limit: int) -> str:\n    return f"QGROUPID RFER EXCL MAX_RFER\\n-------- ---- ---- --------\\n0/256 0 0 {limit}\\n"\n''',
    '''def _qgroup_output(limit: int) -> str:\n    return (\n        "Qgroupid Referenced Exclusive Max referenced Path\\n"\n        "-------- ---------- --------- -------------- ----\\n"\n        f"0/256 0 0 {limit} generation\\n"\n    )\n\n\ndef test_qgroup_limit_parser_accepts_legacy_max_rfer_header() -> None:\n    output = "QGROUPID RFER EXCL MAX_RFER\\n-------- ---- ---- --------\\n0/256 0 0 8192\\n"\n\n    assert LinuxNftablesBtrfsIsolationAttestor._qgroup_max_rfer(output, "0/256") == 8192\n''',
)
