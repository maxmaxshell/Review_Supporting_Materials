# Literature records and core analysis code

| Folder | Contents |
| --- | --- |
| 01_Corpus | Included publications U, research articles and reviews |
| 02_Scope_Groups | Overlapping G1–G8 groups defined in Table S1.1 |
| 03_Analysis_Sets | U, B, I, E and T subsets used in the manuscript |
| 04_Topic_Groups | Ten Figure 4 topics and records with no topic match |
| 05_Method_Definitions | Selected journals, scope expressions, topic expressions and Figure 4 counts |
| 06_Core_Code | Metadata, screening and scope/topic functions with offline examples |

`00_File_List.csv` lists all files and record counts. Record CSVs contain OpenAlex ID, title, DOI, publication year, journal and screened document type. Missing fields remain blank. Publisher-enriched text is excluded. Group and topic lists overlap; do not add their counts to obtain a corpus total.

Membership follows the manuscript's included study sets. The record fields alone do not reconstruct classifications that used supplemented metadata. The extracted core functions and rule constants retain their original logic; examples provide minimal calling code. Screening functions return rule candidates for review, not the complete adjudicated screening history.

Python 3.9 or later is required; only the standard library is used. Run from this folder:

```text
python 06_Core_Code/examples/01_Metadata_Example.py
python 06_Core_Code/examples/02_Screening_Example.py
python 06_Core_Code/examples/03_Deduplication_Example.py
python 06_Core_Code/examples/04_Scope_and_Topic_Example.py
python 06_Core_Code/examples/05_Annual_Counting_Example.py
```

Examples 01–04 use synthetic inputs and make no network requests. Example 05 counts the supplied manuscript record lists. Figure 4 uses a 15% descriptive threshold. The 2026 data cover January–June.
