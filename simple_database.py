from sqlite3 import connect
from typing import Union

conn = connect('library.db')
cursor = conn.cursor()


def create_new_library(books: str) -> None:
    """
    Создание таблицы 'books' с параметрами id (внешний ключ), title, author и year, если такой не существует
    :param books: str: Название создаваемой таблицы
    :return: None
    """
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS {table} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        year INTEGER NOT NULL
        );
        """.format(table=books)
    )


def add_new_book(table_of_books: str, **kwargs: Union[str, int]) -> None:
    """
    Добавление новой записи в таблицу 'table_of_books'
    :param table_of_books: Название таблицы, в которую необходимо добавить запись
    :param kwargs: Union[str, int]: Параметры для добавления (title, author, year)
    :return: None
    """
    cursor.execute(
        """
        INSERT INTO {table} (title, author, year)
        VALUES (?, ?, ?);

        """.format(table=table_of_books),
        (kwargs['title'], kwargs['author'], kwargs['year'])
    )
    conn.commit()


def get_library(table_of_books: str) -> list[tuple[Union[str, int]]]:
    """
    Получение списка книг из таблицы 'table_of_books'
    :param table_of_books: str: Название таблицы для получения списка книг
    :return: list[tuple[Union[str, int]]]: Список кортежей, где каждый кортеж - отдельная книга
    """
    books = cursor.execute(
        """
        SELECT * FROM {table};
        """.format(table=table_of_books)
    ).fetchall()
    return books


def update_book(table_of_books: str, **kwargs: Union[str, int]) -> None:
    """
    Обновление записи в таблице 'table_of_books' по идентификатору id
    :param table_of_books: str: Таблица, в которой необходимо произвести изменение
    :param kwargs: Union[str, int]: Параметры для изменения записи в таблице (title, author, year)
    по идентификатору id
    :return: None
    """
    update_query = """
        UPDATE {table}
        SET title = ?,
        author = ?,
        year = ?
        WHERE id = ?
        """.format(table=table_of_books)
    cursor.execute(update_query, (kwargs['title'], kwargs['author'], kwargs['year'], kwargs['id']))
    conn.commit()


def delete_book(table_of_books: str, book_id: int) -> None:
    """
    Удаление записи из таблицы 'table_of_books' по идентификатору 'book_id'
    :param table_of_books: str: Таблица, из которой будет удалена запись
    :param book_id: int: Идентификатор записи для удаления
    :return: None
    """
    delete_query = """
    DELETE FROM {table}
    WHERE id = ?
    """.format(table=table_of_books)
    cursor.execute(delete_query, (book_id,))
    conn.commit()


table = 'books'
create_new_library(table)
add_new_book(table_of_books=table, author='Михаил Булгаков', title='Мастер и Маргарита', year=1940)
add_new_book(table_of_books=table, author='Николай Гоголь', title='Мертвые души', year=1842)
add_new_book(table_of_books=table, author='Лев Толстой', title='Хождение по мукам', year=1941)
print(get_library(table_of_books=table))
update_book(table_of_books=table, author='Лев Толстой', title='Война и мир', year='1868', id=4)
books_list = get_library(table_of_books=table)
# for book in books_list:
#     if book[0] > 0:
#         delete_book(table_of_books=table, book_id=book[0])
delete_book(table_of_books=table, book_id=3)

cursor.close()
conn.close()
