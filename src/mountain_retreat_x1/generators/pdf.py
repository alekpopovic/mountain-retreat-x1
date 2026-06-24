"""PDF generation from generated Markdown volumes."""

from html import escape
from pathlib import Path
from re import sub
from typing import Any
from warnings import warn

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.generators.markdown import MARKDOWN_OUTPUT_DIR, generate_markdown_volumes

try:
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.enums import TA_CENTER  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import (  # type: ignore[import-untyped]
        ParagraphStyle,
        getSampleStyleSheet,
    )
    from reportlab.lib.units import mm  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    colors = None
    TA_CENTER = 1
    A4 = (595.2755905511812, 841.8897637795277)
    ParagraphStyle = None
    getSampleStyleSheet = None
    mm = 2.834645669291339
    PageBreak = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None
    REPORTLAB_AVAILABLE = False

PDF_OUTPUT_DIR = "pdf"
PDF_TEMPLATE_DIR = Path("docs/templates/pdf")
PDF_TEMPLATE_NAME = "base.html"

PDF_FILES = {
    "01_project_charter.md": "01_Project_Charter.pdf",
    "02_architectural_package.md": "02_Architectural_Package.pdf",
    "03_structural_concept.md": "03_Structural_Concept.pdf",
    "04_electrical_package.md": "04_Electrical_Package.pdf",
    "05_plumbing_wastewater.md": "05_Plumbing_Wastewater.pdf",
    "06_hvac_package.md": "06_HVAC_Package.pdf",
    "07_smart_home_security.md": "07_Smart_Home_Security.pdf",
    "08_off_grid_package.md": "08_Off_Grid_Package.pdf",
    "09_bom_summary.md": "09_BOM_Summary.pdf",
    "10_cost_estimate_summary.md": "10_Cost_Estimate_Summary.pdf",
    "11_construction_management.md": "11_Construction_Management.pdf",
    "12_maintenance_manual.md": "12_Maintenance_Manual.pdf",
    "13_self_build_guide.md": "13_Self_Build_Guide.pdf",
    "14_legal_and_professional_limits.md": "14_Legal_and_Professional_Limits.pdf",
    "15_serbia_balkan_context.md": "15_Serbia_Balkan_Context.pdf",
}


def _volume_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("_", " ").removesuffix(".pdf")


def _safety_notice(config: MountainRetreatConfig) -> str:
    return (
        f"{config.project.disclaimer} PRELIMINARY - not for construction, permitting, "
        "procurement, financing, or legal reliance. Licensed professional and local "
        "authority review required."
    )


def _inline_markdown(text: str) -> str:
    escaped = escape(text)
    escaped = sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", escaped)
    return escaped


def _markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if not line:
            index += 1
            continue
        if line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")), 3)
            text = line[level:].strip()
            html.append(f"<h{level}>{_inline_markdown(text)}</h{level}>")
        elif line.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                if not set(lines[index].replace("|", "").strip()) <= {"-", ":"}:
                    table_lines.append(lines[index])
                index += 1
            html.append("<table>")
            for row_number, table_line in enumerate(table_lines):
                cells = [cell.strip() for cell in table_line.strip("|").split("|")]
                tag = "th" if row_number == 0 else "td"
                row_html = "".join(
                    f"<{tag}>{_inline_markdown(cell)}</{tag}>" for cell in cells
                )
                html.append(f"<tr>{row_html}</tr>")
            html.append("</table>")
            continue
        elif line.startswith("- "):
            html.append(f"<p>&bull; {_inline_markdown(line[2:])}</p>")
        else:
            html.append(f"<p>{_inline_markdown(line)}</p>")
        index += 1
    return "\n".join(html)


def _weasyprint_available() -> bool:
    try:
        import weasyprint  # type: ignore[import-not-found] # noqa: F401
    except Exception:
        return False
    return True


def _render_with_weasyprint(
    config: MountainRetreatConfig,
    markdown_path: Path,
    pdf_path: Path,
    template_dir: Path,
) -> None:
    from weasyprint import HTML  # type: ignore[import-not-found]

    markdown_text = markdown_path.read_text(encoding="utf-8")
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(),
    )
    template = env.get_template(PDF_TEMPLATE_NAME)
    html = template.render(
        project=config.project,
        volume_title=_volume_title(markdown_text, pdf_path.name),
        body_html=_markdown_to_html(markdown_text),
        safety_notice=_safety_notice(config),
    )
    HTML(string=html, base_url=str(template_dir.resolve())).write_pdf(pdf_path)


