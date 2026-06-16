# AGENTS.md

Guidance for AI agents working on the Faunapoolen website.

## Project Overview

This is a static marketing site for Faunapoolen. The site is built with CodeKit.

CodeKit is expected to run in the background during normal editing. When a `.kit` file is saved, CodeKit notices the change and renders the matching `.html` file. The same general workflow applies to SCSS and JavaScript outputs.

## Edit Source Files

- Edit `.kit` files for page markup and content.
- Do not edit generated `.html` files directly unless the user explicitly asks for it.
- Keep CodeKit include comments intact, for example:
  `<!-- @include '/assets/components/_header.kit' -->`
- If generated HTML does not update after a `.kit` change, assume the CodeKit watcher is not running or did not catch the save. Do not hand-edit HTML to force it; tell the user.

## Kit Includes And Variables

Kit files are HTML plus CodeKit special comments. CodeKit compiles `.kit` files into `.html`.

- `@include` and `@import` both import another file. Use `@include` in this project for consistency.
- CodeKit replaces the include comment with the full text of the imported file.
- If the imported file is also `.kit`, CodeKit compiles it recursively.
- Root-relative include paths start with `/` and resolve from the project root.
- Relative include paths resolve from the `.kit` file that contains the include.
- The `.kit` extension is optional for Kit includes, but include it in this project for clarity.
- Include-only partials should use a leading underscore, such as `assets/components/_header.kit`.
- CodeKit can resolve partials without the underscore, but this project should use the explicit filename already present in the repo.

Preferred page-level variable pattern:

```html
<!-- $pageTitle = About us -->
<!-- $metaAuthor = Mikael Cedergren -->
<!-- $metaDescription = Short page description here -->
<!-- $metaKeywords = keyword one, keyword two -->
<!-- $ogImage = /assets/images/og-image.png -->
<!-- $ogTitle = About us -->
<!-- $ogDescription = Short page description here -->
<!-- $ogImageWidth = 1200 -->
<!-- $ogImageHeight = 630 -->
<!-- $canonicalUrl = https://faunapoolen.se/about/ -->
<!-- $alternateSvUrl = https://faunapoolen.se/about/ -->
<!-- $alternateEnUrl = https://faunapoolen.se/en/about/ -->

<!-- @include '/assets/components/_header.kit' -->
```

- Variables are simple strings.
- Declare variables before the include that needs them.
- Variables declared in a parent file are available inside included files after the declaration point.
- Variables declared inside an included file do not flow back up to the parent file.
- Use one variable per special comment.
- Undefined variables cause errors unless used with Kit's optional `?` syntax, such as `<!-- $pageTitle? -->`.
- Use `nil` when a variable should intentionally render as nothing.
- Current canonical header variables are `pageTitle`, `metaAuthor`, `metaDescription`, `metaKeywords`, `ogImage`, `ogTitle`, `ogDescription`, `ogImageWidth`, `ogImageHeight`, `canonicalUrl`, `alternateSvUrl`, and `alternateEnUrl`.
- Preserve existing meta values unless the user explicitly asks to customize SEO for a page.

## Important Paths

- Page sources: root `.kit` files and `*/index.kit` files.
- Blog posts: `blog/posts/*.kit`.
- Shared includes: `assets/components/*.kit`.
- Styles source: `assets/styles/styles.scss`.
- Style variables: `assets/styles/_variables.scss`.
- Generated CSS: `assets/styles/styles.css`.
- Scripts source: `assets/scripts/scripts.js`.
- Generated/minified script: `assets/scripts/scripts-min.js`.
- Images: `assets/images/`.
- CodeKit config: `config.codekit3`.
- English generator: `translate_site.py`.
- English translation config: `translate_site.config.json`.
- English translation plan: `TRANSLATION_PLAN.md`.
- English output: `en/`.
- Translation cache: `.translation-cache/sv-en.json`.
- Python dependencies: `requirements.txt`.
- CodeKit wake helper: `wake_codekit.py`.

## CodeKit Outputs

These files are generated outputs and should usually not be edited by hand:

