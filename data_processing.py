import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Připojení k databázi
DB_NAME = "election_data"
USER = "postgres"
PASSWORD = "123"
HOST = "localhost"
PORT = "5432"

engine = create_engine(f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}")

# Načtení dat z databáze
party_results_2013 = pd.read_sql("SELECT * FROM party_results_2013", engine)
party_results_2017 = pd.read_sql("SELECT * FROM party_results_2017", engine)
party_results_2021 = pd.read_sql("SELECT * FROM party_results_2021", engine)
parties = pd.read_sql("SELECT * FROM parties", engine)
kraj_summary = pd.read_sql("SELECT * FROM kraj_summary", engine)
election_summary_2013 = pd.read_sql("SELECT * FROM election_summary_2013", engine)
election_summary_2017 = pd.read_sql("SELECT * FROM election_summary_2017", engine)
election_summary_2021 = pd.read_sql("SELECT * FROM election_summary_2021", engine)

print("Data byla úspěšně načtena!")

# Převod kraj_id na uppercase, aby odpovídalo formátu v databázi
election_summary_2013["kraj_id"] = election_summary_2013["kraj_id"].str.upper()
election_summary_2017["kraj_id"] = election_summary_2017["kraj_id"].str.upper()
election_summary_2021["kraj_id"] = election_summary_2021["kraj_id"].str.upper()
kraj_summary["kraj_id"] = kraj_summary["kraj_id"].astype(str).str.upper()

# Spojení kraj_summary s election_summary_* podle kraj_id
election_summary_2013 = election_summary_2013.merge(kraj_summary, on="kraj_id", how="left")
election_summary_2017 = election_summary_2017.merge(kraj_summary, on="kraj_id", how="left")
election_summary_2021 = election_summary_2021.merge(kraj_summary, on="kraj_id", how="left")

print("Data spojena: kraj_summary + election_summary_* podle kraj_id!")

# Uživatel zadává kraj_id v jakémkoliv formátu (převedeme na uppercase)
kraj_filter = input("Zadejte kraj_id (např. CZ0311): ").strip().upper()

# Filtrování obcí podle vybraného kraje
filtered_cities = election_summary_2021[election_summary_2021["kraj_id"] == kraj_filter]

print(f"Vybrané obce v regionu {kraj_filter}:")
print(filtered_cities[["obec_id", "obec_nazev"]].head(10))  # Ukážeme prvních 10 obcí

# Kontrola sloupců před spojením s parties
print("Sloupce v 'party_results_2013' před merge:", party_results_2013.columns.tolist())

# Spojení dat s názvy stran podle 'strana_id'
party_results_2013 = party_results_2013.merge(parties, on="strana_id", how="left")
party_results_2017 = party_results_2017.merge(parties, on="strana_id", how="left")
party_results_2021 = party_results_2021.merge(parties, on="strana_id", how="left")

print("Sloupce v 'party_results_2013' po merge:", party_results_2013.columns.tolist())
print("Data byla úspěšně spojena s názvy stran!")

# Oprava názvu sloupce v parties, pokud existuje jiný název
if "název_strany" in parties.columns:
    parties = parties.rename(columns={"název_strany": "party_name"})

# Spojení party_results_* s election_summary_* podle obec_id
party_results_2013 = party_results_2013.merge(election_summary_2013, on="obec_id", how="left")
party_results_2017 = party_results_2017.merge(election_summary_2017, on="obec_id", how="left")
party_results_2021 = party_results_2021.merge(election_summary_2021, on="obec_id", how="left")

print("Data byla úspěšně spojena s volebními souhrny!")

# Funkce pro agregaci hlasů podle obec_id
def aggregate_votes(df, year):
    grouped = df.groupby(["obec_id", "party_name"])["hlasy"].sum().reset_index()
    grouped["year"] = year  # Přidáme sloupec s rokem
    return grouped

# Aplikace funkce na všechna volební období
votes = pd.concat([
    aggregate_votes(party_results_2013, 2013),
    aggregate_votes(party_results_2017, 2017),
    aggregate_votes(party_results_2021, 2021)
], ignore_index=True)

print("Agregovaná data připravena!")

# Převod hlasy na integer (pokud jsou ve formátu string)
votes["hlasy"] = pd.to_numeric(votes["hlasy"], errors="coerce").fillna(0).astype(int)

# Filtrování hlasů pouze pro vybraný kraj a odstranění stran s nulovými hlasy
votes = votes[votes["obec_id"].isin(filtered_cities["obec_id"])]
votes = votes[votes["hlasy"] > 0]

print(f"Data byla filtrována pro kraj_id {kraj_filter}!")

# Export do CSV pro Power BI
votes.to_csv("election_results_filtered.csv", index=False, encoding="utf-8")
print("Data byla uložena do election_results_filtered.csv!")

# Zobrazení top 5 stran podle hlasů
top5 = (
    votes.groupby("party_name")["hlasy"]
    .sum()
    .reset_index()
    .sort_values(by="hlasy", ascending=False)
    .head(5)
)

print("\nTop 5 stran podle hlasů:")
print(top5)

# Vykreslení grafu vývoje hlasů stran podle let
plt.figure(figsize=(10, 5))
for party in votes["party_name"].unique():
    subset = votes[votes["party_name"] == party]
    plt.plot(subset["year"], subset["hlasy"], marker="o", label=party)

plt.xlabel("Rok voleb")
plt.ylabel("Počet hlasů")
plt.title("Vývoj hlasů stran podle let")
plt.legend()
plt.show()