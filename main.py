from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HELP_TEXT = """Send me a Telegram Rich Markdown post as text or as a .md file.

Supported custom blocks:

:::details Title
Hidden content
:::

:::details open Title
Expanded content
:::

:::collage
![](https://example.com/photo.jpg "Caption")
:::

:::slideshow
![](https://example.com/photo.jpg)
:::

Images and media must use HTTP/HTTPS URLs.
"""


DIRECTIVE_RE = re.compile(r"^:::(?P<name>[A-Za-z][A-Za-z0-9_-]*)(?P<args>.*)$")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*]\(\s*(?P<url><[^>]+>|[^)\s]+)")
HTML_MEDIA_RE = re.compile(
    r"<(?:img|video|audio)\b[^>]*\bsrc\s*=\s*(?P<quote>['\"])(?P<url>.*?)(?P=quote)",
    re.IGNORECASE,
)
DEFAULT_ENV_FILE = Path(__file__).with_name(".env")


@dataclass(frozen=True)
class BotConfig:
    token: str
    api_base: str = "https://api.telegram.org"


@dataclass(frozen=True)
class ValidationError:
    line: int
    message: str


@dataclass(frozen=True)
class MarkdownResult:
    markdown: str
    errors: list[ValidationError]


@dataclass
class DirectiveFrame:
    name: str
    line: int
    closing_tag: str


class TelegramAPIError(RuntimeError):
    def __init__(self, method: str, description: str, error_code: int | None = None) -> None:
        self.method = method
        self.description = description
        self.error_code = error_code
        prefix = f"Telegram {method} failed"
        if error_code is not None:
            prefix += f" ({error_code})"
        super().__init__(f"{prefix}: {description}")


