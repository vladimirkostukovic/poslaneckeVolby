import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://www.volby.cz/pls/ps2017nss/"
REGION_URL = "https://www.volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj={}"  # URL šablona pro regiony 1-15


# Funkce pro zpracování obecné volební statistiky
def parse_general_info(soup, region_id):
    try:
        region_name = soup.find("h3").text.strip().replace("Kraj: ", "")
        table = soup.find("table", {"id": "ps311_t1"})
        rows = table.find_all("tr")[2]  # Bereme 3. řádek s daty

        cols = [td.text.strip().replace("\xa0", "") for td in rows.find_all("td")]

        return {
            "Kraj ID": region_id,
            "Kraj Název": region_name,
            "Okrsky celkem": cols[0],
            "Okrsky zpr": cols[1],
            "Okrsky %": cols[2],
            "Voliči": cols[3],
            "Vydané obálky": cols[4],
            "Účast (%)": cols[5],
            "Odevzdané obálky": cols[6],
            "Platné hlasy": cols[7],
            "Platné hlasy (%)": cols[8],
        }
    except Exception as e:
        print(f"❌ Chyba při zpracování obecné informace pro kraj {region_id}: {e}")
        return None


# Funkce pro zpracování hlasů jednotlivých stran
def parse_party_results(soup, region_id, city_name):
    try:
        table = soup.find_all("table", {"class": "table"})[1]  # Bereme druhou tabulku s výsledky stran
        rows = table.find_all("tr")[2:]  # Přeskakujeme záhlaví

        party_results = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            party_results.append({
                "Kraj ID": region_id,
                "Město": city_name,
                "Číslo strany": cols[0].text.strip(),
                "Název strany": cols[1].text.strip(),
                "Hlasy celkem": cols[2].text.strip().replace("\xa0", ""),
                "Hlasy v %": cols[3].text.strip().replace("\xa0", ""),
            })

        return party_results

    except Exception as e:
        print(f"❌ Chyba při zpracování výsledků stran pro kraj {region_id}: {e}")
        return []


# Hlavní funkce pro spuštění parseru pro regiony (1-15)
def scrape_all_regions():
    all_general_info = []
    all_party_results = []

    for region_id in range(1, 16):  # Smyčka přes regiony 1-15
        print(f"📍 Zpracováváme kraj {region_id}...")
        url = REGION_URL.format(region_id)
        response = requests.get(url)

        if response.status_code != 200:
            print(f"❌ Chyba při načítání stránky: {url}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        city_name = soup.find("h3").text.strip().replace("Kraj: ", "")

        general_info = parse_general_info(soup, region_id)
        party_results = parse_party_results(soup, region_id, city_name)

        if general_info:
            all_general_info.append(general_info)

        if party_results:
            all_party_results.extend(party_results)  # Přidáváme všechny strany do seznamu

        time.sleep(1)  # ⏳ Pauza mezi požadavky (aby nedošlo k blokaci)

    # Přepisujeme soubory se záhlavím
    pd.DataFrame(all_general_info).to_csv("general_info.csv", index=False, encoding="utf-8", mode='w', header=True)
    pd.DataFrame(all_party_results).to_csv("party_results.csv", index=False, encoding="utf-8", mode='w', header=True)

    print("✅ Všechny kraje byly úspěšně zpracovány!")


# 🔥 Spuštění parseru
scrape_all_regions()