import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm

# Načtení souboru links.csv (vytvořeného pro rok 2017)
soubor_cesta = "links.csv"
links_df = pd.read_csv(soubor_cesta)

# Filtrujeme řádky, které nemají odkaz na ps311
links_df = links_df.dropna(subset=["ps311_Obec_Link"])


# Funkce pro zpracování volební statistiky
def zpracovat_statistiky(url, kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání stránky {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    try:
        stats_table = soup.find("table", {"id": "ps311_t1"})
        if not stats_table:
            print(f"Tabulka statistik nebyla nalezena na stránce {url}")
            return None
        stats = stats_table.find_all("td", class_="cislo")
        if len(stats) < 9:
            print(f"Nedostatek statistických dat na stránce {url}")
            return None

        data = [
            kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev,
            stats[0].text.strip(), stats[1].text.strip(), stats[2].text.strip(),
            stats[3].text.strip(), stats[4].text.strip(), stats[5].text.strip(),
            stats[6].text.strip(), stats[7].text.strip()
        ]
        return data
    except Exception as e:
        print(f"Chyba při zpracování statistik pro {url}: {e}")
        return None


# Funkce pro zpracování výsledků stran
def zpracovat_vysledky_stran(url, kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání stránky {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    strany_data = []
    tabulka_radky = soup.find_all("tr")
    for radek in tabulka_radky:
        sloupce = radek.find_all("td")
        if len(sloupce) >= 4:
            strana_nazev = sloupce[1].text.strip()
            hlasy = sloupce[2].text.strip()
            procenta = sloupce[3].text.strip()
            # Pokud hlasy nebo procenta nejsou, nastavíme na 0
            if hlasy == "":
                hlasy = "0"
            if procenta == "":
                procenta = "0"
            strany_data.append([
                kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev,
                strana_nazev, hlasy, procenta
            ])
    return strany_data


# Definujeme roky pro zpracování
roky = [2013, 2017, 2021]

for rok in roky:
    print(f"\n===== Zpracování dat pro rok {rok} =====")

    # Seznamy pro ukládání dat pro aktuální rok
    odkazy_rok = []  # Aktualizované odkazy pro daný rok
    volebni_statistiky = []  # Volební statistiky
    vysledky_stran = []  # Výsledky stran

    # Pro vytvoření sady stran a kontrolu na úrovni obcí
    master_party_set = set()  # Všechny nalezené názvy stran pro rok
    municipality_party_dict = {}  # Klíč: (kraj_id, okres_id, obec_id) -> set(názvů stran)

    # Aktualizujeme odkazy pro daný rok
    for idx, row in links_df.iterrows():
        kraj_id = row["Kraj_ID"]
        kraj_nazev = row["Kraj_Název"]
        okres_id = row["Okres_ID"]
        okres_nazev = row["Okres_Název"]
        obec_id = row["Obec_ID"]
        obec_nazev = row["Obec_Název"]
        original_link = row["ps311_Obec_Link"]

        # Přizpůsobíme odkaz pro daný rok:
        # 2017 – beze změny, 2013 – nahradíme "ps2017nss" za "ps2013", 2021 – za "ps2021"
        if rok == 2017:
            new_link = original_link
        elif rok == 2013:
            new_link = original_link.replace("ps2017nss", "ps2013")
        elif rok == 2021:
            new_link = original_link.replace("ps2017nss", "ps2021")
        else:
            new_link = original_link

        odkazy_rok.append([kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev, new_link])

    # Uložíme soubor s odkazy pro aktuální rok
    odkazy_soubor = f"odkazy_{rok}.csv"
    pd.DataFrame(odkazy_rok, columns=[
        "Kraj_ID", "Kraj_Název", "Okres_ID", "Okres_Název", "Obec_ID", "Obec_Název", "ps311_Obec_Link"
    ]).to_csv(odkazy_soubor, index=False, encoding="utf-8")
    print(f"Odkazy uložené: {odkazy_soubor}")

    # Zpracování dat pro každou obec (podle aktualizovaných odkazů)
    for row in tqdm(odkazy_rok, desc=f"Zpracování obcí pro rok {rok}", total=len(odkazy_rok)):
        kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev, new_link = row

        # Zpracujeme volební statistiky
        data_statistiky = zpracovat_statistiky(new_link, kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev)
        if data_statistiky:
            volebni_statistiky.append(data_statistiky)

        # Zpracujeme výsledky stran
        data_strany = zpracovat_vysledky_stran(new_link, kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev)
        key = (kraj_id, okres_id, obec_id)
        if key not in municipality_party_dict:
            municipality_party_dict[key] = set()
        for pr in data_strany:
            strana_nazev = pr[6]
            master_party_set.add(strana_nazev)
            municipality_party_dict[key].add(strana_nazev)
            vysledky_stran.append(pr)

        time.sleep(0.1)  # Pauza pro prevenci blokace

    # Ověříme, zda jsou přítomny všechny strany v každé obci.
    for mun in odkazy_rok:
        kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev, _ = mun
        key = (kraj_id, okres_id, obec_id)
        existing_parties = municipality_party_dict.get(key, set())
        for strana in master_party_set:
            if strana not in existing_parties:
                vysledky_stran.append([
                    kraj_id, kraj_nazev, okres_id, okres_nazev, obec_id, obec_nazev,
                    strana, "0", "0"
                ])

print("\n✅ Hotovo! Pro každý rok byly vytvořeny soubory odkazy, volby a strany.")