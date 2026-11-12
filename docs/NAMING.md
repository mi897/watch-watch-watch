# Naming your files

Jellyfin matches by folder and file name. Our tools never rename or move your files, so name them once and leave them.

```
movies/Heat (1995)/Heat (1995).mkv
shows/Show Name (2010)/Season 01/Show Name (2010) S01E01.mkv
anime/Series Name/Season 01/Series Name S01E01.mkv
cartoons/Show Name/Season 02/Show Name S02E05.mp4
```

- Put the year in parentheses for movies and for shows that share a name with others.
- Use `SxxExx`. For double episodes use `S01E01-E02`.
- Specials go in `Season 00`.
- Keep one library per type: movies and TV never in the same folder.
- Scene tags (`1080p`, `x265`, release groups) are tolerated but anything Jellyfin cannot match will be flagged in the review queue (Phase 4).

Authoritative reference: Jellyfin's own docs on media naming (docs.jellyfin.org).
