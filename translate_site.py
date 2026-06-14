#!/usr/bin/env python3
"""Generate an English static site from CodeKit-generated Swedish HTML."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype, NavigableString, Tag


DEFAULT_CONFIG = "translate_site.config.json"
LETTER_RE = re.compile(r"[A-Za-zÅÄÖåäö]")
WORD_RE = re.compile(r"[A-Za-zÅÄÖåäö]+(?:[’'][A-Za-zÅÄÖåäö]+)?")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{6,}$")
URL_RE = re.compile(r"^(https?:)?//|^(mailto|tel|data|javascript):", re.I)
WHITESPACE_RE = re.compile(r"^(\s*)(.*?)(\s*)$", re.S)
BROKEN_OG_IMAGE_SIZE_RE = re.compile(
    '<meta property="og:image:width" content="([^"\\u2033]+)\\u2033/>\\s*'
    '<meta\\s+property="\\s*og:image:height" content="([^"\\u2033]+)\\u2033/>\\s*'
    '<link rel="\\s*shortcut icon"'
)


@dataclass
class PageJob:
    source_path: Path
    target_path: Path
    rel_path: str
    source_url: str
    english_url: str


class TranslationCatalog:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.cache_path = Path(config["cache"])
        self.cache: Dict[str, Dict[str, str]] = {}
        self.units: Dict[str, Dict[str, str]] = {}
        self.hits = 0
        self.misses = 0

    def load(self) -> None:
        if not self.cache_path.exists():
            return
        with self.cache_path.open("r", encoding="utf-8") as handle:
            self.cache = json.load(handle)

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("w", encoding="utf-8") as handle:
            json.dump(self.cache, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")

    def key_for(self, text: str) -> str:
        payload = {
            "from": self.config["from"],
            "to": self.config["to"],
            "text": text,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def collect(self, text: str, context: str) -> None:
        core = core_text(text)
        if not should_translate(core, self.config):
            return
        key = self.key_for(core)
        if key in self.cache:
            self.hits += 1
        else:
            self.misses += 1
            self.units.setdefault(key, {"source": core, "context": context})

    def render(self, text: str) -> str:
        leading, core, trailing = split_outer_whitespace(text)
        if not should_translate(core, self.config):
            return text
        key = self.key_for(core)
        translated = self.cache.get(key, {}).get("translated")
        if translated is None:
            raise RuntimeError(f"Missing translation for: {core[:80]!r}")
        return f"{leading}{translated}{trailing}"

    def missing_items(self) -> List[Tuple[str, Dict[str, str]]]:
        return list(self.units.items())


def split_outer_whitespace(text: str) -> Tuple[str, str, str]:
    match = WHITESPACE_RE.match(text)
    if not match:
        return "", text, ""
    return match.group(1), match.group(2), match.group(3)


def core_text(text: str) -> str:
    return split_outer_whitespace(text)[1]


def should_translate(text: str, config: Dict[str, Any]) -> bool:
    candidate = text.strip()
    if not candidate:
        return False
    if not LETTER_RE.search(candidate):
        return False
    if URL_RE.search(candidate):
        return False
    if EMAIL_RE.match(candidate):
        return False
    if PHONE_RE.match(candidate):
        return False
    if candidate in set(config.get("preserve_terms", [])):
        return False
    return True


def heading_preserve_terms(config: Dict[str, Any]) -> set:
    terms = set(config.get("preserve_terms", []))
    terms.update(config.get("heading_preserve_terms", []))
    return terms


def split_possessive(word: str) -> Tuple[str, str]:
    lowered = word.lower()
    for suffix in ("'s", "’s"):
        if lowered.endswith(suffix):
            return word[: -len(suffix)], word[-len(suffix) :]
    return word, ""


def is_mixed_case_term(word: str) -> bool:
    letters = [char for char in word if char.isalpha()]
    if len(letters) < 2:
        return False
    return any(char.isupper() for char in letters[1:]) and any(char.islower() for char in letters)


def should_preserve_heading_word(word: str, preserve_terms: set) -> bool:
    base, _ = split_possessive(word)
    if word in preserve_terms or base in preserve_terms:
        return True
    if base.upper() == base and len(base) > 1:
        return True
    return is_mixed_case_term(base)


def sentence_case_heading(text: str, config: Dict[str, Any]) -> str:
    preserve_terms = heading_preserve_terms(config)
    result: List[str] = []
    previous_end = 0
    capitalize_next = True

    for match in WORD_RE.finditer(text):
        between = text[previous_end : match.start()]
        if re.search(r"[.!?]\s*$", between):
            capitalize_next = True
        elif previous_end == 0 and re.search(r"\d", between):
            capitalize_next = False
        result.append(between)

        word = match.group(0)
        if should_preserve_heading_word(word, preserve_terms):
            result.append(word)
        elif capitalize_next:
            result.append(word[:1].upper() + word[1:].lower())
        else:
            result.append(word.lower())

        capitalize_next = False
        previous_end = match.end()

    result.append(text[previous_end:])
    return "".join(result)


def normalize_heading_capitalization(soup: BeautifulSoup, config: Dict[str, Any]) -> None:
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text_nodes = [
            node
            for node in heading.find_all(string=True)
            if not isinstance(node, (Comment, Doctype)) and str(node).strip()
        ]
        if len(text_nodes) != 1:
            continue
        original = str(text_nodes[0])
        normalized = sentence_case_heading(original, config)
        if normalized != original:
            text_nodes[0].replace_with(NavigableString(normalized))

    title = soup.find("title")
    if title and title.string:
        title.string.replace_with(sentence_case_heading(str(title.string), config))

    for meta in soup.find_all("meta"):
        name = str(meta.get("name", "")).lower()
        prop = str(meta.get("property", "")).lower()
        if (name in {"twitter:title"} or prop in {"og:title"}) and meta.has_attr("content"):
            meta["content"] = sentence_case_heading(str(meta["content"]), config)


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def normalize_known_markup(html: str) -> str:
    def replace_og_image_size(match: re.Match[str]) -> str:
        width, height = match.group(1), match.group(2)
        return (
            f'<meta property="og:image:width" content="{width}" />\n'
            f'  <meta property="og:image:height" content="{height}" />\n'
            '    <link rel="shortcut icon"'
        )

    return BROKEN_OG_IMAGE_SIZE_RE.sub(replace_og_image_size, html)


def path_is_excluded(rel_path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def source_url_for(rel_path: str) -> str:
    if rel_path == "index.html":
        return "/"
    if rel_path.endswith("/index.html"):
        return "/" + rel_path[: -len("index.html")]
    return "/" + rel_path


def english_url_for(source_url: str, target_url_prefix: str) -> str:
    prefix = "/" + target_url_prefix.strip("/")
    if source_url == "/":
        return prefix + "/"
    return prefix + source_url


def discover_jobs(config: Dict[str, Any], limit: Optional[int] = None) -> List[PageJob]:
    source_root = Path(config["source"]).resolve()
    target_root = Path(config["target"])
    if not target_root.is_absolute():
        target_root = source_root / target_root
    target_root = target_root.resolve()
    target_url_prefix = config.get("target_url_prefix", "/en")
    jobs: List[PageJob] = []

    for source_path in sorted(source_root.rglob("*.html")):
        resolved_source = source_path.resolve()
        if resolved_source == target_root or target_root in resolved_source.parents:
            continue
        rel_path = source_path.relative_to(source_root).as_posix()
        if path_is_excluded(rel_path, config.get("exclude", [])):
            continue
        source_url = source_url_for(rel_path)
        english_url = english_url_for(source_url, target_url_prefix)
        target_path = target_root / Path(rel_path)
        jobs.append(PageJob(source_path, target_path, rel_path, source_url, english_url))
        if limit and len(jobs) >= limit:
            break
    return jobs


def rewrite_url(value: str, job: PageJob, config: Dict[str, Any]) -> str:
    if not value or value.startswith("#") or URL_RE.search(value):
        return value

    parsed = urllib.parse.urlsplit(value)
    path = parsed.path
    if not path:
        return value

    for prefix in config.get("asset_prefixes", []):
        if path.startswith(prefix):
            return value

    target_url_prefix = "/" + str(config.get("target_url_prefix", "/en")).strip("/")

    if path.startswith(target_url_prefix + "/") or path == target_url_prefix:
        return value

    if path.startswith("/"):
        rewritten_path = target_url_prefix + "/" if path == "/" else target_url_prefix + path
    else:
        extension = posixpath.splitext(path)[1].lower()
        if extension and extension not in {".html"}:
            return value
        base = job.source_url if job.source_url.endswith("/") else posixpath.dirname(job.source_url) + "/"
        absolute_path = posixpath.normpath(posixpath.join(base, path))
        if not absolute_path.startswith("/"):
            absolute_path = "/" + absolute_path
        rewritten_path = target_url_prefix + "/" if absolute_path == "/" else target_url_prefix + absolute_path

    return urllib.parse.urlunsplit(("", "", rewritten_path, parsed.query, parsed.fragment))


def context_for(job: PageJob, kind: str, detail: str = "") -> str:
    suffix = f":{detail}" if detail else ""
    return f"{job.rel_path}:{kind}{suffix}"


def meta_content_is_translatable(tag: Tag) -> bool:
    name = str(tag.get("name", "")).lower()
    prop = str(tag.get("property", "")).lower()
    return name in {"description", "keywords"} or prop in {
        "og:title",
        "og:description",
        "twitter:title",
        "twitter:description",
    }


def transform_soup(
    html: str,
    job: PageJob,
    config: Dict[str, Any],
    catalog: TranslationCatalog,
    mode: str,
) -> str:
    html = normalize_known_markup(html)
    soup = BeautifulSoup(html, "html.parser")
    skip_tags = set(config.get("skip_tags", []))
    translate_attrs = set(config.get("translate_attributes", []))

    html_tag = soup.find("html")
    if html_tag:
        html_tag["lang"] = "en"

    for tag in soup.find_all(True):
        classes = tag.get("class")
        if isinstance(classes, list) and "language-current" in classes:
            tag["class"] = [class_name for class_name in classes if class_name not in {"language-flag-sv", "language-flag-en"}]
            tag["class"].append("language-flag-en")

        if tag.name in skip_tags:
            continue

        language = tag.get("data-language-link")
        if tag.name == "a" and language in {"sv", "en"}:
            tag["href"] = job.source_url if language == "sv" else job.english_url
        elif tag.has_attr("href"):
            tag["href"] = rewrite_url(str(tag["href"]), job, config)

        if tag.has_attr("action"):
            tag["action"] = rewrite_url(str(tag["action"]), job, config)

        if tag.name == "meta" and tag.has_attr("content") and meta_content_is_translatable(tag):
            value = str(tag["content"])
            catalog.collect(value, context_for(job, "meta", str(tag.get("name") or tag.get("property"))))
            if mode == "render":
                tag["content"] = catalog.render(value)

        for attr in translate_attrs:
            if not tag.has_attr(attr):
                continue
            value = tag.get(attr)
            if not isinstance(value, str):
                continue
            catalog.collect(value, context_for(job, "attr", attr))
            if mode == "render":
                tag[attr] = catalog.render(value)

    for text_node in list(soup.find_all(string=True)):
        if isinstance(text_node, (Comment, Doctype)):
            continue
        parent = text_node.parent
        if parent and parent.name in skip_tags:
            continue
        text = str(text_node)
        catalog.collect(text, context_for(job, "text", parent.name if parent else "document"))
        if mode == "render":
            translated = catalog.render(text)
            if translated != text:
                text_node.replace_with(NavigableString(translated))

    if mode == "render":
        normalize_heading_capitalization(soup, config)

    return str(soup)


def collect_jobs(jobs: List[PageJob], config: Dict[str, Any], catalog: TranslationCatalog) -> None:
    for job in jobs:
        html = job.source_path.read_text(encoding="utf-8")
        transform_soup(html, job, config, catalog, mode="collect")


def render_jobs(jobs: List[PageJob], config: Dict[str, Any], catalog: TranslationCatalog, force: bool) -> int:
    written = 0
    for job in jobs:
        html = job.source_path.read_text(encoding="utf-8")
        output = transform_soup(html, job, config, catalog, mode="render")
        if job.target_path.exists() and not force:
            current = job.target_path.read_text(encoding="utf-8")
            if current == output:
                continue
        job.target_path.parent.mkdir(parents=True, exist_ok=True)
        job.target_path.write_text(output, encoding="utf-8")
        written += 1
    return written


def total_source_chars(items: List[Tuple[str, Dict[str, str]]]) -> int:
    return sum(len(item["source"]) for _, item in items)


def enforce_translation_limits(
    items: List[Tuple[str, Dict[str, str]]],
    config: Dict[str, Any],
) -> None:
    max_items = int(config.get("max_uncached_items_per_run", 300))
    max_chars = int(config.get("max_uncached_chars_per_run", 50000))
    max_single = int(config.get("max_single_text_chars", 8000))
    item_count = len(items)
    char_count = total_source_chars(items)
    oversized = [(key, item) for key, item in items if len(item["source"]) > max_single]

    problems = []
    if item_count > max_items:
        problems.append(f"{item_count} uncached strings exceeds max_uncached_items_per_run={max_items}")
    if char_count > max_chars:
        problems.append(f"{char_count} uncached characters exceeds max_uncached_chars_per_run={max_chars}")
    if oversized:
        longest = max(oversized, key=lambda row: len(row[1]["source"]))
        problems.append(
            f"one string is {len(longest[1]['source'])} characters, "
            f"exceeding max_single_text_chars={max_single} at {longest[1]['context']}"
        )

    if problems:
        details = "\n- ".join(problems)
        raise RuntimeError(
            "Translation run blocked by safety limits.\n"
            f"- {details}\n"
            "Use --limit to process fewer pages, or deliberately raise the limit "
            "in translate_site.config.json or with --max-items/--max-chars."
        )


def iter_translation_batches(
    items: List[Tuple[str, Dict[str, str]]],
    batch_size: int,
    max_batch_chars: int,
) -> Iterable[List[Tuple[str, Dict[str, str]]]]:
    batch: List[Tuple[str, Dict[str, str]]] = []
    batch_chars = 0

    for item in items:
        item_chars = len(item[1]["source"])
        if batch and (len(batch) >= batch_size or batch_chars + item_chars > max_batch_chars):
            yield batch
            batch = []
            batch_chars = 0
        batch.append(item)
        batch_chars += item_chars

    if batch:
        yield batch


def translate_missing(catalog: TranslationCatalog, config: Dict[str, Any]) -> None:
    items = catalog.missing_items()
    if not items:
        return

    enforce_translation_limits(items, config)

    provider = config.get("provider", "openai")
    if provider != "openai":
        raise RuntimeError(f"Unsupported provider: {provider}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for real translation. Use --dry-run to scan only.")

    model = os.environ.get("OPENAI_MODEL") or config.get("model", "gpt-4o-mini")
    batch_size = int(config.get("batch_size", 30))
    max_batch_chars = int(config.get("max_batch_chars", 12000))
    total = len(items)

    completed = 0
    for batch in iter_translation_batches(items, batch_size, max_batch_chars):
        batch_chars = total_source_chars(batch)
        print(
            f"Translating {completed + 1}-{completed + len(batch)} of {total} "
            f"({batch_chars} chars) with {model}...",
            flush=True,
        )
        translations = call_openai_translation(batch, config, api_key, model)
        for key, translated in translations.items():
            source = catalog.units[key]["source"]
            catalog.cache[key] = {"source": source, "translated": translated}
        catalog.save()
        completed += len(batch)
        time.sleep(0.2)


def call_openai_translation(
    batch: List[Tuple[str, Dict[str, str]]],
    config: Dict[str, Any],
    api_key: str,
    model: str,
) -> Dict[str, str]:
    preserve_terms = ", ".join(config.get("preserve_terms", []))
    input_items = [
        {
            "id": key,
            "text": item["source"],
            "context": item["context"],
        }
        for key, item in batch
    ]
    system = (
        "You translate Swedish website copy into natural, polished English. "
        "Return strict JSON only. Preserve brand/product names exactly. "
        "Do not add HTML tags. Do not translate URLs, emails, phone numbers, CSS, JS, "
        "class names, IDs, or filenames. Use European sentence capitalization, not "
        "American title case, for headings and page titles. Keep meaning concise for SEO metadata."
    )
    if preserve_terms:
        system += f" Preserve these terms exactly: {preserve_terms}."
    user = {
        "instructions": "Return an object with a translations array. Each item must contain id and text.",
        "from": config["from"],
        "to": config["to"],
        "items": input_items,
    }
    payload: Dict[str, Any] = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        data = post_openai(payload, api_key)
    except urllib.error.HTTPError as error:
        if error.code != 400:
            raise
        payload.pop("response_format", None)
        data = post_openai(payload, api_key)

    content = data["choices"][0]["message"]["content"]
    parsed = parse_json_response(content)
    rows = parsed.get("translations", [])
    result: Dict[str, str] = {}
    for row in rows:
        key = row.get("id")
        text = row.get("text")
        if isinstance(key, str) and isinstance(text, str):
            result[key] = text

    expected = {key for key, _ in batch}
    missing = expected - set(result)
    if missing:
        raise RuntimeError(f"Translation response missed {len(missing)} item(s).")
    return result


def post_openai(payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_json_response(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(content[start : end + 1])


def print_plan(config: Dict[str, Any]) -> None:
    print("Translation plan")
    print(f"- Source: {config['source']}")
    print(f"- Target: {config['target']}")
    print(f"- Language: {config['from']} -> {config['to']}")
    print(f"- Provider: {config.get('provider', 'openai')}")
    print(f"- Model: {os.environ.get('OPENAI_MODEL') or config.get('model')}")
    print(f"- Cache: {config['cache']}")
    print("- Pass 1: collect visible text and SEO/accessibility attributes")
    print("- Pass 2: translate missing cache entries in batches")
    print("- Pass 3: write translated HTML under target and rewrite local page links")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to translation config JSON.")
    parser.add_argument("--source", help="Override source directory.")
    parser.add_argument("--target", help="Override target directory.")
    parser.add_argument("--from", dest="from_lang", help="Override source language.")
    parser.add_argument("--to", dest="to_lang", help="Override target language.")
    parser.add_argument("--dry-run", action="store_true", help="Scan and report without translating or writing files.")
    parser.add_argument("--force", action="store_true", help="Overwrite generated English files.")
    parser.add_argument("--limit", type=int, help="Only process the first N files.")
    parser.add_argument("--max-items", type=int, help="Override max uncached strings allowed in one run.")
    parser.add_argument("--max-chars", type=int, help="Override max uncached source characters allowed in one run.")
    parser.add_argument("--print-plan", action="store_true", help="Print the configured workflow and exit.")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    if args.source:
        config["source"] = args.source
    if args.target:
        config["target"] = args.target
    if args.from_lang:
        config["from"] = args.from_lang
    if args.to_lang:
        config["to"] = args.to_lang
    if args.max_items is not None:
        config["max_uncached_items_per_run"] = args.max_items
    if args.max_chars is not None:
        config["max_uncached_chars_per_run"] = args.max_chars

    load_dotenv(Path(".env"))

    if args.print_plan:
        print_plan(config)
        return 0

    catalog = TranslationCatalog(config)
    catalog.load()
    jobs = discover_jobs(config, limit=args.limit)
    collect_jobs(jobs, config, catalog)
    missing = catalog.missing_items()

    print(f"Found {len(jobs)} HTML page(s).")
    print(f"Cache hits: {catalog.hits}")
    print(f"Missing translations: {len(missing)}")
    print(f"Missing source characters: {total_source_chars(missing)}")
    print(
        "Safety limits: "
        f"{config.get('max_uncached_items_per_run')} uncached strings, "
        f"{config.get('max_uncached_chars_per_run')} uncached chars per run."
    )

    if args.dry_run:
        for key, item in missing[:10]:
            print(f"- {item['context']}: {item['source'][:100]}")
        if len(missing) > 10:
            print(f"...and {len(missing) - 10} more.")
        return 0

    translate_missing(catalog, config)
    written = render_jobs(jobs, config, catalog, force=args.force)
    catalog.save()
    print(f"Wrote {written} English page(s) to {config['target']}/.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
