import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup

from parse_books import find_books, sorted_books, load_json, parse_book_format, download_file, delete_folder

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")


logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

search_button = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('/Search'))


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer('This is a book search bot. '
                         '\nClick on the button to start searching.', reply_markup=search_button)


@dp.message_handler(commands='Search')
async def search_handler(message: types.Message):
    await message.answer('Enter book title', reply_markup=ReplyKeyboardRemove())


@dp.message_handler()
async def book(message: types.Message):
    book_name = await find_books(message.text)

    if book_name is None:
        await bot.send_message(message.from_user.id, 'There is no such book')
    else:
        clean_books = await sorted_books(book_name)
        in_numb = InlineKeyboardMarkup().row(*clean_books["inline"])

        await bot.send_message(message.from_user.id, f'Books on demand "{message.text}"\n'
                                                     f'{clean_books["text"]}', reply_markup=in_numb)


@dp.callback_query_handler(text=[str(num) for num in range(1, len('file_books') + 1)])
async def choose_format(query: types.CallbackQuery):

    file_books = await load_json('books_list')

    formats = await parse_book_format(file_books[int(query.data) - 1]['url'])

    format_inline = InlineKeyboardMarkup().row(*formats)
    books_title = file_books[int(query.data) - 1]['title']

    await bot.delete_message(query.from_user.id, query.message.message_id)
    await bot.send_message(query.from_user.id, f'Choose the format of the book "{books_title}": ',
                           reply_markup=format_inline)


@dp.callback_query_handler(text=['FB2', 'EPUB'])
async def send_file(query: types.CallbackQuery):

    down_file = await download_file(query.data)

    await bot.delete_message(query.from_user.id, query.message.message_id)
    await bot.send_document(query.from_user.id, down_file, reply_markup=search_button)
    await delete_folder()

executor.start_polling(dp, skip_updates=True)