def _paragraph_style(name: str, size: int, leading: int, bold: bool = False) -> Any:
    return ParagraphStyle(
        name=name,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size,
        leading=leading,
        spaceAfter=6,
    )


def _table_from_markdown(lines: list[str]) -> Any:
    data = []
    for line in lines:
        if set(line.replace("|", "").strip()) <= {"-", ":"}:
            continue
        data.append([_inline_markdown(cell.strip()) for cell in line.strip("|").split("|")])
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B9C2CC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    return table


def _reportlab_story(
    config: MountainRetreatConfig,
    markdown_text: str,
    pdf_name: str,
) -> list[object]:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=18,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        spaceAfter=18,
    )
    h1 = _paragraph_style("MRX1H1", 16, 20, True)
    h2 = _paragraph_style("MRX1H2", 13, 17, True)
    h3 = _paragraph_style("MRX1H3", 11, 15, True)
    body = _paragraph_style("MRX1Body", 9, 12)
    notice = ParagraphStyle(
        "Notice",
        parent=body,
        textColor=colors.HexColor("#9C0006"),
        fontName="Helvetica-Bold",
    )
    volume_title = _volume_title(markdown_text, pdf_name)
    story: list[object] = [
        Spacer(1, 70 * mm),
        Paragraph(escape(config.project.project_name), title_style),
        Paragraph(escape(volume_title), subtitle_style),
        Paragraph(f"<b>Version:</b> {escape(config.project.version)}", body),
        Paragraph(f"<b>Status:</b> {escape(config.project.status)}", body),
        Paragraph(f"<b>Revision date:</b> {config.project.revision_date}", body),
        Spacer(1, 12 * mm),
        Paragraph(escape(_safety_notice(config)), notice),
        Paragraph(
            "No fake stamps, fake signatures, or construction approvals are included.",
            notice,
        ),
        PageBreak(),
        Paragraph("Table of Contents", h1),
    ]
    headings = [
        line.strip("# ").strip()
        for line in markdown_text.splitlines()
        if line.startswith("## ")
    ]
    for heading in headings[:35]:
        story.append(Paragraph(_inline_markdown(heading), body))
    story.append(PageBreak())

    lines = markdown_text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(_inline_markdown(line[2:].strip()), h1))
        elif line.startswith("## "):
            story.append(Paragraph(_inline_markdown(line[3:].strip()), h2))
        elif line.startswith("### "):
            story.append(Paragraph(_inline_markdown(line[4:].strip()), h3))
        elif line.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            if table_lines:
                story.append(_table_from_markdown(table_lines))
                story.append(Spacer(1, 4 * mm))
            continue
        elif line.startswith("- "):
            story.append(Paragraph(f"&bull; {_inline_markdown(line[2:])}", body))
        else:
            story.append(Paragraph(_inline_markdown(line), body))
        index += 1
    return story


def _draw_footer(canvas: Any, doc: object, config: MountainRetreatConfig) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#666666"))
    width, _height = A4
    page_number = canvas.getPageNumber()
    footer = (
        "PRELIMINARY - not for construction/permitting/procurement/legal reliance - "
        "licensed professional review required - "
        f"page {page_number}"
    )
    canvas.drawCentredString(width / 2, 10 * mm, footer)
    canvas.restoreState()