- `.html` files next to their `.kit` sources.
- `assets/styles/styles.css` from `assets/styles/styles.scss`.
- `assets/scripts/scripts-min.js` from `assets/scripts/scripts.js`.
- `en/**/*.html` from `translate_site.py`.

If a task requires a publish-ready result, the generated files may need to be present in the final diff because the site is static. Let CodeKit generate them from the source files.

## English Translation Output

The English site is generated after CodeKit has produced the Swedish `.html` files.

- Use `translate_site.py` to generate matching English pages under `en/`.
- Do not run `translate_site.py`, including dry runs or real generation, unless the user explicitly asks for English generation or translation work. Treat English generation as an opt-in publish step; if a Swedish-only change leaves English output stale, say so instead of regenerating it.
- Translation config lives in `translate_site.config.json`.
- The full workflow is documented in `TRANSLATION_PLAN.md`.
- The script uses `.translation-cache/sv-en.json` to avoid paying to translate unchanged text again.
- Keep the cache unless the user intentionally wants to pay for a fresh translation pass.
- Install dependencies with `python3 -m pip install --user -r requirements.txt` if BeautifulSoup is missing.
- Real API translation requires `OPENAI_API_KEY`, typically loaded from `.env`. Never print or expose the key.
- Run `python3 translate_site.py --dry-run` before real translation.
- The script has hard cost guards: by default it blocks runs above 300 uncached strings or 50,000 uncached source characters. Do not bypass this. Use `--limit` for chunks, or deliberately raise the configured limit when the user approves a larger run.
- The script preserves Swedish originals and writes only under `en/`.
- Do not edit `en/**/*.html` directly unless explicitly asked. Change Swedish source/generator/cache and rerun the script.
- English generated headings and page title metadata should use European sentence capitalization, not American title case. The generator normalizes `h1`-`h6`, `<title>`, `og:title`, and `twitter:title` text during rendering; preserve proper nouns and product names through `heading_preserve_terms` in `translate_site.config.json`.
- CodeKit may generate docs HTML such as `AGENTS.html` or `TRANSLATION_PLAN.html`; keep these excluded from translation unless the user explicitly wants docs translated.
- After generation, verify `lang="en"`, rewritten `/en/` internal links, and visible text with DOM-based checks that ignore HTML comments.
- Some Swedish text exists in commented-out blocks in generated HTML. Do not count comment contents as visible mixed-language content.
- The script repairs the known malformed `og:image:width` / `og:image:height` header fragment in English output before parsing. If fixing that source issue in `_header.kit`, verify all Swedish generated pages carefully.

## Language Switcher

- Visible navigation lives in `assets/components/_navigation.kit`, not `_header.kit`.
- `_header.kit` is for document head, metadata, shared assets, and analytics.
- The language switcher is a global nav feature with markup in `_navigation.kit`, styling in `assets/styles/styles.scss`, and behavior in `assets/scripts/scripts.js`.
- The switcher uses flag-only UI with accessible labels. Current Swedish pages show the Swedish flag; generated English pages should show the English flag.
- `scripts.js` updates language links based on the current path, preserves query/hash, marks the active language with `aria-current`, and closes the dropdown when clicking outside it.
- Swedish language-switcher links intentionally point out of `/en/` and back to the original Swedish page. Other internal links in English output should stay under `/en/`.
- After changing the switcher markup, CodeKit may not rebuild every page from the shared include. Use the CodeKit waking workflow below and verify generated pages with `rg "language-switcher"` or `rg "language-flag"`.
- After changing switcher CSS or JS, verify `assets/styles/styles.css` and `assets/scripts/scripts-min.js` updated.

## Waking CodeKit

CodeKit can miss changes when many files are touched at once, especially shared `.kit` includes.

