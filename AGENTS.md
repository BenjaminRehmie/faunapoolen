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

<!-- @include '/assets/components/_header.kit' -->
```

- Variables are simple strings.
- Declare variables before the include that needs them.
- Variables declared in a parent file are available inside included files after the declaration point.
- Variables declared inside an included file do not flow back up to the parent file.
- Use one variable per special comment.
- Undefined variables cause errors unless used with Kit's optional `?` syntax, such as `<!-- $pageTitle? -->`.
- Use `nil` when a variable should intentionally render as nothing.
- Current canonical header variables are `pageTitle`, `metaAuthor`, `metaDescription`, `metaKeywords`, `ogImage`, `ogTitle`, `ogDescription`, `ogImageWidth`, and `ogImageHeight`.
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

## CodeKit Outputs

These files are generated outputs and should usually not be edited by hand:

- `.html` files next to their `.kit` sources.
- `assets/styles/styles.css` from `assets/styles/styles.scss`.
- `assets/scripts/scripts-min.js` from `assets/scripts/scripts.js`.

If a task requires a publish-ready result, the generated files may need to be present in the final diff because the site is static. Let CodeKit generate them from the source files.

## Waking CodeKit

CodeKit can miss changes when many files are touched at once, especially shared `.kit` includes.

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
- Keep headings clear and restrained. Avoid unnecessary fluff.
- Be careful with landing pages and SEO-sensitive pages. Prefer targeted edits over sweeping rewrites.

## Protected SEO Pages

These pages are known to perform very well in Google. Almost never change their content or metadata unless the user explicitly asks to edit that exact page.

- `blog/posts/difference-between-normal-pool-and-natural-pool.kit` generates `https://faunapoolen.se/blog/posts/difference-between-normal-pool-and-natural-pool.html`.
- `blog/posts/build-your-own-nature-pool.kit` generates `https://faunapoolen.se/blog/posts/build-your-own-nature-pool.html`.

## Verification

- After editing `.kit` files, check the matching generated `.html` if CodeKit updates it.
- After editing SCSS, check the generated CSS if CodeKit updates it.
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