def _render_with_reportlab(
    config: MountainRetreatConfig,
    markdown_path: Path,
    pdf_path: Path,
) -> None:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=_volume_title(markdown_text, pdf_path.name),
        author=config.project.author,
    )
    story = _reportlab_story(config, markdown_text, pdf_path.name)
    doc.build(
        story,
        onFirstPage=lambda canvas, doc_obj: _draw_footer(canvas, doc_obj, config),
        onLaterPages=lambda canvas, doc_obj: _draw_footer(canvas, doc_obj, config),
    )


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _plain_text_lines(markdown_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if line.startswith("|"):
            if set(line.replace("|", "").strip()) <= {"-", ":"}:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            line = " | ".join(cells)
        elif line.startswith("#"):
            line = line.lstrip("#").strip()
        elif line.startswith("- "):
            line = f"- {line[2:].strip()}"
        lines.append(line.replace("**", "").replace("`", ""))
    return lines


def _wrap_pdf_line(line: str, width: int = 96) -> list[str]:
    if len(line) <= width:
        return [line]
    words = line.split()
    if not words:
        return [line[:width]]
    wrapped: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            wrapped.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        wrapped.append(current)
    return wrapped


def _basic_pdf_page_stream(
    page_lines: list[str],
    page_number: int,
    total_pages: int,
) -> bytes:
    commands = ["BT", "/F1 9 Tf", "48 800 Td", "12 TL"]
    for line in page_lines:
        commands.append(f"({_pdf_escape(line[:120])}) Tj")
        commands.append("T*")
    footer = (
        "PRELIMINARY - not for construction/permitting/procurement/legal reliance - "
        "licensed professional review "
        f"required - page {page_number} of {total_pages}"
    )
    commands.extend(
        [
            "ET",
            "BT",
            "/F1 7 Tf",
            "48 28 Td",
            f"({_pdf_escape(footer)}) Tj",
            "ET",
        ]
    )
    return "\n".join(commands).encode("latin-1", errors="replace")


def _render_with_basic_pdf(
    config: MountainRetreatConfig,
    markdown_path: Path,
    pdf_path: Path,
) -> None:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    volume_title = _volume_title(markdown_text, pdf_path.name)
    source_lines = [
        config.project.project_name,
        volume_title,
        f"Version: {config.project.version}",
        f"Status: {config.project.status}",
        f"Revision date: {config.project.revision_date}",
        _safety_notice(config),
        "Licensed professional review required before construction or permitting use.",
        "No fake stamps, fake signatures, or construction approvals are included.",
        "",
        *_plain_text_lines(markdown_text),
    ]
    wrapped_lines: list[str] = []
    for line in source_lines:
        wrapped_lines.extend(_wrap_pdf_line(line))

    lines_per_page = 61
    pages = [
        wrapped_lines[index : index + lines_per_page]
        for index in range(0, len(wrapped_lines), lines_per_page)
    ] or [["PRELIMINARY - licensed professional review required."]]

    objects: list[str | bytes] = [
        "",
        "<< /Type /Catalog /Pages 2 0 R >>",
        "",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_refs: list[str] = []
    total_pages = len(pages)
    for page_number, page_lines in enumerate(pages, start=1):
        stream = _basic_pdf_page_stream(page_lines, page_number, total_pages)
        content_object_number = len(objects)
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
        page_object_number = len(objects)
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {content_object_number} 0 R >>"
        )
        page_refs.append(f"{page_object_number} 0 R")

    objects[2] = f"<< /Type /Pages /Kids [{' '.join(page_refs)}] /Count {total_pages} >>"
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number in range(1, len(objects)):
        offsets.append(len(pdf))
        payload = objects[object_number]
        payload_bytes = (
            payload.encode("latin-1", errors="replace")
            if isinstance(payload, str)
            else payload
        )
        pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
        pdf.extend(payload_bytes)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    pdf_path.write_bytes(pdf)


def _render_with_available_backend(
    config: MountainRetreatConfig,
    markdown_path: Path,
    pdf_path: Path,
    template_dir: Path,
    use_weasyprint: bool,
) -> None:
    if use_weasyprint:
        try:
            _render_with_weasyprint(config, markdown_path, pdf_path, template_dir)
            return
        except Exception as exc:
            warn(
                f"WeasyPrint PDF rendering failed for {markdown_path.name}; "
                f"falling back to local PDF renderer: {exc}",
                stacklevel=2,
            )
    if REPORTLAB_AVAILABLE:
        _render_with_reportlab(config, markdown_path, pdf_path)
        return
    _render_with_basic_pdf(config, markdown_path, pdf_path)


def generate_pdf_volumes(
    config: MountainRetreatConfig,
    output_dir: Path,
    template_dir: Path = PDF_TEMPLATE_DIR,
    *,
    large_mode: bool = False,
    language: str | None = None,
) -> list[Path]:
    """Generate PDF volumes from Markdown sources and return their paths."""
    markdown_dir = output_dir / MARKDOWN_OUTPUT_DIR
    generate_markdown_volumes(config, output_dir, large_mode=large_mode, language=language)

    pdf_dir = output_dir / PDF_OUTPUT_DIR
    pdf_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    use_weasyprint = _weasyprint_available()

    for markdown_name, pdf_name in PDF_FILES.items():
        markdown_path = markdown_dir / markdown_name
        pdf_path = pdf_dir / pdf_name
        _render_with_available_backend(
            config,
            markdown_path,
            pdf_path,
            template_dir,
            use_weasyprint,
        )
        paths.append(pdf_path)
    return paths
