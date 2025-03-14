import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm

# Загружаем файл links.csv
file_path = "links.csv"
links_df = pd.read_csv(file_path)

# Отфильтровываем строки, у которых нет ссылки на ps311
links_df = links_df.dropna(subset=["ps311_Obec_Link"])

# Файлы для сохранения данных
SUMMARY_FILE = "election_summary.csv"
PARTY_FILE = "party_results.csv"

# Хранилища данных
election_summary = []
party_results = []


# Функция для парсинга общей статистики
def parse_election_summary(url, kraj_id, kraj_name, okres_id, okres_name, obec_id, obec_name):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    try:
        stats = soup.find("table", {"id": "ps311_t1"}).find_all("td", class_="cislo")
        if len(stats) < 9:
            return None

        data = [
            kraj_id, kraj_name, okres_id, okres_name, obec_id, obec_name,
            stats[0].text.strip(), stats[1].text.strip(), stats[2].text.strip(),
            stats[3].text.strip(), stats[4].text.strip(), stats[5].text.strip(),
            stats[6].text.strip(), stats[7].text.strip()
        ]
        return data
    except Exception as e:
        print(f"Ошибка парсинга статистики для {url}: {e}")
        return None


# Функция для парсинга данных по партиям
def parse_party_results(url, kraj_id, kraj_name, okres_id, okres_name, obec_id, obec_name):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    party_data = []
    table_rows = soup.find_all("tr")

    for row in table_rows:
        cols = row.find_all("td")
        if len(cols) >= 4:
            party_name = cols[1].text.strip()
            votes = cols[2].text.strip()
            percent = cols[3].text.strip()

            party_data.append([
                kraj_id, kraj_name, okres_id, okres_name, obec_id, obec_name,
                party_name, votes, percent
            ])

    return party_data


# Обрабатываем ссылки
for index, row in tqdm(links_df.iterrows(), total=len(links_df), desc="📥 Обрабатываем муниципалитеты"):
    kraj_id = row["Kraj_ID"]
    kraj_name = row["Kraj_Název"]
    okres_id = row["Okres_ID"]
    okres_name = row["Okres_Název"]
    obec_id = row["Obec_ID"]
    obec_name = row["Obec_Název"]
    ps311_link = row["ps311_Obec_Link"]

    # Парсим общую статистику
    summary_data = parse_election_summary(ps311_link, kraj_id, kraj_name, okres_id, okres_name, obec_id, obec_name)
    if summary_data:
        election_summary.append(summary_data)

    # Парсим данные по партиям
    party_data = parse_party_results(ps311_link, kraj_id, kraj_name, okres_id, okres_name, obec_id, obec_name)
    party_results.extend(party_data)

    time.sleep(0.1)  # Задержка для избежания блокировки

# Сохраняем данные
pd.DataFrame(election_summary, columns=[
    "Kraj_ID", "Kraj_Název", "Okres_ID", "Okres_Název", "Obec_ID", "Obec_Název",
    "Okrsky celkem", "Okrsky zpr.", "% zpr.", "Voliči", "Obálky vydané", "Účast",
    "Odevzdané обálки", "Platné hlasy"
]).to_csv(SUMMARY_FILE, index=False, encoding="utf-8")

pd.DataFrame(party_results, columns=[
    "Kraj_ID", "Kraj_Název", "Okres_ID", "Okres_Název", "Obec_ID", "Obec_Název",
    "Strana", "Hlasy", "%"
]).to_csv(PARTY_FILE, index=False, encoding="utf-8")

print("✅ Готово! Данные сохранены в CSV.")