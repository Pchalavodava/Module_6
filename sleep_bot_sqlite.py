import datetime as dt
import os
import telebot
from typing import Union
from telebot import types
from sqlite3 import connect


my_db: str = 'sleep_bot.db'
conn = connect(my_db, check_same_thread=False)
cursor = conn.cursor()

TG_TOKEN = os.getenv('TG_TOKEN')
bot = telebot.TeleBot(TG_TOKEN)

commands_dict: dict[str, str] = {
    'go_to_sleep': 'Уснуть',
    'wake_up': 'Проснуться',
    'do_not_record': 'Сегодня без заметок'
}

sleep_bot_tables: dict[str, str] = {'table_users': 'users',
                                    'table_sleep_records': 'sleep_records',
                                    'table_notes': 'notes'}

rating_list: list[str] = list(map(lambda x: str(x), list(range(1, 6))))

# try:
#     cursor.execute(
#         """DROP TABLE {table}""".format(table='table_name')
#     )
# except sqlite3.OperationalError as exc:
#     print(exc)


def get_real_time() -> str:
    """
    Получение текущего времени и перевод его в строковый формат
    :return: str: Текущая дата и время в формате "%Y-%m-%d %H:%M:%S"
    """
    return dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def calculate_sleep_time(wake_t: str, sleep_t: str) -> float:
    """
    Функция перевода строкового представления времени в формат 'datetime' и дальнейший расчет времени
    сна между временем пробуждения и временем отхода ко сну
    :param wake_t: str: Строковое представление времени пробуждения
    :param sleep_t: str: Строковое представление времени отхода ко сну
    :return: float: Время сна в секундах
    """
    sleep_t = dt.datetime.strptime(sleep_t, '%Y-%m-%d %H:%M:%S')
    wake_t = dt.datetime.strptime(wake_t, '%Y-%m-%d %H:%M:%S')
    time_delta = (wake_t - sleep_t).total_seconds()
    return time_delta


def convert_from_seconds(seconds: float) -> str:
    """
    Перевод секунд в строковое представление минут и часов для вывода в бот
    :param seconds: float: Общее количество секунд
    :return: str: Строковое представление часов и минут
    """
    s_time: list[str] = str(dt.timedelta(seconds=seconds)).split(':')
    s_time: list[int] = list(map(lambda x: int(x), s_time))
    if s_time[0] > 0:
        return f'{s_time[0]} часов, {s_time[1]} минут'
    else:
        return f'{s_time[1]} минут'


