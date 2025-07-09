"""Database script for swimming world records."""

import sqlite3


def main() -> None:
    """Run the database script."""
    con = sqlite3.connect("wrs.db")
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS records (
                stroke TEXT,
                distance INT,
                course TEXT,
                time REAL,
                swimmer TEXT,
                date TEXT,
                location TEXT)""")
    cur.execute("""INSERT INTO records (stroke, distance, course, time, swimmer, date, location)
                VALUES ('Freestyle', 50, 'Short Course', 20.91, 'Caeleb Dressel', '2021-07-26', 'Tokyo')""")
    cur.execute("""SELECT rowid, * FROM records""")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    con.commit()
    con.close()

if __name__ == "__main__":
    main()
