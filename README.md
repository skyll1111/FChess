## FChess
FChess — это веб-приложение для игры в шахматы, предназначенное как для новичков, так и для опытных шахматистов. Оно предлагает интуитивно понятный интерфейс, возможность игры против компьютера, отслеживание истории партий и многое другое.

## Технологии
- Backend: Python, Flask
- Frontend: HTML, CSS, JavaScript (опционально: фреймворк, например React)
- База данных: (опционально: PostgreSQL, MySQL)

## Функциональные требования
### Регистрация/Авторизация:
- [x] Пользователи должны иметь возможность регистрироваться и авторизовываться в системе.
- [x] Хранение данных пользователей (логин, пароль) в базе данных.

### Шахматная доска:
- [x] Отображение шахматной доски с расставленными фигурами.
- [x] Возможность делать ходы фигурами с помощью мыши или сенсорного экрана.
- [x] Проверка корректности ходов согласно правилам шахмат.

### Игра против бота:
- [ ] Реализация алгоритма игры в шахматы для бота (можно использовать готовые библиотеки, например python-chess).
- [ ] Разные уровни сложности бота.

### История партий:
- [x] Сохранение истории сыгранных партий в базе данных.
- [x] Возможность просмотра истории партий.
- [x] Возможность воспроизведения ходов из сохраненных партий.

## Дополнительные возможности (опционально)
- [x] Мультиплеер: возможность игры против других пользователей онлайн.
- [ ] Чат: общение между игроками во время игры.
- [ ] Таймер: ограничение времени на ход.
- [ ] Разные варианты шахмат (шахматы Фишера, блиц и т.д.).

## Установка
1. Установка необходимых библиотек `pip install -r requirements.txt`
2. Запуск приложения `python app.py`
3. Перейдите по ссылке http://127.0.0.1:5000/