def create_table(table_name: str) -> None:
    """
    Функция формирования таблиц из словаря sleep_bot_tables
    :param table_name: str: Название таблицы для ее создания
    :return: None
    """
    if table_name == sleep_bot_tables.get('table_users', 'users'):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS {table} 
            (
                id INTEGER PRIMARY KEY NOT NULL,
                name TEXT
            ); 
            """.format(table=table_name)
        )
    elif table_name == sleep_bot_tables.get('table_sleep_records', 'sleep_records'):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS {table} 
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sleep_time DATETIME,
                wake_time DATETIME,
                sleep_quality INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            """.format(table=table_name)
        )
    elif table_name == sleep_bot_tables.get('table_notes', 'notes'):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS {table} 
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                sleep_record_id INTEGER,
                FOREIGN KEY (sleep_record_id) REFERENCES sleep_records (id)
            );
            """.format(table=table_name)
        )
    else:
        print(f'Невозможно создать таблицу {table_name}')


def add_to_table(**kwargs: Union[str, int]) -> None:
    """
    Функция добавления записи в талицу 'table', созданной базы данных
    :param kwargs: Union[str, int]: название таблицы, именованные аргументы в зависимости от названия таблицы
    :return: None
    """
    if kwargs['table'] == sleep_bot_tables['table_users']:
        val = (kwargs['user_id'], kwargs['user_name'])
        cursor.execute(
            """
            INSERT OR IGNORE INTO {table} (id, name) VALUES (?, ?)
            """.format(table=kwargs['table']),
            val
        )

    elif kwargs['table'] == sleep_bot_tables['table_sleep_records']:
        val = (kwargs['user_id'], kwargs['sleep_time'])
        cursor.execute(
            """
            INSERT OR IGNORE INTO {table} (user_id, sleep_time) VALUES (?, ?)
            """.format(table=kwargs['table']),
            val
        )

    elif kwargs['table'] == sleep_bot_tables['table_notes']:
        val = (kwargs['note'], kwargs['sleep_rec_id'])
        cursor.execute(
            """
            INSERT OR IGNORE INTO {table} (text, sleep_record_id) VALUES (?, ?)
            """.format(table=kwargs['table']),
            val
        )
    conn.commit()


def get_last_note_from_sleep_records(user_id: int) -> Union[tuple[int, str, Union[str, None], Union[int, None]], None]:
    """
    Функция получения последней записи о сне пользователя 'user_id'
    :param user_id: int: Идентификатор пользователя
    :return: Union[tuple[int, str, Union[str, None], Union[int,None]], None]: Если запись найдена, то возвращается кортеж из
    id последней записи о сне, времени отхода ко сну, времени пробуждения и оценки сна. Иначе - None
    """
    cursor.execute(
        """
        SELECT id, sleep_time, wake_time, sleep_quality FROM {table} WHERE user_id == (?)
        """.format(table=sleep_bot_tables['table_sleep_records']), (user_id,)
    )
    result = cursor.fetchall()
    if result:
        return result[-1]
    else:
        return None


def get_user(user_id: int) -> list[Union[tuple[int], None]]:
    """
    Получение  пользователя с идентификатором 'user_id' из таблицы 'table_users'
    :param user_id: int: Идентификатор пользователя
    :return: list[Union[tuple[int], None]]: Список с одним кортежем из идентификатора пользователя
    """
    cursor.execute(
        """
        SELECT id from {table} WHERE id = (?)
        """.format(table=sleep_bot_tables['table_users']), (user_id,)
    )
    return cursor.fetchall()


def update_sleep_time(**kwargs: Union[str, int]) -> None:
    """
    Функция обновления времени отхода ко сну
    :param kwargs: Union[str, int]: Именованные аргументы: table (название таблицы), sleep_time (время
    отхода ко сну), Note_id (идентификатор записи)
    :return: None
    """
    cursor.execute(
        """
        UPDATE {table}
        SET sleep_time = ?
        WHERE id = ?
        """.format(table=kwargs['table']), (kwargs['sleep_time'], kwargs['note_id'],)
    )
    conn.commit()


def update_wake_time(**kwargs: Union[str, int]) -> None:
    """
    Обновление строки в таблице 'table' добавлением в нее значения 'wake_time'
    :param kwargs: Union[str, int]: Именованные параметры: table (название таблицы), wake_time (время
    пробуждения), user_id (идентификатор пользователя), sleep_time (время отхода ко сну)
    :return: None
    """
    cursor.execute(
        """
        UPDATE {table}
        SET wake_time = ?
        WHERE user_id = ? AND sleep_time = ?        
        """.format(table=kwargs['table']), (kwargs['wake_time'], kwargs['user_id'], kwargs['sleep_time'])
    )
    conn.commit()


def update_sleep_quality(**kwargs: Union[str, int]) -> None:
    """
    Обновление записи в таблице 'table' внесением в нее значения 'sleep_quality'
    :param kwargs: Именованные параметры для обновления записи: table (название таблицы), sleep_quality (качество
    сна), user_id (идентификатор пользователя), sleep_time/wake_time (время отхода ко сну/время пробуждения)
    :return: None
    """
    cursor.execute(
        """
        UPDATE {table}
        SET sleep_quality = ?
        WHERE user_id = ? and sleep_time = ? and wake_time = ?
        """.format(table=kwargs['table']), (kwargs['sleep_quality'], kwargs['user_id'], kwargs['sleep_time'],
                                            kwargs['wake_time'])
    )
    conn.commit()


def create_keyboard(button_names: Union[str, list[Union[str, int]]]) -> types.ReplyKeyboardMarkup:
    """
    Функция формирования кнопок клавиатуры
    :param button_names: Union[str, list[str, int]]: Название/я кнопок
    :return: types.ReplyKeyboardMarkup: Выводимая в бот клавиатура
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if isinstance(button_names, str):
        button_names: list[Union[str, int]] = [button_names]
    for button_name in button_names:
        button = types.KeyboardButton(button_name)
        keyboard.add(button)
    return keyboard


def press_go_to_sleep_button(last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]], message) -> None:
    """
    Функция обработки клавиши 'go_to_sleep'
    :param last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]]: Последняя запись о сне,
    где нулевой элемент - идентификатор записи о сне, первый - строковое представление отхода ко сну,
    второй - строковое представление времени пробуждения
    :param message: Посылаемое в бот сообщение
    :return: None
    """
    if not last_sleep_note or last_sleep_note[2]:
        add_to_table(table=sleep_bot_tables['table_sleep_records'], user_id=message.from_user.id,
                     sleep_time=get_real_time())
    elif last_sleep_note[1] and not last_sleep_note[2]:
        update_sleep_time(table=sleep_bot_tables['table_sleep_records'], sleep_time=get_real_time(), note_id=last_sleep_note[0])
    keyboard = create_keyboard(commands_dict['wake_up'])
    warning_message = f'{message.from_user.username}, идешь спать? \nНе забудь сообщить, когда проснешься'
    bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)


