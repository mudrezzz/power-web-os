from __future__ import annotations

from power_web_os.integrations.signal_source_metadata import _date_candidates


def test_signal_source_metadata_extracts_publication_date_candidates() -> None:
    html = """
    <html><head>
      <script type="application/ld+json">{"datePublished": "2026-06-10T12:00:00+03:00"}</script>
      <meta property="article:published_time" content="2026-06-11T00:00:00Z">
    </head></html>
    """

    candidates = _date_candidates(html)

    assert (1, "2026-06-10", "json_ld") in candidates
    assert (2, "2026-06-11", "open_graph") in candidates


def test_signal_source_metadata_ignores_date_modified_as_publication_evidence() -> None:
    html = '<meta property="article:modified_time" content="2026-07-01T00:00:00Z">'

    assert _date_candidates(html) == []
