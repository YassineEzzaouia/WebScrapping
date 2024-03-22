import requests
from bs4 import BeautifulSoup
import re
import csv
import configparser
import datetime
import os

print('NB:This operation can last a few minutes ...')

script_directory = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(script_directory, 'kj_configfile.ini'))

base_url = config.get('WEBSITE','kj_website')

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

output_root_directory = input("Enter the output directory (leave blank for default 'kj_data_logs' directory): ").strip()
if not output_root_directory:
    output_root_directory = os.path.join(script_directory, 'kj_data_logs')
os.makedirs(output_root_directory, exist_ok=True)

csv_file = os.path.join(output_root_directory, config.get('OUTPUT SECTION', 'output_filename').format(current_time))

config.set('OUTPUT SECTION', 'output_root_directory', output_root_directory)

with open(os.path.join(script_directory, 'kj_configfile.ini'), 'w') as configfile:
    config.write(configfile)

pattern = re.compile(r'^/(blog/)?$')

page_num = 1
hrefs = []

data_list = []

fieldnames = ['Nom de la société','Secteur d\'activité', 'Taille de l\'entreprise', 'Catégorie', 'Année de fondation', 'Adresse', 'Lien webs']

print('Collecting data from the website ...')

while True:
    
    url = f'{base_url}/offres-emploi/companies/?page={page_num}'

    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    span4_elements = soup.find_all(class_='span4')

    for span4 in span4_elements:
        a_tag = span4.find('a')

        href = a_tag['href']

        if not pattern.match(href):
            hrefs.append(base_url + href)

    next_button = soup.find('a', class_='page-link', title='Next Page')

    if not next_button:
        break

    page_num += 1

for href in hrefs:
    response = requests.get(href)
    soup = BeautifulSoup(response.text, 'html.parser')

    span9_element = soup.find(class_='span9')

    sector = span9_element.find('dt', string='Secteur d\'activité')
    size = span9_element.find('dt', string='Taille de l\'entreprise')
    category = span9_element.find('dt', string='Catégorie')
    foundation_year = span9_element.find('dt', string='Année de fondation')
    address = span9_element.find('dt', string='Adresse')
    website = span9_element.find('dt', string='Lien webs')

    company_name = soup.find(class_='base').text.strip()
    
    data = {
        'Nom de la société': company_name,
        'Secteur d\'activité': sector.find_next('dd').text.strip() if sector else '',
        'Taille de l\'entreprise': size.find_next('dd').text.strip() if size else '',
        'Catégorie': category.find_next('dd').text.strip() if category else '',
        'Année de fondation': int(foundation_year.find_next('dd').text.strip()) if foundation_year else '',
        'Adresse': address.find_next('dd').text.strip() if address else '',
        'Lien webs': website.find_next('a')['href'] if website else ''
    }

    data_list.append(data)

print('Generating the CSV file ...')

with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data_list)

print("CSV file generated successfully in ",csv_file)