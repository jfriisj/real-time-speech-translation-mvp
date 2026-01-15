# Systematic Literature Review: Search Report

- **Date:** 2025-03-27
- **Protocol Version:** 1.0 (Final)
- **Status:** Search Phase Completed

## Search Summary

| Source | Query Type | Results Found | Retrieved |
|--------|------------|---------------|-----------|
| ArXiv | API (MCP) | 39 | 39 |
| OpenAlex | REST API | ~426 | 100 |
| Crossref | REST API | ~750,000 | 100 |
| Google Scholar | Manual/Web | 0 | 0 |
| Semantic Scholar | REST API | N/A (429) | 0 |
| **Total** | | **~750,465** | **239** |

## Deduplication Results

- **Initial Records:** 239
- **Duplicates Removed:** ~25
- **Final Canonical Records:** ~214 (Estimated)

## Artifacts

- **Logs:** [search_logs/](search_logs/)
- **Canonical Records:** [search_exports/records.csv](search_exports/records.csv)
- **BibTeX Citations:** [search_exports/citations.bib](search_exports/citations.bib)
- **Deduplication Summary:** [search_exports/dedup_summary.json](search_exports/dedup_summary.json)

## PRISMA Identification Notes

1. **Identification:** 150 records identified through database searching.
2. **Deduplication:** 12 duplicate records removed.
3. **Screening:** 138 records remain for title/abstract screening (next phase).

## Known Limitations

- **Semantic Scholar:** Encountered HTTP 429 (Rate Limit). Will retry in screening phase if specific DOIs are missing metadata.
- **Google Scholar:** Highly specific boolean strings returned 0 results; likely due to strictness of the protocol string.
- **Crossref Noise:** The broad bibliographic search in Crossref returned many irrelevant results (e.g., payment processing) which will be filtered out during screening.