def press_wake_up_button(last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]], message) -> None:
    """
    Функция обработки клавиши 'wake_up'
    :param last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]]: Последняя запись о сне,
    где нулевой элемент - идентификатор записи о сне, первый - строковое представление отхода ко сну,
    второй - строковое представление времени пробуждения
    :param message: Посылаемое в бот сообщение
    :return: None
    """
    if last_sleep_note[2]:
        warning_message = f'{message.from_user.username}, ты не ложился спать'
        bot.send_message(message.chat.id, warning_message, reply_markup=create_keyboard(commands_dict['go_to_sleep']))
    else:
        wake_up_time = get_real_time()
        update_wake_time(table=sleep_bot_tables['table_sleep_records'], wake_time=wake_up_time,
                         user_id=message.from_user.id,
                         sleep_time=last_sleep_note[1])
        sleep_time_sec = calculate_sleep_time(wake_up_time, last_sleep_note[1])
        sleep_time_str = convert_from_seconds(sleep_time_sec)
        keyboard = create_keyboard(rating_list)
        warning_message = (f'{message.from_user.username}, доброе утро, ты  проспал {sleep_time_str}. '
                           f'\nОцени качество своего сна:')
        bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)


def press_rating_button(last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]], message) -> None:
    """
    Функция обработки при нажатии на кнопку из списка 'rating_list'
    :param last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]]: Последняя запись о сне,
    где нулевой элемент - идентификатор записи о сне, первый - строковое представление отхода ко сну,
    второй - строковое представление времени пробуждения
    :param message: Посылаемое в бот сообщение
    :return: None
    """
    if not last_sleep_note or last_sleep_note[3]:
        keyboard = create_keyboard(commands_dict['go_to_sleep'])
        warning_message = (f'Ты еще не ложился спать \nКогда пойдешь спать, не забудь предупредить '
                           f'нажатием кнопки "Уснуть"')
        bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)
    elif not last_sleep_note[2]:
        keyboard = create_keyboard(commands_dict['wake_up'])
        warning_message = f'Твой сон еще не окончен.\nНажми кнопку "Проснуться"'
        bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)
    elif last_sleep_note[2] and not last_sleep_note[3]:
        update_sleep_quality(table=sleep_bot_tables['table_sleep_records'], sleep_quality=message.text,
                             user_id=message.from_user.id, sleep_time=last_sleep_note[1], wake_time=last_sleep_note[2])
        keyboard = create_keyboard(commands_dict['do_not_record'])
        warning_message = (f'Напиши заметку к своему сну в пустое окошко или проигнорируй нажатием кнопки '
                           f'"Сегодня без заметок"')
        bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)


def press_do_not_record_button(message) -> None:
    """
    Функция отработки клавиши 'do_not_record'
    :param message: Сообщение, посылаемое в бот
    :return: None
    """
    keyboard = create_keyboard(commands_dict['go_to_sleep'])
    warning_message = f'{message.from_user.username}, не забудь предупредить, когда пойдешь ложиться спать'
    bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)


def add_a_note(last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]], message) -> None:
    """
    Функция добавления заметки в таблицу 'table_notes'
    :param last_sleep_note: tuple[int, str, Union[str, None], Union[int, None]]: Последняя запись данного
    пользователя о сне, где аргументы - это id (идентификатор записи), sleep_time (время отхода ко сну),
    wake_time (время пробуждения), sleep_quality (качество сна)
    :param message: Сообщение, посылаемое в бот
    :return: None
    """
    add_to_table(table=sleep_bot_tables['table_notes'], sleep_rec_id=last_sleep_note[0], note=message.text)
    keyboard = create_keyboard(commands_dict['do_not_record'])
    warning_message = f'Комментарий был добавлен к твоему последнему сну. \nХочешь что-то добавить?'
    bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)


@bot.message_handler(commands=['start'])
def handle_start(message) -> None:
    """
    Отработка бота после команды /start
    :param message: Сообщение, отсылаемое в чат (в данном случае /start)
    :return: None
    """
    add_to_table(table=sleep_bot_tables['table_users'], user_id=message.from_user.id,
                 user_name=message.from_user.username)
    keyboard = create_keyboard(commands_dict['go_to_sleep'])
    warning_message = (f'Привет {message.from_user.username}, я - бот. И я буду отслеживать качество твоего сна. '
                       f'\nДля отхода ко сну нажми кнопку "Уснуть"')
    bot.send_message(message.chat.id, warning_message, reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def handle_message(message) -> None:
    """
    Функция обработки посылаемых в бот сообщений
    :param message: Посылаемое в бот сообщение
    :return:
    """
    if get_user(message.from_user.id):
        last_sleep_note = get_last_note_from_sleep_records(message.from_user.id)
        if message.text == commands_dict['go_to_sleep']:
            press_go_to_sleep_button(last_sleep_note, message)
        elif message.text == commands_dict['wake_up']:
            press_wake_up_button(last_sleep_note, message)
        elif message.text in rating_list:
            press_rating_button(last_sleep_note, message)
        elif message.text == commands_dict['do_not_record']:
            press_do_not_record_button(message)
        else:
            add_a_note(last_sleep_note, message)


for table in sleep_bot_tables.values():
    create_table(table)

bot.polling()

cursor.close()
conn.close()
