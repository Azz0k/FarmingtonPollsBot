import pandas as pd
import os
import logging
import sys
from typing import Any
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from imports.utils import *
from imports.config import *
from imports.Trie import Trie
from imports.TwoWayDict import TwoWayDict
from imports.Users_mssql import Users


class Support:

    def __init__(self):
        self.find_trie = Trie()
        self.data_frame = None
        self.name_vs_id = TwoWayDict()
        self.users = Users()
        self.xsl_file_name = ''

    def get_file_name(self):
        files_list = []
        files_dict = {}
        for root, dirs, files in os.walk(WORK_FOLDER):
            if root.find('архив') > -1:
                continue
            if root.find('планирование') > -1:
                continue
            if root.find('потенциал') > -1:
                continue
            for name in files:
                if not name[:1].isdigit():
                    continue
                if not name.endswith('.xlsb'):
                    continue
                # print(os.path.join(root, name))
                files_list.append(name)
                files_dict[name] = os.path.join(root, name)
        files_list.sort(key=lambda x: int(x[3:5]))
        last_element = len(files_list) - 1
        result = files_dict[files_list[last_element]]
        if self.xsl_file_name != result:
            logging.log(logging.INFO, 'Xls file changed:')
            logging.log(logging.INFO, result)
            self.xsl_file_name = result
        return result

    def get_data_from_file(self, file_name: str) -> Any:
        df = pd.read_excel(file_name, sheet_name='МС')
        trie = Trie()
        #del df['DSM']
        #del df['SV']
        for i in range(1, len(df.iloc[:, 4])):
            if isinstance(df['Unnamed: 1'][i], str) and df['Unnamed: 1'][i].strip().upper().startswith('П'):
                if pd.isna(df.iloc[:, 4][i]):
                    continue
                self.name_vs_id.split_string_and_add(df.iloc[:, 4][i].strip())
                trie.insert(df.iloc[:, 4][i].strip(), i)
        del df['Unnamed: 1']
        del df['Unnamed: 0']
        del df['Unnamed: 2']
        self.data_frame = df
        return trie

    def update_data_frame(self, start: bool = False) -> None:
        """Read data from base file and store it to the trie and to the pandas dataFrame"""

        def log_and_exit(message: str) -> None:
            logging.log(logging.CRITICAL, message)
            if start:
                sys.exit(message)

        root = None
        try:
            self.find_trie = self.get_data_from_file(self.get_file_name())
        except OSError:
            log_and_exit('Base file not accessible!!!')
        except KeyError:
            log_and_exit('Incorrect base file structure')

    def create_repeat_markup(self, data: str) -> Any:
        """Return an inline keyboard markup with one button"""
        reply_markup = InlineKeyboardMarkup()
        if data[0:1].isalpha():
            data = self.name_vs_id.replace_names_with_ids(data)
        button = InlineKeyboardButton(text='Повторить последний запрос', callback_data=f'{BUTTON_PREFIX}{data}')
        reply_markup.add(button)
        return reply_markup

    def create_contact_markup(self) -> Any:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = KeyboardButton('Отправить контакт', request_contact=True)
        markup.add(button)
        return markup

    def create_standard_markup(self, query: str) -> Any:
        markup = InlineKeyboardMarkup(row_width=3)
        callback_id = query
        if query[0:1].isdigit():
            callback_id = self.name_vs_id.replace_ids_with_names(query)
        children = self.find_trie.get_children(callback_id)
        for i in range(0, len(children)):
            element = children[i]
            button = InlineKeyboardButton(text=element,
                                          callback_data=f'{BUTTON_PREFIX}{query}_{self.name_vs_id.get_id_from_name(element)}')
            if i % 3 == 0:
                markup.add(button)
            else:
                markup.insert(button)
        return markup

    def get_children(self, query: str) -> Any:
        return self.find_trie.get_children(self.name_vs_id.replace_ids_with_names(query))

    def get_index(self, query: str) -> Any:
        return self.find_trie.get_index(self.name_vs_id.replace_ids_with_names(query))

    def get_answer(self, query: str) -> str:
        territory_name = query
        if query[0:1].isalpha():
            territory_index = self.find_trie.get_index(query)
            if territory_index == -1:
                return NOT_FOUND_ANSWER
        else:
            territory_index = self.find_trie.get_index(self.name_vs_id.replace_ids_with_names(query))
            territory_name = self.name_vs_id.replace_ids_with_names(query)
        data_row_list = self.data_frame.loc[territory_index, :].values.tolist()[2:]
        logging.log(logging.INFO, territory_name)
        result = convert_to_string(territory_name, data_row_list)
        return result

    def get_message_from_b24(self, telegram_id: int) -> str:
        return self.users.get_link_by_telegram_id(telegram_id)

    def replace_ids_with_names(self, query: str):
        return self.name_vs_id.replace_ids_with_names(query)


def import_from_file():
    merch = pd.read_excel(r'C:\temp\Мерчи.xlsx')
    users = Users()
    for c in merch['Phone'].values:
        c = str(c)
        c = c.replace(' ', '')
        c = c.replace('(', '')
        c = c.replace(')', '')
        c = c.replace('-', '')
        if c.startswith('8'):
            c = '+7' + c[1:]
        if c.startswith('9'):
            c = '+7' + c
        if c.startswith('7'):
            c = '+' + c
        if not users.is_phone_number_exists(c):
            users.insert_number(c)
            print(f'{c} - добавлено')
        else:
            print(f'{c} - уже есть в базе')


if __name__ == '__main__':
    import_from_file()
