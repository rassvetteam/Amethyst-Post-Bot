from __future__ import annotations

import asyncio
import http.client
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


HELP_TEXT = """Send me a Telegram Rich Markdown post as text or upload a UTF-8 .md file.

Supported blocks:

:::details Title
Hidden text
:::

:::details open Title
Expanded text
:::

:::collage
![](https://example.com/photo.jpg "Caption")
:::

:::slideshow
![](https://example.com/photo.jpg)
:::

Media must use http:// or https:// URLs.
"""


DIRECTIVE_RE = re.compile(r"^:::(?P<name>[A-Za-z][A-Za-z0-9_-]*)(?P<args>.*)$")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*]\(\s*(?P<url><[^>]+>|[^)\s]+)")
HTML_MEDIA_RE = re.compile(
    r"<(?:img|video|audio)\b[^>]*\bsrc\s*=\s*(?P<quote>['\"])(?P<url>.*?)(?P=quote)",
    re.IGNORECASE,
)
DEFAULT_ENV_FILE = Path(__file__).with_name(".env")
SAMPLE_POST_FILE = Path(__file__).with_name("sample_post.md")
CALLBACK_SHOW_EXAMPLE = "show_example"
CALLBACK_ANSWER_TIMEOUT = 2
SEND_MESSAGE_TIMEOUT = 8


@dataclass(frozen=True)
class BotConfig:
    token: str
    api_base: str = "https://api.telegram.org"
    proxy_url: str = ""


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
        prefix = f"Telegram method {method} failed"
        if error_code is not None:
            prefix += f" ({error_code})"
        super().__init__(f"{prefix}: {description}")


class TelegramAPI:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.base_url = f"{config.api_base.rstrip('/')}/bot{config.token}"
        self.file_base_url = f"{config.api_base.rstrip('/')}/file/bot{config.token}"
        self.opener = build_url_opener(config.proxy_url)

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
            with self.open_url(request, timeout) as response:
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

    def _download_sync(self, url: str, timeout: int) -> bytes:
        with self.open_url(url, timeout) as response:
            return response.read()

    def open_url(self, request_or_url: urllib.request.Request | str, timeout: int) -> Any:
        if self.opener is not None:
            return self.opener.open(request_or_url, timeout=timeout)
        return urllib.request.urlopen(request_or_url, timeout=timeout)


def load_config() -> BotConfig:
    load_env_file()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required. Set it in .env or in the environment.")

    api_base = os.getenv("BOT_API_BASE", "https://api.telegram.org").strip() or "https://api.telegram.org"
    return BotConfig(
        token=token,
        api_base=api_base,
        proxy_url=os.getenv("TELEGRAM_PROXY_URL", "").strip(),
    )


def build_url_opener(proxy_url: str) -> urllib.request.OpenerDirector | None:
    if not proxy_url:
        return None

    parsed = urllib.parse.urlparse(proxy_url)
    scheme = parsed.scheme.lower()
    if scheme not in {"socks5", "socks5h"}:
        raise SystemExit("TELEGRAM_PROXY_URL must start with socks5:// or socks5h://.")
    if not parsed.hostname or not parsed.port:
        raise SystemExit("TELEGRAM_PROXY_URL must include a host and port.")

    try:
        import socks
    except ImportError as exc:
        raise SystemExit("Install the SOCKS proxy dependency: pip install -r requirements.txt") from exc

    username = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    rdns = scheme == "socks5h"

    def create_socks_connection(connection: http.client.HTTPConnection) -> Any:
        return socks.create_connection(
            (connection.host, connection.port),
            timeout=connection.timeout,
            source_address=getattr(connection, "source_address", None),
            proxy_type=socks.SOCKS5,
            proxy_addr=parsed.hostname,
            proxy_port=parsed.port,
            proxy_username=username,
            proxy_password=password,
            proxy_rdns=rdns,
        )

    class SocksHTTPConnection(http.client.HTTPConnection):
        def connect(self) -> None:
            self.sock = create_socks_connection(self)
            if self._tunnel_host:  # type: ignore[attr-defined]
                self._tunnel()  # type: ignore[attr-defined]

    class SocksHTTPSConnection(http.client.HTTPSConnection):
        def connect(self) -> None:
            sock = create_socks_connection(self)
            if self._tunnel_host:  # type: ignore[attr-defined]
                self.sock = sock
                self._tunnel()  # type: ignore[attr-defined]
                sock = self.sock
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)  # type: ignore[attr-defined]

    class SocksHTTPHandler(urllib.request.HTTPHandler):
        def http_open(self, req: urllib.request.Request) -> Any:
            return self.do_open(SocksHTTPConnection, req)

    class SocksHTTPSHandler(urllib.request.HTTPSHandler):
        def https_open(self, req: urllib.request.Request) -> Any:
            return self.do_open(SocksHTTPSConnection, req)

    return urllib.request.build_opener(SocksHTTPHandler, SocksHTTPSHandler)


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
            raise SystemExit(f"Invalid line {line_number} in {env_path}: expected KEY=VALUE.")

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise SystemExit(f"Invalid line {line_number} in {env_path}: the key is empty.")
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
        errors.append(ValidationError(1, "The post is empty after processing."))
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
                errors.append(ValidationError(line_number, "Closing block without a matching opening block."))
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
        errors.append(ValidationError(frame.line, f"Block {frame.name!r} is not closed. Add a ::: line."))

    return MarkdownResult(markdown="\n".join(output), errors=errors)


