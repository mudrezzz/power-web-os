# Power Web discovery source capability matrix

Status: architecture baseline for slice `0.7.6.6.0`.

| Source | Access | Allowed use | Retained fields | Freshness | Outcome |
|---|---|---|---|---|---|
| `hh_public_web` | Ordinary web search restricted to `hh.ru` | Indexed result discovery and public-page read | URL, title, safe snippet, public role/employer/geography, fingerprints | Search-index dependent | `public_search_only` |
| `official_company` | Public web | Official people, unit, publication and event pages | Public metadata, dates and safe excerpt | Source dependent | `available` |
| `professional_networks` | Public search only | Indexed public profile metadata | Name/headline/employer/location/profile URL | Profile dependent | `public_search_only` |
| `publications_events` | Public web | Authors, speakers and participation | Person, organization, title, date, URL and excerpt | Usually dated | `available` |
| `procurement_patents` | Public records | Named participants and dated organizational records | Person, organization, role, record date/URL | Record dependent | `available` |
| `industry_web` | Public web | Recall-oriented industry sources | Public metadata, dates and excerpt | Source dependent | `available` |
| `generic_web` | Public web | Recall-oriented discovery and gap filling | URL, title, snippet and public metadata | Unknown until validated | `available` |
| `image_evidence` | Public metadata only | Exact/perceptual duplicate fingerprints | Source URL and fingerprints; no image binary | Not applicable | `available` |
| `hh_authorized_api` | Employer OAuth/licensed API | None until approved | None | Unavailable | `deferred` |

All active lanes use bounded search/verification budgets. Common governance:
public product-safe metadata only, no private contacts, no automated outreach,
no authorization/CAPTCHA/robots bypass and no raw page/provider payload
retention. Image evidence additionally forbids face embeddings and reverse-face
search.
