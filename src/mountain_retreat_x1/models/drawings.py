"""Drawing register models."""

from mountain_retreat_x1.models.base import StrictModel


class Drawing(StrictModel):
    """Generated schematic drawing metadata."""

    code: str
    title: str
    discipline: str
    scale: str
    output_file: str
    status: str
    notes: str = ""

