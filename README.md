# Amethyst Post Bot

A small Telegram bot for publishing Telegram Rich Markdown posts from plain text or uploaded `.md` files.

The bot accepts a post, validates media links, converts a few convenient custom blocks, and sends the result through `sendRichMessage`.

## Features

- Accepts Markdown sent as a Telegram message or as a UTF-8 `.md` file.
- Converts short custom directives into Telegram Rich Markdown HTML blocks.
- Validates Markdown and HTML media URLs before sending.
- Uses only the Python standard library.

## Requirements

- Python 3.10 or newer.
- A Telegram bot token from BotFather.
- A Bot API endpoint that supports `sendRichMessage`.

## Quick Start

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env`:

   ```env
   TELEGRAM_BOT_TOKEN=123456789:your_real_bot_token
   ```

3. Run the bot:

   ```bash
   python main.py
   ```

4. Open your Telegram bot and send `/help`.

## Configuration

The bot reads `.env` from the project directory by default. Real secrets must stay in `.env`; this file is ignored by Git.

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from BotFather. |
| `BOT_ENV_FILE` | No | Optional path to another env file. Set it as an environment variable before launch. |

Environment variables take priority over values from `.env`.

## Mini Guide

Send a Markdown post directly to the bot, or upload a UTF-8 `.md` file. The bot checks the content and either publishes it or replies with line-based validation errors.

Use standard Markdown plus these extra blocks:

### Details

```md
:::details FAQ
Hidden content goes here.
:::
```

<img width="509" height="121" alt="изображение" src="https://github.com/user-attachments/assets/cff55120-aca7-44a7-ba25-61d31bb92acf" />


Expanded by default:

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

<img width="509" height="257" alt="изображение" src="https://github.com/user-attachments/assets/e731bf11-7c87-4297-9944-35a73d5eed23" />


### Slideshow

```md
:::slideshow
![](https://example.com/slide-1.jpg)
![](https://example.com/slide-2.jpg)
:::
```

<img width="502" height="489" alt="изображение" src="https://github.com/user-attachments/assets/b97e5131-39dd-42e6-a820-60a8f0a2af21" />


Media links in Markdown images and HTML `src` attributes must start with `http://` or `https://`. Local paths are rejected because Telegram cannot fetch them.

## Example Post

See [sample_post.md](sample_post.md) for a full post that uses details, collage, slideshow, spoiler text, and a complex math block.

## Release Checklist

- Keep `.env` out of Git.
- Use `.env.example` for public configuration examples.
- Rotate any bot token that was ever committed or shared publicly before creating a GitHub release.
