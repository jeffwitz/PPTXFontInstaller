from __future__ import annotations

import zipfile
from pathlib import Path


def make_ooxml(path: Path, entries: dict[str, bytes | str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            data = content.encode("utf-8") if isinstance(content, str) else content
            archive.writestr(name, data)
    return path


def make_pptx(path: Path, entries: dict[str, bytes | str]) -> Path:
    return make_ooxml(path, entries)


def make_docx(path: Path, entries: dict[str, bytes | str]) -> Path:
    return make_ooxml(path, entries)


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



def document_xml(*families: str) -> str:
    attrs = "".join(
        f'<w:r><w:rPr><w:rFonts w:ascii="{family}" w:hAnsi="{family}"/></w:rPr><w:t>x</w:t></w:r>'
        for family in families
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p>{attrs}</w:p></w:body>
</w:document>
"""


def document_theme_xml(theme_value: str = "minorHAnsi") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:rPr><w:rFonts w:asciiTheme="{theme_value}"/></w:rPr><w:t>x</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