class TelegramAPI:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.base_url = f"{config.api_base.rstrip('/')}/bot{config.token}"
        self.file_base_url = f"{config.api_base.rstrip('/')}/file/bot{config.token}"

    async def call(self, method: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
        return await asyncio.to_thread(self._call_sync, method, payload or {}, timeout)

    def _call_sync(self, method: str, payload: dict[str, Any], timeout: int) -> Any:
        url = f"{self.base_url}/{method}"
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as json_error:
                raise TelegramAPIError(method, raw or str(exc), exc.code) from json_error
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TelegramAPIError(method, str(exc)) from exc

        if not data.get("ok"):
            raise TelegramAPIError(method, data.get("description", "Unknown error"), data.get("error_code"))
        return data.get("result")

    async def download_file(self, file_path: str, timeout: int = 30) -> bytes:
        quoted_path = urllib.parse.quote(file_path, safe="/")
        url = f"{self.file_base_url}/{quoted_path}"
        try:
            return await asyncio.to_thread(self._download_sync, url, timeout)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TelegramAPIError("downloadFile", str(exc)) from exc

    @staticmethod
    def _download_sync(url: str, timeout: int) -> bytes:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read()


def load_config() -> BotConfig:
    load_env_file()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required. Set it in .env or in the environment.")

    api_base = os.getenv("BOT_API_BASE", "https://api.telegram.org").strip() or "https://api.telegram.org"
    return BotConfig(token=token, api_base=api_base)


def load_env_file(path: str | os.PathLike[str] | None = None) -> None:
    if path is None:
        configured_path = os.getenv("BOT_ENV_FILE", "").strip()
        env_path = Path(configured_path) if configured_path else DEFAULT_ENV_FILE
    else:
        env_path = Path(path)

    if not env_path.exists():
        return

    for line_number, line in enumerate(env_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise SystemExit(f"Invalid env line {line_number} in {env_path}: expected KEY=VALUE.")

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise SystemExit(f"Invalid env line {line_number} in {env_path}: key is empty.")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def prepare_rich_markdown(source: str) -> MarkdownResult:
    converted = convert_directives(source)
    if converted.errors:
        return converted

    errors = validate_media_urls(source)
    markdown = converted.markdown.strip()
    if not markdown:
        errors.append(ValidationError(1, "Post is empty after preprocessing."))
    return MarkdownResult(markdown=markdown, errors=errors)


def convert_directives(source: str) -> MarkdownResult:
    lines = source.splitlines()
    output: list[str] = []
    stack: list[DirectiveFrame] = []
    errors: list[ValidationError] = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped == ":::":
            if not stack:
                errors.append(ValidationError(line_number, "Closing directive without a matching opening directive."))
                continue
            output.append(stack.pop().closing_tag)
            continue

        match = DIRECTIVE_RE.match(stripped)
        if match:
            name = match.group("name").lower()
            args = match.group("args").strip()
            opened = open_directive(name, args, line_number)
            if isinstance(opened, ValidationError):
                errors.append(opened)
                continue

            opening_lines, closing_tag = opened
            output.extend(opening_lines)
            stack.append(DirectiveFrame(name=name, line=line_number, closing_tag=closing_tag))
            continue

        output.append(line)

    for frame in reversed(stack):
        errors.append(ValidationError(frame.line, f"Unclosed {frame.name!r} directive. Add a closing ::: line."))

    return MarkdownResult(markdown="\n".join(output), errors=errors)


def open_directive(name: str, args: str, line_number: int) -> tuple[list[str], str] | ValidationError:
    if name == "details":
        is_open = False
        title = args
        if args.lower().startswith("open "):
            is_open = True
            title = args[5:].strip()

        if not title:
            return ValidationError(line_number, "details directive requires a title.")

        tag = "<details open>" if is_open else "<details>"
        return [tag, f"<summary>{title}</summary>"], "</details>"

    if name == "collage":
        if args:
            return ValidationError(line_number, "collage directive does not accept arguments.")
        return ["<tg-collage>"], "</tg-collage>"

    if name == "slideshow":
        if args:
            return ValidationError(line_number, "slideshow directive does not accept arguments.")
        return ["<tg-slideshow>"], "</tg-slideshow>"

    return ValidationError(line_number, f"Unknown directive {name!r}.")


def validate_media_urls(source: str) -> list[ValidationError]:
    errors: list[ValidationError] = []
    in_fence = False

    for line_number, line in enumerate(source.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for match in MARKDOWN_IMAGE_RE.finditer(line):
            url = match.group("url").strip("<>")
            if not is_http_url(url):
                errors.append(ValidationError(line_number, f"Media URL must start with http:// or https://: {url}"))

        for match in HTML_MEDIA_RE.finditer(line):
            url = match.group("url")
            if not is_http_url(url):
                errors.append(ValidationError(line_number, f"HTML media src must start with http:// or https://: {url}"))

    return errors


def is_http_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def format_errors(errors: list[ValidationError]) -> str:
    lines = ["Cannot send this post:"]
    for error in errors:
        lines.append(f"line {error.line}: {error.message}")
    return "\n".join(lines)


async def send_text(api: TelegramAPI, chat_id: int | str, text: str) -> None:
    await api.call("sendMessage", {"chat_id": chat_id, "text": text})


async def send_rich_markdown(api: TelegramAPI, chat_id: int | str, markdown: str) -> None:
    await api.call(
        "sendRichMessage",
        {
            "chat_id": chat_id,
            "rich_message": {
                "markdown": markdown,
            },
        },
    )


async def handle_markdown(api: TelegramAPI, chat_id: int | str, source: str) -> None:
    result = prepare_rich_markdown(source)
    if result.errors:
        await send_text(api, chat_id, format_errors(result.errors))
        return

    try:
        await send_rich_markdown(api, chat_id, result.markdown)
    except TelegramAPIError as exc:
        await send_text(api, chat_id, str(exc))


async def handle_document(api: TelegramAPI, chat_id: int | str, document: dict[str, Any]) -> None:
    file_name = document.get("file_name") or ""
    if not file_name.lower().endswith(".md"):
        await send_text(api, chat_id, "Cannot send this post:\nline 1: Upload a .md file.")
        return

    try:
        file_info = await api.call("getFile", {"file_id": document["file_id"]})
        raw = await api.download_file(file_info["file_path"])
    except TelegramAPIError as exc:
        await send_text(api, chat_id, str(exc))
        return

    try:
        source = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        await send_text(api, chat_id, "Cannot send this post:\nline 1: The .md file must be UTF-8 encoded.")
        return

    await handle_markdown(api, chat_id, source)


async def handle_update(api: TelegramAPI, update: dict[str, Any]) -> None:
    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]

    text = message.get("text")
    if text:
        command = text.split(maxsplit=1)[0].split("@", 1)[0]
        if command in {"/start", "/help"}:
            await send_text(api, chat_id, HELP_TEXT)
            return
        await handle_markdown(api, chat_id, text)
        return

    document = message.get("document")
    if document:
        await handle_document(api, chat_id, document)
        return

    await send_text(api, chat_id, "Send a Telegram Rich Markdown post as text or upload a .md file.")


async def polling_loop(api: TelegramAPI) -> None:
    offset = 0
    while True:
        try:
            updates = await api.call(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 50,
                    "allowed_updates": ["message"],
                },
                timeout=60,
            )
            for update in updates:
                offset = max(offset, update["update_id"] + 1)
                await handle_update(api, update)
        except TelegramAPIError as exc:
            print(exc, file=sys.stderr)
            await asyncio.sleep(3)


def main() -> None:
    config = load_config()
    api = TelegramAPI(config)
    asyncio.run(polling_loop(api))


if __name__ == "__main__":
    main()
