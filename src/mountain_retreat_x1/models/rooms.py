"""Room data sheet models."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel


class Room(StrictModel):
    """Room-level planning data."""

    code: str
    name: str
    floor: str
    zone: str
    length_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    area_m2: float = Field(gt=0)
    clear_height_m: float = Field(gt=0)
    function: str
    floor_finish: str
    wall_finish: str
    ceiling_finish: str
    heating_type: str
    ventilation_type: str
    window_area_m2: float = Field(ge=0)
    door_count: int = Field(ge=0)
    socket_count: int = Field(ge=0)
    light_point_count: int = Field(ge=0)
    plumbing_fixtures: list[str] = Field(default_factory=list)
    notes: str = ""

