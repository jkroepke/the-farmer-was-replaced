# External Reference Archive

This directory is the local provenance/archive layer for external TFWR research.

Each source uses:

```text
external/<name>/
├── README.md
└── source/
```

- `README.md` contains provenance, summary, revision and validity notes.
- `source/` contains an unchanged upstream snapshot when redistribution is permitted or the original content was supplied by the user.
- If a verbatim snapshot cannot be redistributed or fetched, `source/UPSTREAM.md` records the upstream location and why the body is absent.

Do not edit mirrored source files to fit this project. Adaptations belong in normal project files or benchmarks.
