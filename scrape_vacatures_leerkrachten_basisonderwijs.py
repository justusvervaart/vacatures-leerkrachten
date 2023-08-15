import requests
import re
import csv
import os
from bs4 import BeautifulSoup

BASE_URL = 'https://www.meesterbaan.nl/vacatures/basisonderwijs/onderwijzend/p-99'
CSV_FILENAME = 'vacatures_basisonderwijs.csv'
DEV_MODE = True  # Zet dit op False om alle links te verwerken.

def fetch_detail_page(url):
    """Haal de content van een detailpagina op."""
    response = requests.get(url)
    return response.text

def extract_info_from_page(html_content):
    """Extraheer specifieke informatie van een pagina."""
    soup = BeautifulSoup(html_content, 'html.parser')

    info_dict = {}

    # Extractie van de eigenschappen zoals eerder.
    properties = soup.select('.list-property')
    for prop in properties:
        label = prop.select_one('label')
        div_value = prop.select_one('div')

        if label and div_value:
            key = label.get_text(strip=True)
            value = div_value.get_text(strip=True)
            info_dict[key] = value

    # Extractie van Naam school en ID-school
    school_name_div = soup.select_one('.text-center.text-md-start.mt-3.mt-md-0 h2')
    if school_name_div:
        info_dict['Naam school'] = school_name_div.get_text(strip=True)

    school_link = soup.select_one('a[href^="https://www.meesterbaan.nl/school/"]')
    if school_link:
        href_value = school_link.get('href')
        match = re.search(r'/school/(\d+)/', href_value)
        if match:
            info_dict['ID-school'] = match.group(1)

    # Extractie van Functienaam
    job_title_div = soup.select_one('h1.mt-3.mt-md-0')
    if job_title_div:
        info_dict['Functienaam'] = job_title_div.get_text(strip=True)

    # Extractie van Postcode en Plaatsnaam
    address_div = soup.select_one('.body-medium-default.school-adres-gegevens')
    if address_div:
        address_lines = address_div.select('.ms-2 > div')
        for line in address_lines:
            content = line.get_text(strip=True)
            match = re.search(r'(\d{4}\s?[A-Za-z]{2})\s+(.*)', content)
            if match:
                info_dict['Postcode'] = match.group(1)
                info_dict['Plaatsnaam'] = match.group(2)
                break

    # Extractie van Latitude en Longitude
    map_link = soup.select_one('#school-map-container a[href^="http://maps.google.com/maps?q="]')
    if map_link:
        href_value = map_link.get('href')
        match = re.search(r'q=(\d+\.\d+),(\d+\.\d+)', href_value)
        if match:
            info_dict['Latitude'] = match.group(1)
            info_dict['Longitude'] = match.group(2)

    return info_dict

def get_existing_links(filename):
    """Haal bestaande links op uit een CSV-bestand."""
    if not os.path.exists(filename):
        return set()
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return set(row['URL'] for row in reader)

def get_links_for_development(all_links, limit=10):
    """Retourneer een subset van de links voor ontwikkelingsdoeleinden."""
    return set(list(all_links)[:limit])

def main():
    response = requests.get(BASE_URL)
    all_links = set(re.findall(r'https://www.meesterbaan.nl/vacature/\d+', response.text))

    # Als DEV_MODE actief is, beperk het aantal links.
    if DEV_MODE:
        all_links = get_links_for_development(all_links)

    existing_links = get_existing_links(CSV_FILENAME)

    # Verwijder de bestaande links uit de set van alle links.
    new_links = all_links - existing_links

    new_entries = []

    for link in new_links:
        page_content = fetch_detail_page(link)
        info = extract_info_from_page(page_content)
        info['URL'] = link  # Voeg URL toe aan het info woordenboek
        new_entries.append(info)

    # Schrijf de nieuwe entries naar het CSV-bestand.
    if new_entries:
        # Neem de union van alle keys uit alle dictionary items in new_entries voor dynamische headers
        all_keys = set().union(*(d.keys() for d in new_entries))

        with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=all_keys)
            if not existing_links:  # Als het bestand leeg was, voeg de header toe.
                writer.writeheader()
            writer.writerows(new_entries)

if __name__ == '__main__':
    main()
