# Isaac Lab Chinese Documentation Rules

- Use the official Isaac Lab v2.3.2 documentation and source code as the
  exclusive translation baseline. Do not mix content from other versions.
- Translate all tutorial titles, prose, notes, captions, tables, and navigation
  labels into Chinese.
- Preserve Isaac Lab, Isaac Sim, Omniverse, robotics, and API concepts in
  English when translating them would reduce technical precision.
- Prefer natural, coherent Chinese sentence structure over word-for-word
  translation. Retain English only for necessary technical concepts and API
  identifiers; translate ordinary connective and descriptive wording into
  fluent Chinese.
- Capitalize the first letter of retained English terms in prose and render
  them with the shared `term` emphasis style.
- Preserve API identifiers, file names, paths, commands, keyboard shortcuts,
  inline code, and code-block text exactly as written in the official source.
- Give inline code a high-contrast background, border, and text color.
- Mark every standalone code block with its language. Use at least
  `language-python` for Python and `language-bash` for shell commands so local
  syntax highlighting is activated.
- Never translate or reformat executable source code. Verify complete embedded
  scripts byte-for-byte against the official v2.3.2 files.
- Preserve the official tutorial hierarchy and reading order. Each page must
  include the shared sidebar, page table of contents, previous/next navigation,
  light and dark themes, directory search, and code-copy controls.
- Label the sidebar root link `IsaacLab Tutorial`. Keep the sidebar typography
  hierarchy visually explicit: the root link must be largest, section headings
  must be larger and bolder than tutorial-page links, and page links must remain
  subordinate.
- Render exactly one page-level `h1`. Remove any upstream `h1` retained inside
  the imported article before adding the translated page title.
- Do not number the page-level `h1`. Number second-level headings as `1`, `2`,
  and so on; number third-level headings as `1.1`, `1.2`, and so on; extend the
  same hierarchy to lower levels. Rebuild the page table of contents from the
  numbered headings so its labels always match the visible heading numbers.
- Store required images and static assets locally. Tutorial browsing must not
  require a network connection; links outside the translated tutorial scope may
  continue to point to the official v2.3.2 documentation.
- Preserve upstream copyright notices and add a clear unofficial Chinese
  translation notice with a link to the corresponding official page.
- Keep all local links and heading anchors valid. Run link, asset, HTML, and
  code-fidelity checks before considering a page complete.
