import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Iterator, overload

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

    style = AnnouncementStyle(
        weekday_font=ImageFont.truetype("Hack-Bold.ttf", size=50),
        schedule_total_height=458,
        schedule_y=87,
        entry_style=EntryStyle(
            stroke_width=7,
            max_height=123,
            min_spacing=7,
            width=285,
            stroke_color=RGBColor(238, 17, 75),
            url_font=ImageFont.truetype("Hack-Regular.ttf", size=16),
            time_font=ImageFont.truetype("Hack-Bold.ttf", size=20),
            url_position=Position(-50, 0),
            time_position=Position(-50, -20),
            avatar_x=80,
        ),
    )

    with Image.open("background.png") as base:
        as_rgba = base.convert(mode='RGBA')
        draw_announcement(as_rgba, day_schedule, avatars=avatars, style=style)
        as_rgba.save("generated.png")


if __name__ == "__main__":
    main()
