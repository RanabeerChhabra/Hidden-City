"""Saves cleaned results to a SQLite database and CSV files in data/.

The cache is the source of truth, so these files are rebuilt from scratch every time.
"""

import csv
import sqlite3

from hiddencity import config

DB_PATH = config.DATA_DIR / "results.db"


def write_table(connection, name, rows):
    connection.execute(f"DROP TABLE IF EXISTS {name}")
    if not rows:
        return
    columns = list(rows[0].keys())
    connection.execute(f"CREATE TABLE {name} ({', '.join(columns)})")
    placeholders = ", ".join("?" for _ in columns)
    connection.executemany(
        f"INSERT INTO {name} VALUES ({placeholders})",
        [[row[c] for c in columns] for row in rows],
    )


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_results(itineraries, opportunities):
    config.DATA_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        write_table(connection, "itineraries", itineraries)
        write_table(connection, "opportunities", opportunities)
    write_csv(config.DATA_DIR / "itineraries.csv", itineraries)
    write_csv(config.DATA_DIR / "opportunities.csv", opportunities)
