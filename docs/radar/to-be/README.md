# Radar Pipeline TO BE Designs

Use this folder for reviewed TO BE designs before substantial Radar search
pipeline changes.

Filename convention:

```text
RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md
RADAR_SEARCH_PIPELINE_TO_BE_<slice>.pdf
```

Every TO BE design must have both Markdown and PDF review artifacts. Generate
the PDF from the Markdown with:

```bash
python scripts/render_radar_pipeline_doc.py --source docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md --output docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.pdf
```

The Markdown may keep Mermaid source blocks for GitHub readability. The PDF
must contain rendered diagrams or controlled diagram flowables, not raw Mermaid
notation.

After implementation, compare the TO BE document with actual behavior, update
`docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`, regenerate
`docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf`, and record any remaining gaps in
`ROADMAP.md`.
