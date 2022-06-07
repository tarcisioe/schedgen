schedgen
========

![](https://github.com/tarcisioe/schedgen/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/tarcisioe/schedgen/branch/master/graph/badge.svg)](https://codecov.io/gh/tarcisioe/schedgen)

This is a schedule image generator for streamer teams!

Software Requirements
---------------------
- [poetry](https://python-poetry.org): package manager (it should install [summon](https://github.com/tarcisioe/summon-python) as dev dependency)

Usage
-----

```bash
schedgen [OPTION]... WEEKDAY STREAMER...
```

Generates schedule announcement for streamers (check [example](#example)).

Where OPTION may be one of following options:

| OPTION        | Description                                    |
|---------------|------------------------------------------------|
| --background  | Background image path                          |
| --config-file | config toml file path, default='schedgen.toml' |
| --output      | output png image path, default='generated.png' |

Pass WEEKDAY as a single-word string, like "tuesday" (don't include quotes)

Pass each STREAMER as follows: "NICKNAME;HH:MM", where NICKNAME is a streamer nickname, like "jo3star".
HH:MM will respect 24-hour format.

For example, for scheduling "jo3star" every tuesday 9pm pass STREAMER as "jo3star;21:00"


Example
-------

First of all, create a toml file (by default, schedgen will use `schedgen.toml`)
Below toml example uses `demo` directory resources

```toml
[schedgen.style]
weekday_font = { file = "iosevka-custom-regular.ttf", size = 50 }  # Day of Week's font (main header)
schedule_height = 458  # Result schedule image height, in px
schedule_y = 87  # from the top
weekday_y = 32  # from the top

[schedgen.entry_style]
stroke_width = 7
max_height = 120
min_spacing = 7  # minimum spacing between each entry
width = 285  # entry rectangle's width
stroke_color = { r=70, g=196, b=248 }  # similar to css border colour
url_font = { file="./demo/iosevka-custom-regular.ttf", size=16 }
time_font = { file="./demo/iosevka-custom-bold.ttf", size=20 }
url_position = { x=-50, y=0 }  # based off of the center of the rectangle
time_position = { x=-50, y=-25 }  # based off of the center of the rectangle
avatar_x = 80  # based off of the center of the rectangle
avatar_margin = 9  # margin around avatar

[schedgen.streamers]
'jo3star' = { avatar='./demo/joestar.png', service='twitch.tv' }
'king4rthur' = { avatar='./demo/monty-python.png', service='twitch.tv' }
```

Then, run `schedgen` such as the following example:

```
schedgen --background background.png --output tuesday.png tuesday "jo3star;12:00" "king4rthur;21:00"
```

and the result will be as follows.

![](./example.png)


Contributing
------------

- Fork this repo
- Clone your fork into local machine
- Run `poetry install` to install packages
- Run `poetry run pre-commit install` to install commit hooks
- Run `poetry shell` to get a poetry shell, in which you may run:
  - `summon test` for running tests
  - `summon format` for code formating
  - `summon lint` for code linting
  - `schedgen` for actually testing the tool
- Commit your changes (squashing before merging is quite a good idea =))
- Open a PR and request reviews

Contributors
------------
- @tarcisioe (barely tolerates the Jojo reference)
- @Lakshamana (responsible for Jojo reference)
