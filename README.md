# `do2obs`

Other DayOne to Obsidian converters exist, but they don't really format stuff the way I want, and it can't be *that* hard, right?

## Plan

- [X] Rename photos to YYYY-MM-DD-HHMM
- [X] Output files should be YYYY-MM-DD-HHMM.md
- [X] Location metadata should conform to the obsidian-map-view pattern
- [X] Create tags and frontmatter to indicate journal source
- [X] Preserve tags
- [X] Recover corrupted photos.
  - Basic outline:
    - Search for `.json` and `.zip` files in given backup dir
    - Look for broken photo
    - Retry copy
- [ ] Preserve stars