def open_directive(name: str, args: str, line_number: int) -> tuple[list[str], str] | ValidationError:
    if name == "details":
        is_open = False
        title = args
        if args.lower().startswith("open "):
            is_open = True
            title = args[5:].strip()

        if not title:
            return ValidationError(line_number, "The details block requires a title.")

        tag = "<details open>" if is_open else "<details>"
        return [tag, f"<summary>{title}</summary>"], "</details>"

    if name == "collage":
        if args:
            return ValidationError(line_number, "The collage block does not accept arguments.")
        return ["<tg-collage>"], "</tg-collage>"

    if name == "slideshow":
        if args:
            return ValidationError(line_number, "The slideshow block does not accept arguments.")
        return ["<tg-slideshow>"], "</tg-slideshow>"

    return ValidationError(line_number, f"Unknown block {name!r}.")


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
    lines = ["I cannot send this post:"]
    for error in errors:
        lines.append(f"line {error.line}: {error.message}")
    return "\n".join(lines)


async def send_text(
    api: TelegramAPI,
    chat_id: int | str,
    text: str,
    reply_markup: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    await api.call("sendMessage", payload, timeout=SEND_MESSAGE_TIMEOUT)


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


async def send_example(api: TelegramAPI, chat_id: int | str) -> None:
    try:
        source = SAMPLE_POST_FILE.read_text(encoding="utf-8-sig")
    except OSError as exc:
        await send_text(api, chat_id, f"Could not read the example post: {exc}")
        return

    await send_text(api, chat_id, f"Example post MD file:\n\n```md\n{source}\n```")
    await send_text(api, chat_id, "This is how the finished rich post will look:")
    await handle_markdown(api, chat_id, source)


async def handle_document(api: TelegramAPI, chat_id: int | str, document: dict[str, Any]) -> None:
    file_name = document.get("file_name") or ""
    if not file_name.lower().endswith(".md"):
        await send_text(api, chat_id, "I cannot send this post:\nline 1: upload a .md file.")
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
        await send_text(api, chat_id, "I cannot send this post:\nline 1: the .md file must use UTF-8 encoding.")
        return

    await handle_markdown(api, chat_id, source)


def main_keyboard() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "Show example", "callback_data": CALLBACK_SHOW_EXAMPLE}],
        ]
    }


async def send_help(api: TelegramAPI, chat_id: int | str) -> None:
    await send_text(api, chat_id, HELP_TEXT, main_keyboard())


async def answer_callback(api: TelegramAPI, callback_query_id: str, text: str = "") -> None:
    payload: dict[str, Any] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        await api.call("answerCallbackQuery", payload, timeout=CALLBACK_ANSWER_TIMEOUT)
    except TelegramAPIError as exc:
        print(exc, file=sys.stderr)


def schedule_callback_answer(api: TelegramAPI, callback_query_id: str, text: str = "") -> None:
    asyncio.create_task(answer_callback(api, callback_query_id, text))


def is_private_chat(chat: dict[str, Any]) -> bool:
    return chat.get("type") == "private"


async def handle_callback_query(api: TelegramAPI, callback_query: dict[str, Any]) -> None:
    callback_query_id = callback_query["id"]
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    data = callback_query.get("data")

    if chat_id is None:
        schedule_callback_answer(api, callback_query_id, "Could not identify the chat.")
        return

    if not is_private_chat(chat):
        schedule_callback_answer(api, callback_query_id, "The bot works only in private chats.")
        return

    if data != CALLBACK_SHOW_EXAMPLE:
        schedule_callback_answer(api, callback_query_id, "Unknown action.")
        return

    schedule_callback_answer(api, callback_query_id)
    await send_example(api, chat_id)


async def handle_update(api: TelegramAPI, update: dict[str, Any]) -> None:
    callback_query = update.get("callback_query")
    if callback_query:
        await handle_callback_query(api, callback_query)
        return

    message = update.get("message")
    if not message:
        return

    chat = message["chat"]
    if not is_private_chat(chat):
        return

    chat_id = chat["id"]
    text = message.get("text")
    if text:
        command = text.split(maxsplit=1)[0].split("@", 1)[0]
        if command in {"/start", "/help"}:
            await send_help(api, chat_id)
            return
        if command == "/example":
            await send_example(api, chat_id)
            return
        await handle_markdown(api, chat_id, text)
        return

    document = message.get("document")
    if document:
        await handle_document(api, chat_id, document)
        return

    await send_text(api, chat_id, "Send a post as text or upload a .md file.", main_keyboard())


async def polling_loop(api: TelegramAPI) -> None:
    offset = 0
    while True:
        try:
            updates = await api.call(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 50,
                    "allowed_updates": ["message", "callback_query"],
                },
                timeout=60,
            )
            for update in updates:
                offset = max(offset, update["update_id"] + 1)
                await handle_update(api, update)
        except TelegramAPIError as exc:
            print(exc, file=sys.stderr)
            await asyncio.sleep(3)


def looks_like_proxy_error(exc: TelegramAPIError) -> bool:
    text = f"{exc.description}".lower()
    return "socks5 proxy" in text or "proxy" in text or "winerror 10060" in text


async def verify_api_connection(api: TelegramAPI, config: BotConfig) -> None:
    try:
        await api.call("getMe", timeout=10)
    except TelegramAPIError as exc:
        if config.proxy_url and looks_like_proxy_error(exc):
            raise SystemExit(
                "Could not connect to Telegram through the SOCKS proxy.\n"
                "Check that the proxy is available, the credentials are correct, the port is open, and the proxy permits Telegram connections.\n"
                "To run locally without a proxy, temporarily clear TELEGRAM_PROXY_URL in .env.\n"
                f"Technical error: {exc.description}"
            ) from exc
        raise


async def run_bot(api: TelegramAPI, config: BotConfig) -> None:
    await verify_api_connection(api, config)
    await polling_loop(api)


def main() -> None:
    config = load_config()
    api = TelegramAPI(config)
    asyncio.run(run_bot(api, config))


if __name__ == "__main__":
    main()
