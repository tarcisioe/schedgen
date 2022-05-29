import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple, Iterator, overload

import toml
from PIL import Image, ImageDraw, ImageFont


class Size(NamedTuple):
    width: int
    height: int


class Position(NamedTuple):
    x: int
    y: int


class RGBColor(NamedTuple):
    r: int
    g: int
    b: int


@dataclass(frozen=True)
class ScheduleEntry:
    streaming_service_url: str
    username: str
    time: datetime.time


@dataclass
class EntryStyle:
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
    image: Image.Image
    drawer: ImageDraw.ImageDraw


Schedule = list[ScheduleEntry]
Avatars = dict[str, Path]

def translate(position: Position, delta: tuple[int, int]) -> Position:
    dx, dy = delta
    return Position(position.x + dx, position.y + dy)


def allocate_y_and_heights(
    *,
    total_height: int,
    max_entry_height: int,
    n_entries: int,
    min_spacing: int,
) -> Iterator[tuple[int, int]]:
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
    for i in range(n_entries):
        yield current, entry_height
        current += spacing + entry_height


def draw_text_by_center(
    drawer: Drawer,
    text: str,
    *,
    position: Position,
    font: ImageFont.FreeTypeFont,
) -> None:
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
        desired_height = height - 2*style.stroke_width - 4
        proportion = desired_height/avatar.height
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
    day: str
    schedule: Schedule


@dataclass
class AnnouncementStyle:
    weekday_font: ImageFont.FreeTypeFont
    schedule_y: int
    schedule_total_height: int
    entry_style: EntryStyle


def draw_announcement(
    base: Image.Image, day_schedule: DaySchedule, *, avatars: Avatars, style: AnnouncementStyle
) -> None:
    drawer = Drawer(
        image=base,
        drawer=ImageDraw.Draw(base)
    )

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
    return ImageFont.truetype(
        toml_dict['file'],
        size = toml_dict['size'],
    )


def load_position_from_toml(toml_dict: TomlDict) -> Position:
    return Position(
        x=toml_dict['x'],
        y=toml_dict['y'],
    )


def load_rgb_color_from_toml(toml_dict: TomlDict) -> RGBColor:
    return RGBColor(
        r=toml_dict['r'],
        g=toml_dict['g'],
        b=toml_dict['b'],
    )


def main() -> None:
    avatars = {
        'vinnydays': Path('./streamer.png'),
        'ponzuzuju': Path('./streamer.png'),
        'gamerdeesquerda': Path('./streamer.png'),
        '0froggy': Path('./streamer.png'),
    }

    schedule = [
        ScheduleEntry("twitch.tv", "vinnydays", datetime.time(hour=13, minute=00)),
        ScheduleEntry("twitch.tv", "ponzuzuju", datetime.time(hour=17, minute=00)),
        ScheduleEntry(
            "twitch.tv", "gamerdeesquerda", datetime.time(hour=18, minute=00)
        ),
        ScheduleEntry("twitch.tv", "0froggy", datetime.time(hour=21, minute=00)),
    ]

    day_schedule = DaySchedule("quarta", schedule)

    with open('style.toml') as f:
        raw_announcement_style = toml.load(f)['schedgen']

    raw_style = raw_announcement_style['style']
    raw_entry_style = raw_announcement_style['entry_style']

    style = AnnouncementStyle(
        weekday_font=load_font_from_toml(raw_style['weekday_font']),
        schedule_total_height=raw_style['schedule_height'],
        schedule_y=raw_style['schedule_y'],
        entry_style=EntryStyle(
            stroke_width=raw_entry_style['stroke_width'],
            max_height=raw_entry_style['max_height'],
            min_spacing=raw_entry_style['min_spacing'],
            width=raw_entry_style['width'],
            stroke_color=load_rgb_color_from_toml(raw_entry_style['stroke_color']),
            url_font=load_font_from_toml(raw_entry_style['url_font']),
            time_font=load_font_from_toml(raw_entry_style['time_font']),
            url_position=load_position_from_toml(raw_entry_style['url_position']),
            time_position=load_position_from_toml(raw_entry_style['time_position']),
            avatar_x=raw_entry_style['avatar_x'],
        ),
    )

    with Image.open("background.png") as base:
        as_rgba = base.convert(mode='RGBA')
        draw_announcement(as_rgba, day_schedule, avatars=avatars, style=style)
        as_rgba.save("generated.png")


if __name__ == "__main__":
    main()
