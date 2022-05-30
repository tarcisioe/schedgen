"""Main module."""
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, Iterator

import toml
import typer
from PIL import Image, ImageDraw, ImageFont


class Size(NamedTuple):
    """The size of a rectangle."""
    width: int
    height: int


class Position(NamedTuple):
    """A 2D cartesian position."""
    x: int
    y: int


class RGBColor(NamedTuple):
    """An RGB colorspace color."""
    r: int
    g: int
    b: int


@dataclass(frozen=True)
class ScheduleEntry:
    """An entry on the streamer schedule."""
    streaming_service_url: str
    username: str
    time: datetime.time


@dataclass
class EntryStyle:
    """The style of each entry on the schedule."""
    stroke_width: int
    max_height: int
    min_spacing: int
    width: int
    stroke_color: RGBColor
    url_font: ImageFont.FreeTypeFont
    time_font: ImageFont.FreeTypeFont
    url_position: Position
    time_position: Position
    avatar_x: int


@dataclass
class Drawer:
    """A helper object for aggregating an Image and an ImageDraw objects."""
    image: Image.Image
    drawer: ImageDraw.ImageDraw


Schedule = list[ScheduleEntry]
Avatars = dict[str, Path]


def translate(position: Position, delta: tuple[int, int]) -> Position:
    """Translate a position on space.

    Args:
        position: The base position.
        delta: How much to translate on each coordinate.

    Returns:
        A new position.
    """
    dx, dy = delta
    return Position(position.x + dx, position.y + dy)


def allocate_y_and_heights(
    *,
    total_height: int,
    max_entry_height: int,
    n_entries: int,
    min_spacing: int,
) -> Iterator[tuple[int, int]]:
    """Allocate space for each entry given some constraints.

    Args:
        total_height: How much vertical space is available (in pixels).
        max_entry_height: The maximum height for each schedule entry.
        n_entries: How many entries to distribute.
        min_spacing: The minimum spacing between each entry.

    Yields:
        Position and height for each entry.
    """
    n_spaces = n_entries - 1
    min_total_spacing = n_spaces * min_spacing
    max_total_entry_height = n_entries * max_entry_height

    if (remaining_space := total_height - max_total_entry_height) >= min_total_spacing:
        spacing = remaining_space // (n_spaces + 2)
        start = spacing
        entry_height = max_entry_height
    else:
        extra = min_total_spacing - remaining_space
        subtract_from_entry = extra // n_entries
        start = 0
        spacing = min_spacing
        entry_height = max_entry_height - subtract_from_entry

    current = start
    for _ in range(n_entries):
        yield current, entry_height
        current += spacing + entry_height


