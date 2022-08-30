import shutil

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from aiogram.types import InlineKeyboardButton
import json
import os
import re

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 "
                  "Safari/537.36 "
}


async def clean(books: list):
    i = 1
    for book in books:
        for item in books[i:]:
            if book['title'] == item['title']:
                books.remove(item)
        i += 1
    return books


async def write_to_json(file_name, file):
    with open(f'{file_name}.json', 'w', encoding='utf-8') as f:
        json.dump(file, f, ensure_ascii=False, indent=4)


async def find_books(title: str):
    url = f"https://librusec.club/booksearch?ask={title.replace(' ', '+').lower()}&submit=Найти"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as resp:
            r = await resp.text()
            soup = BeautifulSoup(r, 'lxml')

            block_div = soup.find('div', class_="wrap").find_all('div', class_='desc')

            dict_list = []
            for book in block_div:
                book_title = book.find('div', class_='book_name').find('a').text
                book_url = 'https://librusec.club' + book.find('div', class_='book_name').find('a')['href']
                book_author = book.find('span', class_='author').find('a')['title']

                dict_list.append({
                    'title': book_title,
                    'url': book_url,
                    'author': book_author
                })

            file = await clean(dict_list)

            await write_to_json('books_list', file)

            return await load_json(file_name='books_list')


async def load_json(file_name):
    with open(f'{file_name}.json', encoding='utf-8') as file:
        connect = file.read()
        return json.loads(connect)


async def sorted_books(book_dict: list):
    count = 0
    text = ''
    inline_list = []

    for item in book_dict:
        count += 1
        text += f"{count}. {item['title']} - {item['author']} \n"
        inline_list.append(InlineKeyboardButton(text=str(count), callback_data=str(count)))

    return {'text': text, 'inline': inline_list}


async def download_book_link(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as resp:
            r = await resp.text()
            soup = BeautifulSoup(r, 'lxml')

            return soup.find('div', class_='download_link').find('a')['href']


async def parse_book_format(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as resp:
            r = await resp.text()
            soup = BeautifulSoup(r, 'lxml')

            div_block = soup.find('div', class_='b_download').find_all('span', class_='link')

            inline_format = []
            all_information = []
            for item in div_block:
                book_format = item.text
                book_url = 'https://librusec.club/' + item['onclick'].replace("window.open('", '').replace("', '_top')",
                                                                                                           '')
                url = await download_book_link(book_url)

                inline_format.append(InlineKeyboardButton(text=book_format, callback_data=book_format))
                all_information.append({
                    'format': book_format,
                    'url': url
                })

            await write_to_json(file_name='book_formats', file=all_information)

            return inline_format


async def download_file(format_book: str):
    formats_file = await load_json('book_formats')

    if not os.path.exists('data/'):
        os.mkdir('data/')

    for i in formats_file:
        if i['format'] == format_book:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=i['url'], headers=headers) as r:
                    content = await r.read()

                    name_format = re.search(r'format=\D*\d*\D*&', i["url"]).group().split('=')[-1].replace('&', '')
                    name_book = re.search(r'art=\d*&', i["url"]).group().split('=')[-1].replace('&', '')
                    with open(f'data/{name_book}.{name_format}', 'wb') as file:
                        file.write(content)

                    with open(f'data/{name_book}.{name_format}', 'rb') as file:
                        book = file.read()

                    return book


async def delete_folder():
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
    shutil.rmtree(path)
