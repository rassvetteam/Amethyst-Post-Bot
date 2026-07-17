<div align="center">

# Amethyst Post Bot

[![Stars](https://img.shields.io/github/stars/rassvetteam/Amethyst-Post-Bot?style=flat&logo=github)](https://github.com/rassvetteam/Amethyst-Post-Bot/stargazers)
[![Forks](https://img.shields.io/github/forks/rassvetteam/Amethyst-Post-Bot?style=flat&logo=github)](https://github.com/rassvetteam/Amethyst-Post-Bot/network/members)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://t.me/amthpostbot)
[![Markdown](https://img.shields.io/badge/input-Markdown%20%2F%20.md-purple)](#post-format)
[![Rich Posts](https://img.shields.io/badge/output-Rich%20Markdown-8A2BE2)](#features)
[![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-lightgrey)](LICENSE)
[![Free](https://img.shields.io/badge/use-free%20%26%20non--commercial-success)](#license)

Free Telegram bot that turns Markdown (or a `.md` file) into Telegram Rich Markdown posts — no subscriptions, no ads, private chats only.

**Bot:** [@amthpostbot](https://t.me/amthpostbot)

</div>

---

## Features

- Free to use without subscriptions, payments, accounts, or promotional steps.
- Accepts Markdown as a Telegram message or a UTF-8 `.md` file.
- Converts `details`, `collage`, and `slideshow` directives into Telegram Rich Markdown blocks.
- Validates Markdown and HTML media URLs before sending.
- Supports an optional SOCKS5/SOCKS5H proxy.
- Provides an example through `/example` and the **Show example** button.

## Examples
<img width="506" height="629" alt="изображение" src="https://github.com/user-attachments/assets/aa85dd3b-7934-4c95-b971-530d2cb420fb" />


## Requirements

- Python 3.10 or newer.
- A Telegram bot token from BotFather.
- A Bot API endpoint that supports `sendRichMessage`.

The bot does not need to be an administrator or member of any channel or group.

## Quick Start

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

3. Set your bot token in `.env`:

   ```env
   TELEGRAM_BOT_TOKEN=123456789:your_real_bot_token
   TELEGRAM_PROXY_URL=
   ```

4. Start the bot:

   ```bash
   python main.py
   ```

5. Open the bot in Telegram and send `/start`.

## Configuration

The bot reads `.env` from the project directory by default. Real secrets must stay in `.env`; Git ignores this file.

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from BotFather. |
| `BOT_API_BASE` | No | Bot API base URL. Defaults to `https://api.telegram.org`. |
| `TELEGRAM_PROXY_URL` | No | Optional SOCKS5/SOCKS5H proxy URL. |
| `BOT_ENV_FILE` | No | Optional path to a different environment file. |

Environment variables take priority over values from `.env`.

## Commands

- `/start` — displays the format guide and example button.
- `/help` — displays the format guide and example button.
- `/example` — sends the source of `sample_post.md` followed by the formatted rich post.

Messages from groups, channels, and other non-private chats are ignored to prevent accidental output outside the user's private conversation.

## Post Format

Send standard Markdown directly or upload a UTF-8 `.md` file. The bot replies with line-based validation errors when the content is invalid.

Details block:

```md
:::details FAQ
Hidden content goes here.
:::
```

<img width="505" height="123" alt="изображение" src="https://github.com/user-attachments/assets/e975577f-6e3f-4d3f-9a88-01b70dbb629b" />


Expanded by default:

```md
:::details open FAQ
This content starts open.
:::
```

Collage:

```md
:::collage
![](https://example.com/photo-1.jpg "First caption")
![](https://example.com/photo-2.jpg "Second caption")
:::
```

<img width="506" height="259" alt="изображение" src="https://github.com/user-attachments/assets/bcb74cc8-1b89-461c-b9d6-04bebff5e80c" />

Slideshow:

```md
:::slideshow
![](https://example.com/slide-1.jpg)
![](https://example.com/slide-2.jpg)
:::
```

<img width="502" height="491" alt="изображение" src="https://github.com/user-attachments/assets/1e1ee592-1bdc-4248-82c4-d63423249826" />

Media links in Markdown images and HTML `src` attributes must start with `http://` or `https://`. Telegram cannot fetch local file paths.

See [sample_post.md](sample_post.md) for a complete example.

## License

This project is provided for non-commercial use under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license. See [LICENSE](LICENSE).

## Release Checklist

- Keep `.env` out of Git and use `.env.example` for public configuration examples.
- Rotate any bot token that was ever committed or shared publicly.
- Check syntax with `python -m py_compile main.py`.
- Test `/start`, `/help`, `/example`, a text post, a `.md` upload, and an invalid media URL.
