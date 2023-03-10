import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import warnings
# warnings.filterwarnings('ignore')

site_url = 'https://www.nevatom.ru/catalog/detali-sistem-ventilyatsii/glushiteli/'

catalog = site_url[site_url.find('.ru') + 3:]
url = site_url[:site_url.find('.ru') + 3]

res = requests.get(url + catalog)
soup = BeautifulSoup(res.text, 'html.parser')
page_catalog_links = [x['href'] for x in soup.find_all('a', {'class': "b-tile__title"})]
title = soup.find('div', {'class': 'b-title'}).text

temp_list = [True]
# df_final = pd.DataFrame({'Наименование': None, 'Ссылка': None, 'Каталог': None, 'Стоимость': None})
df_final = pd.DataFrame()


def get_dataframe(text: str, catalog_url: str) -> None:
    global df_final

    def convert_price(x):
        res = re.findall('\d*\s*\d*', x)[0].replace(' ', '')
        res = res if res else 0
        return int(res)

    def convert_to_hyperlink(row):
        rr = row["Наименование"].replace('"', "'")
        return f'=HYPERLINK("{row["Ссылка"]}", "Ссылка: {rr}")'

    try:
        df = pd.read_html(text)[0]
        df = df[['Наименование', 'Стоимость']]
    except Exception as ex:
        print(ex)
        df = pd.DataFrame(data={'Наименование': ["Не найдено"], "Стоимость": [None]})
    try:
        df['Стоимость'] = df['Стоимость'].apply(convert_price)
        # df['Стоимость'] = df['Стоимость'].str.replace('\D', '', regex=True).str.extract('(\d*\s*\d*)').replace('\s*', '', regex=True).astype(int)
    except Exception as ex:
        print(ex)
        pass

    soup = BeautifulSoup(text, 'html.parser')
    breadcrumbs = ' / '.join([x['title'] for x in soup.find_all('a', {'class': 'e-breadcrumb__link'})] + [
        soup.find('span', {'class': 'e-breadcrumb__link'}).text])

    df['Ссылка'] = catalog_url
    df['Ссылка'] = df.apply(convert_to_hyperlink, axis=1)
    df['Каталог'] = breadcrumbs

    df_final = pd.concat([df_final, df])

    # print(df)
    # input('123')


def get_links(links: list):
    global temp_list

    if not temp_list:
        return

    for n, link in enumerate(links):
        res = requests.get(url + link)
        soup = BeautifulSoup(res.text, 'html.parser')
        new_links = [x['href'] for x in soup.find_all('a', {'class': "b-tile__title"})]
        if new_links:
            temp_list.append(links[n + 1:])
            return get_links(new_links)
        else:
            print(link)
            get_dataframe(res.text, url + link)

    return get_links(temp_list.pop())


get_links(page_catalog_links)

df_final.to_excel(f'{title}.xlsx', index=False)
