# Faunapoolen Website

Static marketing site for Faunapoolen (naturpooler + waterscapes). Built with CodeKit so `.kit` templates compile into `.html`. This README is written for AI assistants and non-technical editors.

## Quick Start (CodeKit is required)
- Open CodeKit and add this repo folder.
- CodeKit watches `.kit` and `.scss` files and auto-renders `.html` and `.css`.
- Always edit `.kit` files (not `.html`). The HTML files are generated.

## Project Structure (what to edit)
- Page sources: root `.kit` files and `*/index.kit` files (e.g. `index.kit`, `about/index.kit`, `contact/index.kit`).
- Blog list: `blog/index.kit` (each entry is a link block).
- Blog posts: `blog/posts/*.kit` (each post has a matching generated `.html`).
- Shared layout/includes: `assets/components/*.kit` (header, footer, nav, CTAs, etc). Files prefixed with `_` are include-only and are not rendered by CodeKit.
- Styles: `assets/styles/styles.scss` (compiled to `assets/styles/styles.css`).
- Style tokens/variables: `assets/styles/_variables.scss`.
- Scripts: `assets/scripts/scripts.js` (compiled/minified to `assets/scripts/scripts-min.js`).
- Images: `assets/images/`.
- CodeKit config: `config.codekit3` (do not edit by hand).

## Editing Rules (important)
- Edit `.kit` files only. CodeKit generates `.html` automatically.
- Keep includes intact: `<!-- @include '/assets/components/_header.kit' -->`.
- Update global navigation in `assets/components/_navigation.kit`.
- Update footer links/text in `assets/components/_footer.kit`.
- CSS/SCSS: Prefer existing variables and utility patterns in `assets/styles/` and avoid one-off styles.
- SEO: Favor small, structured edits over large rewrites to protect current Google ranking performance.
- JavaScript: Keep JS minimal; only add scripts when absolutely necessary.
- Headings are sentence case.

## Common Tasks
### Update page copy
1. Open the relevant `.kit` file.
2. Edit text or images.
3. Save; CodeKit rebuilds the `.html`.

### Add a new page
1. Copy an existing `.kit` page as a starting point.
2. Adjust the content and save.
3. CodeKit outputs the matching `.html`.
4. Add the new link to `assets/components/_navigation.kit` and `assets/components/_footer.kit`.

### Add a blog post
1. Duplicate `blog/posts/blog-post-template.kit`.
2. Update the title, content, image paths, and slug in the filename.
3. Add a new entry block in `blog/index.kit` linking to the new `.html`.

## Secrets / .env (AI tooling)
This site is static and does not currently use runtime secrets. If you add AI scripts or local tooling:
- Create a local `.env` file with keys like `OPENAI_API_KEY=...`.
- Do not commit `.env` to git (add it to `.gitignore` if needed).

## Output Files (generated)
- `.html` files next to their `.kit` sources (do not edit directly).
- `assets/styles/styles.css` from `assets/styles/styles.scss`.
- `assets/scripts/scripts-min.js` from `assets/scripts/scripts.js`.

## Notes for AI Assistants
- Prefer editing `.kit` templates and SCSS source files.
- Keep the CodeKit include comments and file paths unchanged unless you intentionally restructure the site.
- Avoid editing `config.codekit3` directly; use CodeKit UI.
- Use the existing light CSS framework and variables; avoid special-case CSS.
- Keep changes minimal to protect current SEO performance.
- Copy tone: Swedish-first site; keep wording tight and avoid fluff or repetition (except SEO-driven blog content).
- Business context: Mikael is the director; landing pages should balance CTR/SEO with high-value customer conversions (not window shoppers).
- Forms: Contact forms submit via Formspree (`https://formspree.io`).
- Header/meta/analytics live in `assets/components/_header.kit`; do not change tracking IDs without approval.
- When Ben writes in English, translate all public-facing copy to concise, correct Swedish.
- Guide Ben step by step and warn clearly if a request could hurt Google ranking.

## Publishing
- Hosted on GitHub Pages with a custom domain (see `CNAME`).

## Local Preview
- Use the CodeKit built-in server to preview changes locally.

## Images
- Place new images under `assets/images/` following existing folder patterns (e.g. `assets/images/blog/`, `assets/images/services/`, `assets/images/pricing/`).
- Optimize images for web; avoid overly large resolutions.
