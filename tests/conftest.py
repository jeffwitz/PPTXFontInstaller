from __future__ import annotations

import zipfile
from pathlib import Path


def make_pptx(path: Path, entries: dict[str, bytes | str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            data = content.encode("utf-8") if isinstance(content, str) else content
            archive.writestr(name, data)
    return path


def slide_xml(*families: str) -> str:
    body = "".join(f'<a:rPr><a:latin typeface="{family}"/></a:rPr>' for family in families)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>{body}</p:spTree></p:cSld>
</p:sld>
"""


def theme_xml(minor_latin: str = "Aptos", major_latin: str = "Aptos Display") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <a:themeElements>
    <a:fontScheme name="Office">
      <a:majorFont>
        <a:latin typeface="{major_latin}"/>
        <a:ea typeface="Yu Gothic"/>
        <a:cs typeface="Arial"/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="{minor_latin}"/>
        <a:ea typeface="Yu Gothic"/>
        <a:cs typeface="Arial"/>
      </a:minorFont>
    </a:fontScheme>
  </a:themeElements>
</a:theme>
"""

