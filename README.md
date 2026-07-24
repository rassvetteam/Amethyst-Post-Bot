<div align="center">

# Rich Post Bot

[![Stars](https://img.shields.io/github/stars/rassvetteam/Rich-Post-Bot?style=for-the-badge&logo=github)](https://github.com/rassvetteam/Rich-Post-Bot/stargazers)
[![Forks](https://img.shields.io/github/forks/rassvetteam/Rich-Post-Bot?style=for-the-badge&logo=github)](https://github.com/rassvetteam/Rich-Post-Bot/network/members)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey?style=for-the-badge)](LICENSE)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://t.me/amthpostbot)
[![Markdown](https://img.shields.io/badge/input-Markdown%20%2F%20.md-7B68EE?style=flat-square)](#post-format)
[![Rich Posts](https://img.shields.io/badge/output-Rich%20Markdown-8A2BE2?style=flat-square)](#features)
[![Free](https://img.shields.io/badge/use-free%20%26%20non--commercial-2ea44f?style=flat-square)](#license)
[![Proxy](https://img.shields.io/badge/SOCKS5-optional-informational?style=flat-square)](#configuration)

Free Telegram bot that turns Markdown (or a `.md` file) into Telegram **Rich Markdown** posts — no subscriptions, no ads, private chats only.

<br/>

**Bot:** [@amthpostbot](https://t.me/amthpostbot) · **[Features](#features)** · **[Quick Start](#quick-start)** · **[Post Format](#post-format)**

</div>

---

> [!IMPORTANT]
> Non-commercial project under **CC BY-NC-SA 4.0**. Free to use for personal / non-commercial purposes — see [LICENSE](LICENSE).

> [!TIP]
> Open [@amthpostbot](https://t.me/amthpostbot), send `/start`, then try `/example` or the **Show example** button to see a finished rich post.

## Features

- Free to use — no subscriptions, payments, accounts, or promo steps
- Accepts Markdown as a Telegram message or a UTF-8 `.md` file
- Converts `details`, `collage`, and `slideshow` into Telegram Rich Markdown blocks
- Validates Markdown and HTML media URLs before sending
- Optional SOCKS5 / SOCKS5H proxy
- Built-in example via `/example` and the **Show example** button

## Examples

<p align="center">
  <img width="506" height="629" alt="Example rich post" src="https://github.com/user-attachments/assets/aa85dd3b-7934-4c95-b971-530d2cb420fb" />
</p>

## Requirements

- Python **3.10** or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Bot API endpoint that supports `sendRichMessage`

> [!NOTE]
> The bot does **not** need to be an administrator or member of any channel or group. It works in **private chats** only.

## Quick Start

1. Install dependencies:

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

> [!WARNING]
> Never commit a real bot token. Keep secrets in `.env` (Git-ignored). If a token was ever leaked — revoke it in BotFather and create a new one.

## Configuration

The bot reads `.env` from the project directory by default. Environment variables override values from the file.

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from BotFather |
| `BOT_API_BASE` | No | Bot API base URL (default `https://api.telegram.org`) |
| `TELEGRAM_PROXY_URL` | No | Optional SOCKS5 / SOCKS5H proxy URL |
| `BOT_ENV_FILE` | No | Optional path to another env file |

## Commands

| Command | Description |
| --- | --- |
| `/start` | Format guide + example button |
| `/help` | Same as `/start` |
| `/example` | Sends `sample_post.md` source, then the formatted rich post |

> [!NOTE]
> Messages from groups, channels, and other non-private chats are **ignored**, so nothing is posted outside your private conversation by accident.

## Post Format

Send standard Markdown as text, or upload a UTF-8 `.md` file. Invalid content gets line-based validation errors.

### Details (collapsed)

```md
:::details FAQ
Hidden content goes here.
:::
```

<p align="center">
  <img width="505" height="123" alt="Details block" src="https://github.com/user-attachments/assets/e975577f-6e3f-4d3f-9a88-01b70dbb629b" />
</p>

### Details (open by default)

```md
:::details open FAQ
This content starts open.
:::
```

### Collage

```md
:::collage
![](https://example.com/photo-1.jpg "First caption")
![](https://example.com/photo-2.jpg "Second caption")
:::
```

<p align="center">
  <img width="506" height="259" alt="Collage block" src="https://github.com/user-attachments/assets/bcb74cc8-1b89-461c-b9d6-04bebff5e80c" />
</p>

### Slideshow

```md
:::slideshow
![](https://example.com/slide-1.jpg)
![](https://example.com/slide-2.jpg)
:::
```

<p align="center">
  <img width="502" height="491" alt="Slideshow block" src="https://github.com/user-attachments/assets/1e1ee592-1bdc-4248-82c4-d63423249826" />
</p>

> [!CAUTION]
> Media URLs in Markdown images and HTML `src` must start with `http://` or `https://`. Telegram **cannot** fetch local file paths.

Full sample: [sample_post.md](sample_post.md).

## License

Non-commercial use under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International**. See [LICENSE](LICENSE).

## Release Checklist

- [ ] Keep `.env` out of Git; use `.env.example` for public examples
- [ ] Rotate any bot token that was committed or shared
- [ ] `python -m py_compile main.py`
- [ ] Smoke-test `/start`, `/help`, `/example`, a text post, a `.md` upload, and an invalid media URL
