# Election Data Analysis Project

## How to Use This Project (EN)

This guide is simplified for absolute beginners:

### Step-by-Step:

1. Run `main.py`:
   This script scrapes all necessary links from 2017 elections data (towns and municipalities).
   ```sh
   python main.py
   ```

2. Run `1+1.py`:
   This script downloads all voting data for 2013 and 2021 elections and saves them into CSV files.
   ```sh
   python 1+1.py
   ```

3. Load Data into PostgreSQL:
   - If you don’t want to scrape data, use the provided dump file with already-scraped data for your local PostgreSQL database.
   - Alternatively, use the following SQL script in DBeaver or another SQL client to create a unified dataset:

   ```sql
   DROP VIEW IF EXISTS votes_summary CASCADE;

   CREATE VIEW votes_summary AS
   SELECT
       CAST(pr.obec_id AS VARCHAR) AS obec_id,
       pr.strana_id,
       p.party_name,
       CAST(es.kraj_id AS VARCHAR) AS kraj_id,
       k.kraj_nazev,
       es.obec_nazev,
       SUM(CAST(pr.hlasy AS INTEGER)) AS hlasy,
       '2013' AS year
   FROM party_results_2013 pr
   JOIN election_summary_2013 es ON CAST(pr.obec_id AS VARCHAR) = CAST(es.obec_id AS VARCHAR)
   JOIN kraj_summary k ON CAST(es.kraj_id AS VARCHAR) = CAST(k.kraj_id AS VARCHAR)
   JOIN parties p ON pr.strana_id = p.strana_id
   GROUP BY pr.obec_id, pr.strana_id, p.party_name, es.kraj_id, k.kraj_nazev, es.obec_nazev
   UNION ALL
   SELECT
       CAST(pr.obec_id AS VARCHAR) AS obec_id,
       pr.strana_id,
       p.party_name,
       CAST(es.kraj_id AS VARCHAR) AS kraj_id,
       k.kraj_nazev,
       es.obec_nazev,
       SUM(CAST(pr.hlasy AS INTEGER)) AS hlasy,
       '2017' AS year
   FROM party_results_2017 pr
   JOIN election_summary_2017 es ON CAST(pr.obec_id AS VARCHAR) = CAST(es.obec_id AS VARCHAR)
   JOIN kraj_summary k ON CAST(es.kraj_id AS VARCHAR) = CAST(k.kraj_id AS VARCHAR)
   JOIN parties p ON pr.strana_id = p.strana_id
   GROUP BY pr.obec_id, pr.strana_id, p.party_name, es.kraj_id, k.kraj_nazev, es.obec_nazev
   UNION ALL
   SELECT
       CAST(pr.obec_id AS VARCHAR) AS obec_id,
       pr.strana_id,
       p.party_name,
       CAST(es.kraj_id AS VARCHAR) AS kraj_id,
       k.kraj_nazev,
       es.obec_nazev,
       SUM(CAST(pr.hlasy AS INTEGER)) AS hlasy,
       '2021' AS year
   FROM party_results_2021 pr
   JOIN election_summary_2021 es ON CAST(pr.obec_id AS VARCHAR) = CAST(es.obec_id AS VARCHAR)
   JOIN kraj_summary k ON CAST(es.kraj_id AS VARCHAR) = CAST(k.kraj_id AS VARCHAR)
   JOIN parties p ON pr.strana_id = p.strana_id
   GROUP BY pr.obec_id, pr.strana_id, p.party_name, es.kraj_id, k.kraj_nazev, es.obec_nazev;
   ```

4. Export Data to Power BI or CSV:
   After running the SQL script, export the filtered dataset:
   ```sql
   SELECT * FROM votes_summary WHERE kraj_id = 'CZ0201' AND hlasy > 0;
   ```

## Jak používat tento projekt (CZ)

Tento návod je napsán jednoduše pro úplné začátečníky:

### Krok za krokem:

1. Spusťte `main.py`:
   Tento skript parsuje všechny potřebné odkazy z volebních dat z roku 2017 (obce a města).
   ```sh
   python main.py
   ```

2. Spusťte `1+1.py`:
   Tento skript stáhne všechna hlasovací data z let 2013 a 2021 a uloží je do CSV souborů.
   ```sh
   python 1+1.py
   ```

3. Načtení dat do PostgreSQL:
   - Pokud nechcete parsovat data, použijte přiložený dump již připravených dat pro lokální databázi PostgreSQL.
   - Nebo použijte následující SQL skript v DBeaveru nebo jiném SQL klientovi k vytvoření sjednocené databáze:

   _(SQL skript je uveden výše)_

4. Export dat do Power BI nebo CSV:
   Po spuštění SQL skriptu exportujte filtrovaná data:
   ```sql
   SELECT * FROM votes_summary WHERE kraj_id = 'CZ0201' AND hlasy > 0;
   ```

---

**Project Overview**
- Automated election data scraping (2013, 2017, 2021)
- Data transformation and PostgreSQL integration
- Power BI-ready structured dataset

