from pathlib import Path
import csv
import json
from collections import Counter

root = Path(__file__).resolve().parents[2]

def annual(relative):
    with (root / relative).open(encoding='utf-8-sig', newline='') as handle:
        return Counter(int(row['publication_year']) for row in csv.DictReader(handle))

u = annual('01_Corpus/01_Included_Publications_U.csv')
t = annual('03_Analysis_Sets/01_IoT_Including_Edge_SHM_T.csv')
b = annual('03_Analysis_Sets/02_Bridge_SHM_B.csv')
bt = annual('03_Analysis_Sets/04_Bridge_IoT_Including_Edge_SHM.csv')
e = annual('03_Analysis_Sets/03_Edge_SHM_E.csv')
rows = []
for year in sorted(u):
    percent = lambda numerator, denominator: 100 * numerator / denominator if denominator else 0
    rows.append(dict(year=year, U=u[year], T=t[year], B=b[year], bridge_T=bt[year], E=e[year],
                     remaining_U=u[year]-t[year], remaining_B=b[year]-bt[year], T_without_E=t[year]-e[year],
                     T_percent_of_U=percent(t[year],u[year]), bridge_T_percent_of_B=percent(bt[year],b[year]),
                     E_percent_of_T=percent(e[year],t[year])))
assert sum(u.values()) == 21840 and sum(t.values()) == 863
assert sum(b.values()) == 5833 and sum(bt.values()) == 261 and sum(e.values()) == 158
print(json.dumps(rows, indent=2))
