"""Attribution for the BE software, distinct from study/report authorship."""

DEVELOPER = "Nguyễn Trần Linh"
COPYRIGHT_NOTICE = f"© 2026 {DEVELOPER}"


def software_attribution(language: str = "vi") -> str:
    label = "Phần mềm phát triển bởi" if language == "vi" else "Software developed by"
    return f"{label} {DEVELOPER} · {COPYRIGHT_NOTICE}"
