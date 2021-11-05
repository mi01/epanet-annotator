import json
import math
from enum import Enum, unique
from typing import Final, List, Optional, Tuple

import wntr  # type: ignore


@unique
class OverlayType(str, Enum):
    HOUSE = "House"
    APARTMENTS = "Apartments"
    WHOLESALE = "Wholesale"
    COMMERCIAL = "Commercial"
    INSTITUTIONAL = "Institutional"
    INDUSTRIAL = "Industrial"
    OTHER = "Other"


class OverlayElement:
    def __init__(
        self, x: float, y: float, overlay_type: OverlayType = OverlayType.HOUSE
    ):
        self.x = x
        self.y = y
        self.type = overlay_type


class Network:
    SIZE_FACTOR: Final = 1000

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self.wn: Optional[wntr.network.model.WaterNetworkModel] = None
        self._net_offset_x: float = 0.0
        self._net_offset_y: float = 0.0
        self._net_height: float = 0.0
        self._net_width: float = 0.0
        self.elements: List[OverlayElement] = []

    def load_network(self, filename: str) -> bool:
        self.wn = wntr.network.WaterNetworkModel(filename)

        first_node = True
        for _, node in self.wn.nodes():
            (x, y) = node.coordinates
            if first_node:
                self._net_offset_x = x
                self._net_offset_y = y
                self._net_width = x
                self._net_height = y
                first_node = False
            if x < self._net_offset_x:
                self._net_offset_x = x
            if y < self._net_offset_y:
                self._net_offset_y = y
            if x > self._net_width:
                self._net_width = x
            if y > self._net_height:
                self._net_height = y

        self._net_width = self._net_width - self._net_offset_x
        self._net_height = self._net_height - self._net_offset_y
        if self._net_height > 0.0 and self._net_width > 0.0:
            return True
        return False

    def save_overlay_to_file(self, filename: str) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([e.__dict__ for e in self.elements], f, ensure_ascii=False)

    def load_overlay_from_file(self, filename: str) -> None:
        with open(filename, "r", encoding="utf-8") as f:
            self.elements = json.loads(
                f.read(),
                object_hook=lambda d: OverlayElement(
                    d["x"], d["y"], OverlayType(d["type"])
                ),
            )

    def get_dimensions(
        self, scale: float, offset_x: int, offset_y: int
    ) -> Tuple[int, int]:
        width = int(self.SIZE_FACTOR * scale + offset_x)
        height = int(
            (self.SIZE_FACTOR * self._net_height / self._net_width) * scale + offset_y
        )
        return (width, height)

    def _from_net_coords(self, net_x: float, net_y: float) -> Tuple[int, int]:
        x = (net_x - self._net_offset_x) / self._net_width
        y = (net_y - self._net_offset_y) / self._net_height
        dim_y = self.SIZE_FACTOR * self._net_height / self._net_width
        return (int(x * self.SIZE_FACTOR), int(dim_y - y * dim_y))

    def _to_net_coords(self, x: int, y: int) -> Tuple[float, float]:
        net_x = (x / self.SIZE_FACTOR) * self._net_width + self._net_offset_x
        dim_y = self.SIZE_FACTOR * self._net_height / self._net_width
        net_y = ((dim_y - y) / dim_y) * self._net_height + self._net_offset_y
        return (net_x, net_y)

    def add_overlay_element(self, x: int, y: int, overlay_type: OverlayType) -> None:
        (net_x, net_y) = self._to_net_coords(x, y)
        self.elements.append(OverlayElement(net_x, net_y, overlay_type))

    def draw(self, ctx, scale: float, offset_x: int, offset_y: int) -> None:
        ctx.set_source_rgb(0.0, 0.0, 0.7)
        ctx.set_line_width(0.4 * scale)

        for _, node in self.wn.nodes():  # type: ignore
            (x, y) = self._from_net_coords(node.coordinates[0], node.coordinates[1])
            ctx.arc(
                x * scale + offset_x, y * scale + offset_y, 4 * scale, 0, 2 * math.pi
            )
            ctx.fill()

        for _, pipe in self.wn.pipes():  # type: ignore
            (x1, y1) = self._from_net_coords(
                pipe.start_node.coordinates[0], pipe.start_node.coordinates[1]
            )
            (x2, y2) = self._from_net_coords(
                pipe.end_node.coordinates[0], pipe.end_node.coordinates[1]
            )
            ctx.move_to(x1 * scale + offset_x, y1 * scale + offset_y)
            ctx.line_to(x2 * scale + offset_x, y2 * scale + offset_y)
            ctx.stroke()

        for e in self.elements:
            if e.type == OverlayType.HOUSE:
                ctx.set_source_rgb(0.0, 0.7, 0.0)
            else:
                ctx.set_source_rgb(0.7, 0.0, 0.0)

            (x, y) = self._from_net_coords(e.x, e.y)
            ctx.arc(
                x * scale + offset_x, y * scale + offset_y, 4 * scale, 0, 2 * math.pi
            )
            ctx.fill()
