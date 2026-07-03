"""GDP message types - mirrors GoPxLSdk GoGdpMsg classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import MessageType
from .kserializer import KSerializerReader, image_row_size, intensity_row_size

_COMMON_ATTRS = (
    "data_source_id_",
    "stamp_source_id_",
    "space_type",
    "arrayed_count",
    "arrayed_index",
    "data_set_id_",
    "is_last_msg_",
    "gdp_id",
)


@dataclass(slots=True)
class GoGdpMsg:
    msg_type: MessageType
    data_source_id_: str = ""
    stamp_source_id_: str = ""
    space_type: int = 0
    arrayed_count: int = 0
    arrayed_index: int = 0
    data_set_id_: int = 0
    is_last_msg_: bool = False
    gdp_id: int = 0
    raw: bytes = field(default_factory=bytes, repr=False)

    def type(self) -> MessageType:
        return self.msg_type

    def data_source_id(self) -> str:
        return self.data_source_id_

    def stamp_source_id(self) -> str:
        return self.stamp_source_id_

    def data_set_id(self) -> int:
        return self.data_set_id_

    def is_last_msg(self) -> bool:
        return self.is_last_msg_

    @staticmethod
    def parse_common(reader: KSerializerReader, msg_type: MessageType) -> GoGdpMsg:
        msg = GoGdpMsg(msg_type=msg_type)
        try:
            section = reader.section_u32()
            msg.space_type = section.read_u8()
            if section.read_u8() > 0:
                _skip_transform(section)
            if section.read_u8() > 0:
                _skip_bbox(section)
            msg.arrayed_count = section.read_u32()
            msg.arrayed_index = section.read_u32()
            ds_len = section.read_u16()
            msg.data_source_id_ = section.read_text(ds_len)
            st_len = section.read_u16()
            msg.stamp_source_id_ = section.read_text(st_len)
            msg.data_set_id_ = section.read_u64()
            msg.is_last_msg_ = section.read_u8() > 0
            msg.gdp_id = section.read_u16()
        except EOFError as exc:
            raise EOFError(
                f"Unexpected end of GDP data reading common header "
                f"(type={int(msg_type)}, remaining={reader.remaining()})"
            ) from exc
        return msg


def _apply_common(msg: GoGdpMsg, common: GoGdpMsg) -> None:
    for attr in _COMMON_ATTRS:
        setattr(msg, attr, getattr(common, attr))


@dataclass(slots=True)
class GoGdpSignal(GoGdpMsg):
    """Signals that data on a stream is invalidated."""


@dataclass(slots=True)
class GoGdpNull(GoGdpMsg):
    error_status: int = 0

    def error_status_value(self) -> int:
        return self.error_status


@dataclass(slots=True)
class GoGdpHealth(GoGdpMsg):
    payload_: bytes = field(default_factory=bytes, repr=False)

    def payload(self) -> bytes:
        return self.payload_


@dataclass(slots=True)
class GoGdpProfileUniform(GoGdpMsg):
    width_: int = 0
    intensity_width_: int = 0
    resolution_x: float = 0.0
    resolution_z: float = 0.0
    offset_x: float = 0.0
    offset_z: float = 0.0
    exposure: float = 0.0
    ranges_: list[int] = field(default_factory=list)
    intensities_: bytes = b""

    def width(self) -> int:
        return self.width_

    def ranges(self) -> list[int]:
        return self.ranges_

    def intensities(self) -> bytes:
        return self.intensities_


@dataclass(slots=True)
class GoGdpProfilePointCloud(GoGdpMsg):
    width_: int = 0
    intensity_width_: int = 0
    resolution_x: float = 0.0
    resolution_z: float = 0.0
    offset_x: float = 0.0
    offset_z: float = 0.0
    exposure: float = 0.0
    points_: list[tuple[int, int]] = field(default_factory=list)
    intensities_: bytes = b""

    def width(self) -> int:
        return self.width_

    def points(self) -> list[tuple[int, int]]:
        return self.points_

    def intensities(self) -> bytes:
        return self.intensities_


@dataclass(slots=True)
class GoGdpSurfaceUniform(GoGdpMsg):
    length_: int = 0
    width_: int = 0
    intensity_length_: int = 0
    intensity_width_: int = 0
    resolution: tuple[float, float, float] = (0.0, 0.0, 0.0)
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    surface_id: int = 0
    exposure: float = 0.0
    intensity_pixel_format: int = 0
    ranges_: list[int] = field(default_factory=list)
    intensities_: bytes = b""

    def length(self) -> int:
        return self.length_

    def width(self) -> int:
        return self.width_

    def ranges(self) -> list[int]:
        return self.ranges_

    def intensities(self) -> bytes:
        return self.intensities_


@dataclass(slots=True)
class GoGdpSurfacePointCloud(GoGdpMsg):
    length_: int = 0
    width_: int = 0
    intensity_length_: int = 0
    intensity_width_: int = 0
    resolution: tuple[float, float, float] = (0.0, 0.0, 0.0)
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    surface_id: int = 0
    exposure: float = 0.0
    is_adjacent: bool = False
    intensity_pixel_format: int = 0
    ranges_: list[tuple[int, int, int]] = field(default_factory=list)
    intensities_: bytes = b""

    def length(self) -> int:
        return self.length_

    def width(self) -> int:
        return self.width_

    def ranges(self) -> list[tuple[int, int, int]]:
        return self.ranges_

    def intensities(self) -> bytes:
        return self.intensities_


@dataclass(slots=True)
class GoGdpImage(GoGdpMsg):
    height_: int = 0
    width_: int = 0
    pixel_size: int = 0
    pixel_format: int = 0
    color_filter: int = 0
    exposure: float = 0.0
    flipped_x: bool = False
    flipped_y: bool = False
    column_based: bool = False
    # 2D resolution/offset (x, y) — present from GoPxL 1.3+
    resolution: tuple[float, float] = (0.0, 0.0)
    offset: tuple[float, float] = (0.0, 0.0)
    row_size_: int = 0
    pixels_: bytes = b""

    def height(self) -> int:
        return self.height_

    def width(self) -> int:
        return self.width_

    def row_size(self) -> int:
        return self.row_size_

    def pixels(self) -> bytes:
        return self.pixels_


@dataclass(slots=True)
class GdpSpot:
    slice: int = 0
    centre: int = 0


@dataclass(slots=True)
class GoGdpSpots(GoGdpMsg):
    point_count: int = 0
    exposure: float = 0.0
    column_based: bool = False
    slice_scale: float = 0.0
    slice_offset: float = 0.0
    center_scale: float = 0.0
    center_offset: float = 0.0
    max_slice_count: int = 0
    spot_center_min: int = 0
    spot_center_max: int = 0
    spots_: list[GdpSpot] = field(default_factory=list)

    def spots(self) -> list[GdpSpot]:
        return self.spots_


@dataclass(slots=True)
class MeshChannel:
    id: int = 0
    type: int = 0
    state: int = 0
    flag: int = 0
    allocated_count: int = 0
    used_count: int = 0
    data: list[Any] = field(default_factory=list)


@dataclass(slots=True)
class GoGdpMesh(GoGdpMsg):
    has_data: bool = False
    system_channel_count: int = 0
    max_user_channel_count: int = 0
    user_channel_count: int = 0
    channel_count: int = 0
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    range: tuple[float, float, float] = (0.0, 0.0, 0.0)
    channels_: list[MeshChannel] = field(default_factory=list)

    def channels(self) -> list[MeshChannel]:
        return self.channels_


@dataclass(slots=True)
class GoGdpStamp(GoGdpMsg):
    frame_index: int = 0
    timestamp: int = 0
    encoder: int = 0
    encoder_at_z: int = 0
    status: int = 0
    system_time_seconds: int = 0
    system_time_nanoseconds: int = 0


@dataclass(slots=True)
class GoGdpMeasurement(GoGdpMsg):
    value: float = 0.0
    decision: int = 0
    label_position: tuple[float, float, float] | None = None


@dataclass(slots=True)
class GoGdpString(GoGdpMsg):
    text: str = ""
    decision: int = 0
    label_position: tuple[float, float, float] | None = None


@dataclass(slots=True)
class GoPointSet:
    size: float = 0.0
    color: int = 0
    shape: int = 0
    points: list[tuple[float, float, float]] = field(default_factory=list)


@dataclass(slots=True)
class GoLineSet:
    width: float = 0.0
    color: int = 0
    has_start_point_arrow: bool = False
    has_end_point_arrow: bool = False
    points: list[tuple[float, float, float]] = field(default_factory=list)


@dataclass(slots=True)
class GoPlane:
    distance: float = 0.0
    normal: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(slots=True)
class GoRay:
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    direction: tuple[float, float, float] = (0.0, 0.0, 0.0)
    width: float = 0.0
    color: int = 0


@dataclass(slots=True)
class GoLabel:
    text: str = ""
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(slots=True)
class GoPosition:
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    type: int = 0


@dataclass(slots=True)
class GoGraphics:
    point_sets: list[GoPointSet] = field(default_factory=list)
    line_sets: list[GoLineSet] = field(default_factory=list)
    regions: list[dict[str, Any]] = field(default_factory=list)
    planes: list[GoPlane] = field(default_factory=list)
    rays: list[GoRay] = field(default_factory=list)
    labels: list[GoLabel] = field(default_factory=list)
    positions: list[GoPosition] = field(default_factory=list)


@dataclass(slots=True)
class GoGdpRendering(GoGdpMsg):
    graphics_: GoGraphics = field(default_factory=GoGraphics)

    def graphics(self) -> GoGraphics:
        return self.graphics_


@dataclass(slots=True)
class GoGdpFeaturePoint(GoGdpMsg):
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(slots=True)
class GoGdpFeatureLine(GoGdpMsg):
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    direction: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(slots=True)
class GoGdpFeaturePlane(GoGdpMsg):
    normal: tuple[float, float, float] = (0.0, 0.0, 0.0)
    distance_to_origin: float = 0.0


@dataclass(slots=True)
class GoGdpFeatureCircle(GoGdpMsg):
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    normal: tuple[float, float, float] = (0.0, 0.0, 0.0)
    radius: float = 0.0


_MESH_ID_VERTEX = 1
_MESH_ID_FACET = 2
_MESH_ID_VERTEX_TEXTURE = 3
_MESH_ID_FACET_NORMAL = 4
_MESH_ID_VERTEX_NORMAL = 5
_MESH_ID_VERTEX_CURVATURE = 6

# Mirrors GoGdpRendering::RegionType
_REGION_PROFILE_2D = 0
_REGION_3D = 1
_REGION_SURFACE_2D = 2


def parse_gdp_message(msg_type: int, packet: bytes) -> GoGdpMsg:
    body = packet[6:]
    reader = KSerializerReader(body)
    mtype = MessageType(msg_type)
    common = GoGdpMsg.parse_common(reader, mtype)

    if mtype == MessageType.SIGNAL:
        msg = GoGdpSignal(msg_type=mtype)
        _apply_common(msg, common)
        if reader.remaining() >= 2:
            reader.section_u16()
        msg.raw = packet
        return msg

    if mtype == MessageType.NULL_TYPE:
        msg = GoGdpNull(msg_type=mtype)
        _apply_common(msg, common)
        section = reader.section_u16()
        msg.error_status = section.read_i32()
        msg.raw = packet
        return msg

    if mtype == MessageType.HEALTH:
        msg = GoGdpHealth(msg_type=mtype)
        _apply_common(msg, common)
        if reader.remaining() > 0:
            msg.payload_ = reader.read_bytes(reader.remaining())
        msg.raw = packet
        return msg

    if mtype == MessageType.UNIFORM_PROFILE:
        # u16 attribute section then ranges/intensities (may be in-section or parent).
        msg = GoGdpProfileUniform(msg_type=mtype)
        _apply_common(msg, common)
        section, parent = _split_u16_section(reader, "uniform profile")
        _require_bytes(section, 44, "uniform profile attributes")
        msg.width_ = section.read_u32()
        msg.intensity_width_ = section.read_u32()
        msg.resolution_x = section.read_f64()
        msg.resolution_z = section.read_f64()
        msg.offset_x = section.read_f64()
        msg.offset_z = section.read_f64()
        msg.exposure = section.read_f32()
        payload = _join_readers(section, parent)
        msg.ranges_ = _read_i16_payload(
            payload, msg.width_, "uniform profile ranges", width=msg.width_
        )
        msg.intensities_ = _read_optional_u8_payload(payload, msg.intensity_width_)
        msg.raw = packet
        return msg

    if mtype == MessageType.PROFILE_POINT_CLOUD:
        msg = GoGdpProfilePointCloud(msg_type=mtype)
        _apply_common(msg, common)
        section, parent = _split_u16_section(reader, "profile point-cloud")
        _require_bytes(section, 44, "profile point-cloud attributes")
        msg.width_ = section.read_u32()
        msg.intensity_width_ = section.read_u32()
        msg.resolution_x = section.read_f64()
        msg.resolution_z = section.read_f64()
        msg.offset_x = section.read_f64()
        msg.offset_z = section.read_f64()
        msg.exposure = section.read_f32()
        payload = _join_readers(section, parent)
        raw = _read_i16_payload(
            payload, msg.width_ * 2, "profile point-cloud ranges", width=msg.width_
        )
        msg.points_ = [(raw[i], raw[i + 1]) for i in range(0, len(raw), 2)]
        msg.intensities_ = _read_optional_u8_payload(payload, msg.intensity_width_)
        msg.raw = packet
        return msg

    if mtype == MessageType.UNIFORM_SURFACE:
        # Attribute section holds base attrs + optional intensity format; payload follows.
        msg = GoGdpSurfaceUniform(msg_type=mtype)
        _apply_common(msg, common)
        section, parent = _split_u16_section(reader, "uniform surface")
        _read_surface_base(section, msg)
        msg.intensity_pixel_format = _read_intensity_pixel_format(
            section, msg.intensity_length_, msg.intensity_width_
        )
        payload = _join_readers(section, parent)
        count = msg.length_ * msg.width_
        msg.ranges_ = _read_i16_payload(
            payload, count, "surface uniform ranges",
            length=msg.length_, width=msg.width_,
        )
        _read_intensity_payload(payload, msg, "surface uniform intensity")
        msg.raw = packet
        return msg

    if mtype == MessageType.SURFACE_POINT_CLOUD:
        msg = GoGdpSurfacePointCloud(msg_type=mtype)
        _apply_common(msg, common)
        section, parent = _split_u16_section(reader, "surface point-cloud")
        _read_surface_base(section, msg)
        msg.is_adjacent = section.read_u8() > 0
        msg.intensity_pixel_format = _read_intensity_pixel_format(
            section, msg.intensity_length_, msg.intensity_width_
        )
        payload = _join_readers(section, parent)
        count = msg.length_ * msg.width_ * 3
        raw = _read_i16_payload(
            payload, count, "surface point-cloud ranges",
            length=msg.length_, width=msg.width_,
        )
        msg.ranges_ = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
        _read_intensity_payload(payload, msg, "surface point-cloud intensity")
        msg.raw = packet
        return msg

    if mtype == MessageType.IMAGE:
        # Wire layout matches GoGdpImage::Deserialize:
        # u16 section: height, width, pixelSize, pixelFormat, colorFilter,
        # reserved16, exposure, flippedX/Y, columnBased, optional res/offset (x,y).
        # Pixel bytes follow the section on the parent serializer.
        msg = GoGdpImage(msg_type=mtype)
        _apply_common(msg, common)
        section = reader.section_u16()
        msg.height_ = section.read_u32()
        msg.width_ = section.read_u32()
        msg.pixel_size = section.read_u32()
        msg.pixel_format = section.read_i32()
        msg.color_filter = section.read_i32()
        section.read_u16()  # reserved
        msg.exposure = section.read_f32()
        msg.flipped_x = section.read_u8() > 0
        msg.flipped_y = section.read_u8() > 0
        msg.column_based = section.read_u8() > 0
        # Optional fields added in GoPxL 1.3 (2D resolution/offset).
        if section.remaining() >= 32:
            msg.resolution = (section.read_f64(), section.read_f64())
            msg.offset = (section.read_f64(), section.read_f64())
        msg.row_size_ = image_row_size(
            msg.width_, msg.pixel_size, msg.color_filter, msg.pixel_format
        )
        bytes_needed = msg.height_ * msg.row_size_
        if reader.remaining() < bytes_needed:
            raise EOFError(
                f"Insufficient bytes for image pixels: need {bytes_needed}, "
                f"have {reader.remaining()}"
            )
        msg.pixels_ = reader.read_u8_array(bytes_needed)
        msg.raw = packet
        return msg

    if mtype == MessageType.SPOTS:
        msg = GoGdpSpots(msg_type=mtype)
        _apply_common(msg, common)
        section = reader.section_u16()
        msg.point_count = section.read_u32()
        msg.exposure = section.read_f32()
        msg.column_based = section.read_u8() > 0
        msg.slice_scale = section.read_f32()
        msg.slice_offset = section.read_f32()
        msg.center_scale = section.read_f32()
        msg.center_offset = section.read_f32()
        msg.max_slice_count = section.read_u32()
        msg.spot_center_min = section.read_u32()
        msg.spot_center_max = section.read_u32()
        for _ in range(msg.point_count):
            msg.spots_.append(GdpSpot(slice=reader.read_u16(), centre=reader.read_u32()))
        msg.raw = packet
        return msg

    if mtype == MessageType.MESH:
        msg = GoGdpMesh(msg_type=mtype)
        _apply_common(msg, common)
        section = reader.section_u16()
        msg.has_data = section.read_u8() > 0
        msg.system_channel_count = section.read_u32()
        msg.max_user_channel_count = section.read_u32()
        msg.user_channel_count = section.read_u32()
        msg.channel_count = section.read_u32()
        msg.offset = (section.read_f64(), section.read_f64(), section.read_f64())
        msg.range = (section.read_f64(), section.read_f64(), section.read_f64())
        for _ in range(msg.channel_count):
            ch_section = reader.section_u16()
            channel = MeshChannel(
                id=ch_section.read_u32(),
                type=ch_section.read_u32(),
                state=ch_section.read_i32(),
                flag=ch_section.read_u32(),
                allocated_count=ch_section.read_u32(),
                used_count=ch_section.read_u32(),
            )
            channel.data = _read_mesh_channel(reader, channel.id, channel.allocated_count)
            msg.channels_.append(channel)
        msg.raw = packet
        return msg

    if mtype == MessageType.STAMP:
        msg = GoGdpStamp(msg_type=mtype)
        _apply_common(msg, common)
        section = reader.section_u16()
        msg.frame_index = section.read_u64()
        msg.timestamp = section.read_u64()
        msg.encoder = int(section.read_u64())
        msg.encoder_at_z = int(section.read_u64())
        msg.status = section.read_u64()
        msg.system_time_seconds = section.read_u64()
        msg.system_time_nanoseconds = section.read_u64()
        msg.raw = packet
        return msg

    if mtype == MessageType.MEASUREMENT:
        msg = GoGdpMeasurement(msg_type=mtype)
        _apply_common(msg, common)
        msg.value = reader.read_f64()
        msg.decision = reader.read_u8()
        if reader.remaining() >= 24:
            msg.label_position = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.raw = packet
        return msg

    if mtype == MessageType.STRING:
        msg = GoGdpString(msg_type=mtype)
        _apply_common(msg, common)
        strlen = reader.read_u32()
        msg.text = reader.read_text(strlen)
        msg.decision = reader.read_u8()
        if reader.remaining() >= 24:
            msg.label_position = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.raw = packet
        return msg

    if mtype == MessageType.RENDERING:
        msg = GoGdpRendering(msg_type=mtype)
        _apply_common(msg, common)
        msg.graphics_ = _parse_graphics(reader)
        msg.raw = packet
        return msg

    if mtype == MessageType.POINT_FEATURE:
        msg = GoGdpFeaturePoint(msg_type=mtype)
        _apply_common(msg, common)
        msg.position = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.raw = packet
        return msg

    if mtype == MessageType.LINE_FEATURE:
        msg = GoGdpFeatureLine(msg_type=mtype)
        _apply_common(msg, common)
        msg.position = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.direction = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.raw = packet
        return msg

    if mtype == MessageType.PLANE_FEATURE:
        msg = GoGdpFeaturePlane(msg_type=mtype)
        _apply_common(msg, common)
        msg.normal = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.distance_to_origin = reader.read_f64()
        msg.raw = packet
        return msg

    if mtype == MessageType.CIRCLE_FEATURE:
        msg = GoGdpFeatureCircle(msg_type=mtype)
        _apply_common(msg, common)
        msg.center = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.normal = (reader.read_f64(), reader.read_f64(), reader.read_f64())
        msg.radius = reader.read_f64()
        msg.raw = packet
        return msg

    common.raw = packet
    return common


def _read_surface_base(section: KSerializerReader, msg: GoGdpSurfaceUniform | GoGdpSurfacePointCloud) -> None:
    _require_bytes(section, 72, "surface attributes")
    msg.length_ = section.read_u32()
    msg.width_ = section.read_u32()
    msg.intensity_length_ = section.read_u32()
    msg.intensity_width_ = section.read_u32()
    msg.resolution = (section.read_f64(), section.read_f64(), section.read_f64())
    msg.offset = (section.read_f64(), section.read_f64(), section.read_f64())
    msg.surface_id = section.read_u32()
    msg.exposure = section.read_f32()


def _read_intensity_pixel_format(section: KSerializerReader, intensity_length: int, intensity_width: int) -> int:
    if intensity_length <= 0 or intensity_width <= 0:
        return 0
    if section.remaining() >= 4:
        return section.read_i32()
    return 1  # Greyscale_8BPP legacy fallback


def _require_bytes(reader: KSerializerReader, count: int, label: str) -> None:
    if reader.remaining() < count:
        raise EOFError(
            f"Unexpected end of GDP data reading {label}: "
            f"need {count} bytes, have {reader.remaining()}"
        )


def _split_u16_section(
    reader: KSerializerReader, label: str
) -> tuple[KSerializerReader, KSerializerReader]:
    """Split a u16-sized attribute section from the remainder of the frame.

    If the section size claims more bytes than remain, consume all remaining
    bytes as the section (some firmware packs payload into the section size).
    """
    if reader.remaining() < 2:
        raise EOFError(
            f"Unexpected end of GDP data reading {label} section size "
            f"(have {reader.remaining()} bytes)"
        )
    size = reader.read_u16()
    content_len = max(size - 2, 0)
    avail = reader.remaining()
    take = min(content_len, avail)
    section_bytes = reader.read_bytes(take)
    parent_bytes = reader.read_bytes(reader.remaining())
    return KSerializerReader(section_bytes), KSerializerReader(parent_bytes)


def _join_readers(
    section: KSerializerReader, parent: KSerializerReader
) -> KSerializerReader:
    """Concatenate unread section bytes with parent-frame bytes as payload."""
    chunks = b""
    if section.remaining() > 0:
        chunks += section.read_bytes(section.remaining())
    if parent.remaining() > 0:
        chunks += parent.read_bytes(parent.remaining())
    return KSerializerReader(chunks)


def _read_i16_payload(
    reader: KSerializerReader,
    count: int,
    label: str,
    **dims: int,
) -> list[int]:
    if count <= 0:
        return []
    needed = count * 2
    avail = reader.remaining()
    if avail < needed:
        # Accept partial payloads (seen on profile outputs while in surface mode).
        if avail >= 2 and avail % 2 == 0:
            return reader.read_i16_array(avail // 2)
        detail = ", ".join(f"{k}={v}" for k, v in dims.items())
        raise EOFError(
            f"Unexpected end of GDP data reading {label}: "
            f"need {needed} bytes, have {avail}"
            + (f" ({detail})" if detail else "")
        )
    return reader.read_i16_array(count)


def _read_optional_u8_payload(reader: KSerializerReader, count: int) -> bytes:
    """Read up to *count* bytes; trailing intensity is omitted if the packet is short."""
    if count <= 0:
        return b""
    avail = reader.remaining()
    if avail <= 0:
        return b""
    return reader.read_u8_array(min(count, avail))


def _read_intensity_payload(
    reader: KSerializerReader,
    msg: GoGdpSurfaceUniform | GoGdpSurfacePointCloud,
    label: str,
) -> None:
    if msg.intensity_length_ <= 0 or msg.intensity_width_ <= 0:
        return
    row = intensity_row_size(msg.intensity_width_, msg.intensity_pixel_format)
    needed = msg.intensity_length_ * row
    avail = reader.remaining()
    if avail < needed:
        # Fall back to 1 byte/pixel (legacy native intensity) if format was misread.
        native = msg.intensity_length_ * msg.intensity_width_
        if avail >= native:
            needed = native
            msg.intensity_pixel_format = 1
        elif avail > 0:
            needed = avail
        else:
            raise EOFError(
                f"Unexpected end of GDP data reading {label}: "
                f"need {needed} bytes (length={msg.intensity_length_}, "
                f"width={msg.intensity_width_}, format={msg.intensity_pixel_format}), "
                f"have {avail}"
            )
    msg.intensities_ = reader.read_u8_array(needed)


def _read_mesh_channel(reader: KSerializerReader, channel_id: int, count: int) -> list[Any]:
    if count <= 0:
        return []
    if channel_id in (_MESH_ID_VERTEX, _MESH_ID_FACET_NORMAL, _MESH_ID_VERTEX_NORMAL):
        return [(reader.read_f32(), reader.read_f32(), reader.read_f32()) for _ in range(count)]
    if channel_id == _MESH_ID_FACET:
        return [(reader.read_u32(), reader.read_u32(), reader.read_u32()) for _ in range(count)]
    if channel_id == _MESH_ID_VERTEX_CURVATURE:
        return [reader.read_f32() for _ in range(count)]
    if channel_id == _MESH_ID_VERTEX_TEXTURE:
        return [reader.read_u8() for _ in range(count)]
    return [reader.read_u8() for _ in range(count)]


def _parse_graphics(reader: KSerializerReader) -> GoGraphics:
    graphics = GoGraphics()
    section = reader.section_u16()
    point_count = section.read_u16()
    line_count = section.read_u16()
    region_count = section.read_u16()
    plane_count = section.read_u16()
    ray_count = section.read_u16()
    label_count = section.read_u16()
    position_count = section.read_u16()

    for _ in range(point_count):
        ps = GoPointSet()
        ps_section = reader.section_u16()
        ps.size = ps_section.read_f32()
        ps.color = ps_section.read_u32()
        ps.shape = ps_section.read_i32()
        n = ps_section.read_u16()
        for _ in range(n):
            ps.points.append((reader.read_f32(), reader.read_f32(), reader.read_f32()))
        graphics.point_sets.append(ps)

    for _ in range(line_count):
        ls = GoLineSet()
        ls_section = reader.section_u16()
        ls.width = ls_section.read_f32()
        ls.color = ls_section.read_u32()
        ls.has_start_point_arrow = ls_section.read_u8() > 0
        ls.has_end_point_arrow = ls_section.read_u8() > 0
        n = ls_section.read_u16()
        for _ in range(n):
            ls.points.append((reader.read_f32(), reader.read_f32(), reader.read_f32()))
        graphics.line_sets.append(ls)

    for _ in range(region_count):
        region_type = reader.read_u8()
        if region_type == _REGION_PROFILE_2D:
            sec = reader.section_u16()
            graphics.regions.append(
                {
                    "type": region_type,
                    "x": sec.read_f64(),
                    "z": sec.read_f64(),
                    "width": sec.read_f64(),
                    "height": sec.read_f64(),
                    "angleY": sec.read_f64(),
                }
            )
        elif region_type == _REGION_SURFACE_2D:
            sec = reader.section_u16()
            graphics.regions.append(
                {
                    "type": region_type,
                    "x": sec.read_f64(),
                    "y": sec.read_f64(),
                    "width": sec.read_f64(),
                    "length": sec.read_f64(),
                    "angleZ": sec.read_f64(),
                }
            )
        elif region_type == _REGION_3D:
            sec = reader.section_u16()
            graphics.regions.append(
                {
                    "type": region_type,
                    "x": sec.read_f64(),
                    "y": sec.read_f64(),
                    "z": sec.read_f64(),
                    "width": sec.read_f64(),
                    "length": sec.read_f64(),
                    "height": sec.read_f64(),
                    "angleZ": sec.read_f64(),
                }
            )

    for _ in range(plane_count):
        sec = reader.section_u16()
        graphics.planes.append(
            GoPlane(
                distance=sec.read_f32(),
                normal=(sec.read_f32(), sec.read_f32(), sec.read_f32()),
            )
        )

    for _ in range(ray_count):
        sec = reader.section_u16()
        graphics.rays.append(
            GoRay(
                position=(sec.read_f32(), sec.read_f32(), sec.read_f32()),
                direction=(sec.read_f32(), sec.read_f32(), sec.read_f32()),
                width=sec.read_f32(),
                color=sec.read_u32(),
            )
        )

    for _ in range(label_count):
        sec = reader.section_u16()
        length = sec.read_u16()
        text = sec.read_text(length) if length else ""
        graphics.labels.append(
            GoLabel(
                text=text,
                position=(sec.read_f64(), sec.read_f64(), sec.read_f64()),
            )
        )

    for _ in range(position_count):
        sec = reader.section_u16()
        graphics.positions.append(
            GoPosition(
                position=(sec.read_f64(), sec.read_f64(), sec.read_f64()),
                type=sec.read_u8(),
            )
        )

    return graphics


def _skip_transform(section: KSerializerReader) -> None:
    # GoGdpTransform: 3x4 matrix of f32 (xx..zt), implicit last row [0,0,0,1].
    for _ in range(12):
        section.read_f32()


def _skip_bbox(section: KSerializerReader) -> None:
    # GoGdpBoundingBox: x,y,z,width,length,height as f32 (not f64).
    for _ in range(6):
        section.read_f32()