def draw_text_by_center(
    drawer: Drawer,
    text: str,
    *,
    position: Position,
    font: ImageFont.FreeTypeFont,
) -> None:
    """Draw text on an image given its top-center position.

    Args:
        drawer: The Drawer object for drawing.
        text: What to write.
        position: Where to position the text on the image.
        font: Which font to use to write.
    """
    width, _ = font.getsize_multiline(text)
    true_position = translate(position, Size(-width // 2, 0))

    drawer.drawer.text(true_position, text, font=font, align="center")


def draw_schedule_entry(
    drawer: Drawer,
    entry: ScheduleEntry,
    *,
    avatar_path: Path,
    position: Position,
    height: int,
    style: EntryStyle,
) -> None:
    """Draw a schedule entry given its top-left position.

    Args:
        drawer: The Drawer object for drawing.
        entry: The schedule entry to draw.
        avatar_path: Which avatar to use for this entry.
        position: Where to position the entry on the image.
        height: Which height should the entry have.
        style: The style to use for drawing the entry.
    """
    size = Size(style.width, height)

    drawer.drawer.rectangle(
        (position, translate(position, size)),
        outline=style.stroke_color,
        width=style.stroke_width,
    )

    center = translate(position, Size(size.width // 2, size.height // 2))

    time_absolute = translate(center, style.time_position)
    url_absolute = translate(center, style.url_position)

    draw_text_by_center(
        drawer,
        f"{entry.time.hour}:{entry.time.minute:02}",
        position=time_absolute,
        font=style.time_font,
    )
    draw_text_by_center(
        drawer,
        f"{entry.streaming_service_url}/\n{entry.username}".upper(),
        position=url_absolute,
        font=style.url_font,
    )

    with Image.open(avatar_path) as avatar:
        desired_height = height - 2 * style.stroke_width - 4
        proportion = desired_height / avatar.height
        desired_width = int(avatar.width * proportion)
        resized = avatar.resize((desired_height, desired_width))

        avatar_center_delta = Size(-resized.width // 2, -resized.height // 2)
        avatar_position = translate(center, avatar_center_delta)
        avatar_position = translate(avatar_position, Size(style.avatar_x, 0))
        drawer.image.paste(resized, avatar_position, mask=resized)


def draw_schedule(
    drawer: Drawer,
    schedule: Schedule,
    *,
    avatars: Avatars,
    position: Position,
    total_height: int,
    style: EntryStyle,
) -> None:
    """Draw a schedule on an image given its top-left position.

    Args:
        drawer: The Drawer object for drawing.
        schedule: The schedule to draw on the image.
        avatars: The avatar mapping for the streamers.
        position: Where to position the schedule on the image.
        total_height: The total height available to draw the schedule.
        entry_style: The style to use for each entry.
    """
    ys_and_heights = allocate_y_and_heights(
        total_height=total_height,
        max_entry_height=style.max_height,
        n_entries=len(schedule),
        min_spacing=style.min_spacing,
    )

    for entry, (y_delta, height) in zip(schedule, ys_and_heights):
        draw_schedule_entry(
            drawer,
            entry,
            position=translate(position, Size(0, y_delta)),
            height=height,
            style=style,
            avatar_path=avatars[entry.username],
        )


@dataclass
class DaySchedule:
    """The schedule to draw, given a weekday and the entries."""
    day: str
    schedule: Schedule


@dataclass
class AnnouncementStyle:
    """The style for the image."""
    weekday_font: ImageFont.FreeTypeFont
    schedule_y: int
    schedule_total_height: int
    entry_style: EntryStyle


def draw_announcement(
    base: Image.Image,
    day_schedule: DaySchedule,
    *,
    avatars: Avatars,
    style: AnnouncementStyle,
) -> None:
    """Draw the schedule announcement image.

    Args:
        base: The image to use as the background.
        day_schedule: The schedule information to draw.
        avatars: The avatar mapping for the streamers.
        style: The style to use for drawing the announcement.
    """
    drawer = Drawer(image=base, drawer=ImageDraw.Draw(base))

    draw_text_by_center(
        drawer,
        position=Position(base.width // 2, 10),
        text=day_schedule.day.upper(),
        font=style.weekday_font,
    )
    draw_schedule(
        drawer,
        day_schedule.schedule,
        avatars=avatars,
        position=Position(
            base.width // 2 - style.entry_style.width // 2, y=style.schedule_y
        ),
        total_height=style.schedule_total_height,
        style=style.entry_style,
    )


TomlDict = dict[str, Any]
TomlPath = list[str]


def load_font_from_toml(toml_dict: TomlDict) -> ImageFont.FreeTypeFont:
    """Load a FreeTypeFont from a toml-loaded dict."""
    return ImageFont.truetype(
        toml_dict["file"],
        size=toml_dict["size"],
    )


def load_position_from_toml(toml_dict: TomlDict) -> Position:
    """Load a Position from a toml-loaded dict."""
    return Position(
        x=toml_dict["x"],
        y=toml_dict["y"],
    )


def load_rgb_color_from_toml(toml_dict: TomlDict) -> RGBColor:
    """Load an RGBColor from a toml-loaded dict."""
    return RGBColor(
        r=toml_dict["r"],
        g=toml_dict["g"],
        b=toml_dict["b"],
    )


APP = typer.Typer()


@APP.command()
def main(
    weekday: str, streams: list[str], config_file: Path = Path("schedgen.toml"),
) -> None:
    """A schedule announcement generator for streamer teams."""
    with config_file.open(encoding='utf8') as f:
        config = toml.load(f)["schedgen"]

    raw_style = config["style"]
    raw_entry_style = config["entry_style"]

    style = AnnouncementStyle(
        weekday_font=load_font_from_toml(raw_style["weekday_font"]),
        schedule_total_height=raw_style["schedule_height"],
        schedule_y=raw_style["schedule_y"],
        entry_style=EntryStyle(
            stroke_width=raw_entry_style["stroke_width"],
            max_height=raw_entry_style["max_height"],
            min_spacing=raw_entry_style["min_spacing"],
            width=raw_entry_style["width"],
            stroke_color=load_rgb_color_from_toml(raw_entry_style["stroke_color"]),
            url_font=load_font_from_toml(raw_entry_style["url_font"]),
            time_font=load_font_from_toml(raw_entry_style["time_font"]),
            url_position=load_position_from_toml(raw_entry_style["url_position"]),
            time_position=load_position_from_toml(raw_entry_style["time_position"]),
            avatar_x=raw_entry_style["avatar_x"],
        ),
    )

    streamers = config["streamers"]
    avatars = {streamer: Path(info["avatar"]) for streamer, info in streamers.items()}

    raw_stream_entries = [e.split(";", maxsplit=1) for e in streams]
    stream_entries = [
        (username, time.split(":")) for username, time in raw_stream_entries
    ]

    schedule = [
        ScheduleEntry(
            streamers[username]["service"],
            username,
            datetime.time(hour=int(h), minute=int(m)),
        )
        for username, (h, m) in stream_entries
    ]

    day_schedule = DaySchedule(weekday, sorted(schedule, key=lambda e: e.time))

    with Image.open("background.png") as base:
        as_rgba = base.convert(mode="RGBA")
        draw_announcement(as_rgba, day_schedule, avatars=avatars, style=style)
        as_rgba.save("generated.png")
