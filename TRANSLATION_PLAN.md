# English Site Translation Plan

This site stays CodeKit-first. CodeKit generates the Swedish `.html` files from `.kit` sources, then `translate_site.py` post-processes those generated Swedish files into a matching English tree under `en/`.

## Workflow

1. Edit `.kit`, SCSS, and JS sources as usual.
2. Let CodeKit generate the Swedish `.html`, CSS, and JS.
3. Run:

   ```sh
   python3 translate_site.py --dry-run
   ```

4. If the dry run looks right and `OPENAI_API_KEY` is available, run:

   ```sh
   python3 translate_site.py
   ```

5. Review the generated `en/` pages locally.

## Design

- Source pages are generated Swedish `.html` files.
- Output pages are written under `en/` with matching paths.
- The Swedish originals are never modified.
- HTML structure, classes, IDs, scripts, stylesheets, image paths, and asset paths are preserved.
- Visible text nodes are translated.
- SEO text in `<title>`, description/keywords meta tags, Open Graph title/description, `alt`, `title`, `aria-label`, and placeholders is translated.
- Internal page links are rewritten to `/en/...`.
- Asset links such as `/assets/...` and `/images/...` are preserved.
- The language switcher gets correct static links for Swedish and English.
- English headings and page title metadata are normalized to European sentence capitalization during rendering, while configured proper nouns and product names are preserved.
- Translations are cached in `.translation-cache/sv-en.json`.
- Large uncached runs are blocked by default to avoid accidental API spend.

## Notes

- The script uses BeautifulSoup; install dependencies with `python3 -m pip install --user -r requirements.txt`.
- Real translation requires `OPENAI_API_KEY`.
- The default model can be changed in `translate_site.config.json` or with `OPENAI_MODEL`.
- Use `--force` to overwrite existing English files.
- Default safety limits are 300 uncached strings, 50,000 uncached source characters, 8,000 characters for any single string, and 12,000 characters per API batch.
- Use `--limit` for incremental translation. To translate more in one run, deliberately raise `max_uncached_items_per_run` or `max_uncached_chars_per_run` in the config, or pass `--max-items` / `--max-chars` for that run.
