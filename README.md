# VNBank-LOD · Group 24 · Final submission

IT6390E Semantic Web, Hanoi University of Science and Technology. Supervisor: Dr. Đỗ Bá Lâm.

| Member | Student ID |
|---|---|
| Đinh Thị Lan Hương | 20261261M |
| Vũ Đức Thành | 20261082M |
| Nguyễn Khắc Duy Ngọc | 20261206M |
| Ngô Quang Minh | 20252084M |

## Contents

| Folder | Files |
|---|---|
| `01_Report/` | Report in English (10 pages) and Vietnamese (10 pages), LaTeX source |
| `02_Slides/` | Presentation (18 slides, about 10 minutes, 4 speakers, speaker notes included) |
| `03_Video/` | Demonstration video (3:05, 1920×1080) and English subtitles |
| `04_Source_Code_and_Data/` | Turtle dataset, CSV and Excel tables, notebook (SPARQL terminal, 16 queries), query results, scripts |

## Quick start

- Data: `04_Source_Code_and_Data/data/vietnam-banking.ttl` (1,067 triples, 30 banks, 38 `owl:sameAs` links).
- Notebook: open `04_Source_Code_and_Data/notebook/Group_24_Semantic_Web_project_final.ipynb` in Google Colab or Jupyter and run all cells.
- Command line: `pip install rdflib owlrl`, then `python scripts/validate_and_query.py` inside `04_Source_Code_and_Data/`.
- Protégé: open the Turtle file and start the HermiT reasoner.

Public repository: https://github.com/Huongdinh91/vietnam-banking-lod