- Preferred workflow: run `python3 wake_codekit.py` after shared include changes or broad `.kit` edits. The helper prefers CodeKit's AppleScript `process file at path` command, batches the work, and reports whether generated `.html` mtimes changed.
- If AppleScript is unavailable, use `python3 wake_codekit.py --method pulse`. Pulse mode temporarily adds a newline to page `.kit` files, waits, restores the original source exactly, then checks generated output.
- To wake one stale page, run for that source file, for example `python3 wake_codekit.py blog/posts/small-features-for-small-spaces.kit`.
- Use `python3 wake_codekit.py --dry-run` to see which files would be pulsed.
- If the helper reports unchanged generated HTML, CodeKit is probably stopped or did not process the files. Ask the user to restart CodeKit, then rerun the helper.
- `touch` alone is not reliable; it can update timestamps without making CodeKit process the file.
- No-op rewrites are also unreliable. Prefer a real, harmless source edit such as adding or removing a blank line near the relevant include.
- Save or rewrite files in small batches, then wait roughly 6-10 seconds before checking generated outputs.
- For global include changes, first edit the shared include, wait, and check a representative generated page with `rg`.
- If some pages are stale, make a tiny whitespace-only edit in those specific `.kit` files and wait again instead of touching the whole site at once.
- Verify with timestamps and content checks, for example searching generated `.html` for the new class or text.
- Do not hand-edit generated `.html` just to force a result unless the user explicitly asks for that.

## Editing Guidelines

- Keep changes small and focused.
- Prefer existing components, classes, variables, and layout patterns.
- Use `assets/components/_navigation.kit` for global navigation changes.
- Use `assets/components/_footer.kit` for footer changes.
- Use `assets/components/_header.kit` for metadata, analytics, global head markup, and shared assets.
- Do not edit `config.codekit3` by hand. Use CodeKit UI for configuration changes.
- Preserve current SEO structure unless the user asks for a broader rewrite.
- Keep JavaScript minimal.
- Optimize new images for web before adding them.

## Copy And SEO

- Public-facing copy should usually be concise Swedish.
- If the user writes draft copy in English, translate it into natural Swedish for the site unless they ask otherwise.
- Headings use European/sentence capitalization in both Swedish and English: capitalize the first word and proper nouns/product names only. Do not use American title case such as `Natural Pools`, `Garden Care & Maintenance`, or `Frequently Asked Questions`.
- Keep headings clear and restrained. Avoid unnecessary fluff.
- Be careful with landing pages and SEO-sensitive pages. Prefer targeted edits over sweeping rewrites.

## Protected SEO Pages

These pages are known to perform very well in Google. Almost never change their content or metadata unless the user explicitly asks to edit that exact page.

- `blog/posts/difference-between-normal-pool-and-natural-pool.kit` generates `https://faunapoolen.se/blog/posts/difference-between-normal-pool-and-natural-pool.html`.
- `blog/posts/build-your-own-nature-pool.kit` generates `https://faunapoolen.se/blog/posts/build-your-own-nature-pool.html`.

## Verification

- After editing `.kit` files, check the matching generated `.html` if CodeKit updates it.
- After editing SCSS, check the generated CSS if CodeKit updates it.
- After editing JS, run `node --check assets/scripts/scripts.js` and check that CodeKit updates `assets/scripts/scripts-min.js`.
- After translation work, run `python3 translate_site.py --dry-run`; a complete cache should report `Missing translations: 0`.
- For generated English pages, prefer DOM-based verification with BeautifulSoup so HTML comments do not create false Swedish-content hits.
- For visual changes, preview through the CodeKit local server when available: `http://wolfbook.local:5757`.
- If the sandbox cannot resolve `wolfbook.local`, ask for or use approved local-network access for verification.
- Git is optional for verification. Use it only for read-only context when helpful, such as `git status`, `git diff`, `git log`, or `git show`.

## Git

- Do not commit, push, tag, rebase, reset, or otherwise change git history.
- Do not stage files unless the user explicitly asks.
- Only read from git. The working tree is managed by the user.

## Notes For Future Agents

- The README also contains project-specific assistant guidance. Read it when the task is broader than a tiny edit.
- The user may have CodeKit running locally. File saves from edits should trigger rebuilds, but if they do not, communicate that clearly.
- Do not revert unrelated user changes in the working tree.
