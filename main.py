import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime, time, timedelta
import pytz
import time as time_module
import json
import os

# Отключаем логирование
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.disable(logging.CRITICAL)

# Конфигурация
BOT_TOKEN = "8236867741:AAEWPBaBOH-kK6KRc9QB7EO4X1dG6DGMCdE"
GROUP_CHAT_ID = "-1002364657409"

versionbot = "3.2.12 - Stable"

# Список администраторов (их user_id)
ADMINS = [5403608788, 6879963816, 1295169352, 6283747542]

# Файл для сохранения блок-листа
BLOCKLIST_FILE = "blocklist.json"
# Файл для сохранения тестов
TESTS_FILE = "tests.json"
# Файл для сохранения ссылок
LINKS_FILE = "links.json"

# Переменная для хранения ссылки uchiru
uchiru_link = "https://example.com"  # Ссылка по умолчанию


# Функции для работы с блок-листом
def load_blocklist():
    """Загружает блок-лист из файла"""
    try:
        if os.path.exists(BLOCKLIST_FILE):
            with open(BLOCKLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"❌ Ошибка загрузки блок-листа: {e}")
        return []


def save_blocklist():
    """Сохраняет блок-лист в файл"""
    try:
        with open(BLOCKLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(BLOCKLIST, f, ensure_ascii=False, indent=2)
        print("✅ Блок-лист сохранен")
    except Exception as e:
        print(f"❌ Ошибка сохранения блок-листа: {e}")


# Функции для работы с тестами
def load_tests():
    """Загружает тесты из файла"""
    try:
        if os.path.exists(TESTS_FILE):
            with open(TESTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки тестов: {e}")
        return {}


def save_tests():
    """Сохраняет тесты в файл"""
    try:
        with open(TESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(TESTS, f, ensure_ascii=False, indent=2)
        print("✅ Тесты сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения тестов: {e}")


# Функции для работы с ссылками
def load_links():
    """Загружает ссылки из файла"""
    try:
        if os.path.exists(LINKS_FILE):
            with open(LINKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"uchiru": "https://example.com"}  # Ссылка по умолчанию
    except Exception as e:
        print(f"❌ Ошибка загрузки ссылок: {e}")
        return {"uchiru": "https://example.com"}


def save_links():
    """Сохраняет ссылки в файл"""
    try:
        with open(LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(LINKS, f, ensure_ascii=False, indent=2)
        print("✅ Ссылки сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения ссылок: {e}")


# Загружаем блок-лист, тесты и ссылки при запуске
BLOCKLIST = load_blocklist()
TESTS = load_tests()
LINKS = load_links()

# Устанавливаем uchiru_link из сохраненных данных
uchiru_link = LINKS.get("uchiru", "https://example.com")

# Переменная для хранения текста ДЗ
current_homework = "Администраторы не успели выложить актуальное домашнее задание. Ожидайте!"

# Переменная для хранения ID закрепленного сообщения
pinned_message_id = None

# Словарь для отслеживания времени последнего использования команды /hv
last_hv_usage = {}

# База данных дней рождения
birthdays = [
    {"name": "Алина", "date": "14.02"},
    {"name": "Мирон", "date": "03.11"},
    {"name": "Никита", "date": "31.03"},
    {"name": "Максим", "date": "31.03"},
    {"name": "Марта", "date": "16.02"},
    {"name": "Скороходов", "date": "04.04"},
    {"name": "Денис", "date": "21.11"},
    {"name": "Агеенко", "date": "05.02"},
    {"name": "Лиза", "date": "16.10"},
    {"name": "Варя", "date": "06.05"},
    {"name": "Камила", "date": "01.04"},
    {"name": "Фидан", "date": "29.11"},
    {"name": "Ярик", "date": "29.11"},
    {"name": "Вадим", "date": "07.04"},
    {"name": "Семён", "date": "30.01"},
    {"name": "Жасмин", "date": "18.01"},
    {"name": "Ева", "date": "15.06"},
    {"name": "Сережа", "date": "03.08"},
    {"name": "Алиса", "date": "05.05"},
    {"name": "София", "date": "15.05"},
    {"name": "Усенко", "date": "06.09"},
    {"name": "Коваленко", "date": "18.06"}
]


# Альтернатива - сбор участников из истории сообщений
async def chat_members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return

    try:
        members_text = "👥 Активные участники (писавшие в чат):\n\n"
        members_seen = set()

        # Собираем из последних сообщений (ограниченно)
        async for message in context.bot.get_chat_history(GROUP_CHAT_ID, limit=100):
            user = message.from_user
            if user.id not in members_seen:
                members_seen.add(user.id)
                name = f"{user.first_name} {user.last_name if user.last_name else ''}".strip()
                members_text += f"• {name}\n"

                if len(members_seen) >= 50:  # максимум 50
                    break

        members_text += f"\nВсего: {len(members_seen)} участников"
        await update.message.reply_text(members_text)

    except Exception as e:
        await update.message.reply_text("❌ Ошибка получения активных участников")
async def addtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 *Добавление теста*\n\n"
            "Использование:\n"
            "/addtest <номер_теста> <предмет> <количество_заданий> <варианты> <ссылка>\n\n"
            "Пример:\n"
            "/addtest 1 Алгебра 5 Да https://example.com/test1\n"
            "/addtest 2 Геометрия 3 Нет https://example.com/test2\n\n"
            "Доступные предметы: Алгебра, Геометрия, Физика, Химия, Русский язык, Литература, История, География, Биология, Английский язык\n"
            "Варианты: Да/Нет\n"
            "Ссылка: любая валидная ссылка на тест"
        )
        return

    if len(context.args) < 5:
        await update.message.reply_text(
            "❌ Недостаточно аргументов. Нужно: номер_теста предмет количество_заданий варианты ссылка")
        return

    try:
        test_number = context.args[0]
        subject = context.args[1]
        tasks_count = int(context.args[2])
        has_variants = context.args[3].lower() in ['да', 'yes', 'true', '1']
        test_link = context.args[4]

        # Сохраняем тест
        TESTS[test_number] = {
            "subject": subject,
            "tasks_count": tasks_count,
            "has_variants": has_variants,
            "link": test_link,
            "added_date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        save_tests()  # Сохраняем изменения

        await update.message.reply_text(
            f"✅ *Тест #{test_number} добавлен!*\n\n"
            f"📚 Предмет: {subject}\n"
            f"📊 Заданий: {tasks_count}\n"
            f"🎲 Разные варианты: {'Да' if has_variants else 'Нет'}\n"
            f"🔗 Ссылка: {test_link}\n"
            f"📅 Дата добавления: {TESTS[test_number]['added_date']}",
            parse_mode='Markdown'
        )

    except ValueError:
        await update.message.reply_text("❌ Неверный формат количества заданий. Должно быть число.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при добавлении теста: {e}")


# Команда /tests - просмотр всех тестов
async def tests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not TESTS:
        await update.message.reply_text("📝 Тестов пока нет.")
        return

    tests_text = "📚 *Список тестов:*\n\n"

    for test_num, test_data in sorted(TESTS.items(), key=lambda x: x[0]):
        tests_text += (
            f"🔹 *Тест #{test_num}*\n"
            f"   📖 {test_data['subject']}\n"
            f"   📊 Заданий: {test_data['tasks_count']}\n"
            f"   🎲 Варианты: {'Да' if test_data['has_variants'] else 'Нет'}\n"
            f"   🔗 Ссылка: {test_data['link']}\n"
            f"   📅 {test_data['added_date']}\n\n"
        )

    await update.message.reply_text(tests_text, parse_mode='Markdown')


# Команда /deltest - удаление теста (только для админов)
async def deltest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text(
            "🗑️ *Удаление теста*\n\n"
            "Использование:\n"
            "/deltest <номер_теста>\n\n"
            "Пример:\n"
            "/deltest 1"
        )
        return

    test_number = context.args[0]

    if test_number in TESTS:
        del TESTS[test_number]
        save_tests()  # Сохраняем изменения
        await update.message.reply_text(f"✅ Тест #{test_number} удален!")
    else:
        await update.message.reply_text(f"❌ Тест #{test_number} не найден.")


# Команда /test - информация о конкретном тесте
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "ℹ️ *Информация о тесте*\n\n"
            "Использование:\n"
            "/test <номер_теста>\n\n"
            "Пример:\n"
            "/test 1"
        )
        return

    test_number = context.args[0]

    if test_number in TESTS:
        test_data = TESTS[test_number]

        # Создаем кнопку для перехода к тесту
        keyboard = [
            [InlineKeyboardButton("📝 Перейти к тесту", url=test_data['link'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📚 *Тест #{test_number}*\n\n"
            f"📖 Предмет: {test_data['subject']}\n"
            f"📊 Количество заданий: {test_data['tasks_count']}\n"
            f"🎲 Разные варианты: {'Да' if test_data['has_variants'] else 'Нет'}\n"
            f"🔗 Ссылка: {test_data['link']}\n"
            f"📅 Добавлен: {test_data['added_date']}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ Тест #{test_number} не найден.")


# Команда /edittest - редактирование теста (только для админов)
async def edittest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "✏️ *Редактирование теста*\n\n"
            "Использование:\n"
            "/edittest <номер_теста> <поле> <новое_значение>\n\n"
            "Примеры:\n"
            "/edittest 1 subject Физика\n"
            "/edittest 1 tasks_count 10\n"
            "/edittest 1 has_variants Нет\n"
            "/edittest 1 link https://new-link.com\n\n"
            "Доступные поля: subject, tasks_count, has_variants, link"
        )
        return

    test_number = context.args[0]
    field = context.args[1]
    new_value = " ".join(context.args[2:]) if len(context.args) > 2 else ""

    if test_number not in TESTS:
        await update.message.reply_text(f"❌ Тест #{test_number} не найден.")
        return

    if field not in ['subject', 'tasks_count', 'has_variants', 'link']:
        await update.message.reply_text("❌ Неверное поле. Доступные поля: subject, tasks_count, has_variants, link")
        return

    try:
        if field == 'tasks_count':
            new_value = int(new_value)
        elif field == 'has_variants':
            new_value = new_value.lower() in ['да', 'yes', 'true', '1']

        old_value = TESTS[test_number][field]
        TESTS[test_number][field] = new_value
        TESTS[test_number]['updated_date'] = datetime.now().strftime("%d.%m.%Y %H:%M")

        save_tests()  # Сохраняем изменения

        await update.message.reply_text(
            f"✅ *Тест #{test_number} обновлен!*\n\n"
            f"📝 Поле: {field}\n"
            f"📄 Старое значение: {old_value}\n"
            f"🆕 Новое значение: {new_value}",
            parse_mode='Markdown'
        )

    except ValueError:
        await update.message.reply_text("❌ Неверный формат значения для этого поля.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при редактировании теста: {e}")


# Команда /uchiru - отправка ссылки
async def uchiru_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🎓 *Доступ к учебным материалам:*\n\n"
        f"🔗 {uchiru_link}\n\n"
        f"Приятного обучения! 📚",
        parse_mode='Markdown'
    )


# Команда /setuchiru - установка ссылки (только для админов)
async def set_uchiru_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global uchiru_link, LINKS

    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text(
            "🎓 *Установка ссылки для команды /uchiru*\n\n"
            "Использование:\n"
            "/setuchiru <ссылка>\n\n"
            "Пример:\n"
            "/setuchiru https://uchi.ru/classroom\n\n"
            f"Текущая ссылка: {uchiru_link}"
        )
        return

    new_link = " ".join(context.args)
    uchiru_link = new_link
    LINKS["uchiru"] = new_link
    save_links()  # Сохраняем изменения

    await update.message.reply_text(
        f"✅ Ссылка для команды /uchiru успешно обновлена!\n\n"
        f"Новая ссылка: {uchiru_link}",
        parse_mode='Markdown'
    )


# Функция проверки блок-листа
def is_user_blocked(user_id: int) -> bool:
    return user_id in BLOCKLIST


# Команда /block - добавить пользователя в блок-лист (только для админов)
async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text(
            "🚫 *Управление блок-листом*\n\n"
            "Использование:\n"
            "/block <user_id> - добавить пользователя в блок-лист\n"
            "/unblock <user_id> - удалить пользователя из блок-листа\n"
            "/blocklist - показать текущий блок-лист\n\n"
            "Чтобы получить user_id пользователя, попросите его написать @userinfobot"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if target_user_id in ADMINS:
            await update.message.reply_text("❌ Нельзя заблокировать администратора.")
            return

        if target_user_id in BLOCKLIST:
            await update.message.reply_text("⚠️ Этот пользователь уже в блок-листе.")
            return

        BLOCKLIST.append(target_user_id)
        save_blocklist()  # Сохраняем изменения
        await update.message.reply_text(f"✅ Пользователь {target_user_id} добавлен в блок-лист.")

    except ValueError:
        await update.message.reply_text("❌ Неверный формат user_id. User_id должен быть числом.")


# Команда /unblock - удалить пользователя из блок-листа (только для админов)
async def unblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование:\n"
            "/unblock <user_id> - удалить пользователя из блок-листа"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if target_user_id in BLOCKLIST:
            BLOCKLIST.remove(target_user_id)
            save_blocklist()  # Сохраняем изменения
            await update.message.reply_text(f"✅ Пользователь {target_user_id} удален из блок-листа.")
        else:
            await update.message.reply_text("⚠️ Этот пользователь не найден в блок-листе.")

    except ValueError:
        await update.message.reply_text("❌ Неверный формат user_id. User_id должен быть числом.")


# Команда /blocklist - показать блок-лист (только для админов)
async def blocklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not BLOCKLIST:
        await update.message.reply_text("📝 Блок-лист пуст.")
        return

    blocklist_text = "🚫 *Текущий блок-лист:*\n\n"
    for i, blocked_user_id in enumerate(BLOCKLIST, 1):
        blocklist_text += f"{i}. `{blocked_user_id}`\n"

    await update.message.reply_text(blocklist_text, parse_mode='Markdown')


# Команда /msg - отправка сообщения в группу от имени бота (только для админов)
async def msg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text(
            "💬 *Отправка сообщения в группу*\n\n"
            "Использование:\n"
            "/msg <текст сообщения>\n\n"
            "Пример:\n"
            "/msg Всем привет! Напоминаю о собрании завтра."
        )
        return

    message_text = " ".join(context.args)

    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message_text
        )
        await update.message.reply_text("✅ Сообщение успешно отправлено в группу!")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке сообщения: {e}")


# Команда /birthday - дни рождения
async def birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎂 Все дни рождения", callback_data="all_birthdays")],
        [InlineKeyboardButton("🎁 Ближайший день рождения", callback_data="next_birthday")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎉 *Дни рождения класса*\n\n"
        "Выберите опцию:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "all_birthdays":
        await show_all_birthdays(query)
    elif query.data == "next_birthday":
        await show_next_birthday(query)


# Показать все дни рождения
async def show_all_birthdays(query):
    # Сортируем по дате
    sorted_birthdays = sorted(birthdays, key=lambda x: (int(x['date'].split('.')[1]), int(x['date'].split('.')[0])))

    text = "🎂 *Все дни рождения класса:*\n\n"

    months = {
        '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
        '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
        '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
    }

    current_month = ""
    for bd in sorted_birthdays:
        month_num = bd['date'].split('.')[1]
        month_name = months[month_num]
        day = bd['date'].split('.')[0]

        if month_name != current_month:
            text += f"\n📅 *{month_name}:*\n"
            current_month = month_name

        text += f"• {bd['name']} - {day} {month_name}\n"

    await query.edit_message_text(text, parse_mode='Markdown')


# Показать ближайший день рождения
async def show_next_birthday(query):
    now = datetime.now()
    current_date = now.strftime("%d.%m")

    # Находим ближайший день рождения
    next_bd = None
    days_until = 365  # максимальное значение

    for bd in birthdays:
        bd_date = datetime.strptime(bd['date'] + f".{now.year}", "%d.%m.%Y")

        # Если день рождения уже прошел в этом году, смотрим на следующий год
        if bd_date < now:
            bd_date = datetime.strptime(bd['date'] + f".{now.year + 1}", "%d.%m.%Y")

        days = (bd_date - now).days

        if days < days_until:
            days_until = days
            next_bd = bd

    if next_bd:
        # Эмодзи в зависимости от того, скоро ли день рождения
        if days_until == 0:
            emoji = "🎉"
            message = "СЕГОДНЯ!"
        elif days_until <= 7:
            emoji = "🎁"
            message = f"через {days_until} дней"
        elif days_until <= 30:
            emoji = "📅"
            message = f"через {days_until} дней"
        else:
            emoji = "🗓️"
            message = f"через {days_until} дней"

        text = (
            f"{emoji} *Ближайший день рождения:*\n\n"
            f"👤 *{next_bd['name']}*\n"
            f"📅 {next_bd['date']}\n"
            f"⏰ {message}"
        )
    else:
        text = "❌ Не удалось найти ближайший день рождения"

    # Добавляем кнопку "Назад"
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="all_birthdays")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


# Команда /hv в группе с защитой от флуда и блок-листом
async def hv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    current_time = time_module.time()

    # Проверяем, является ли пользователь администратором
    is_admin = user_id in ADMINS

    # Для администраторов ограничение не применяется
    if not is_admin and update.effective_chat.type in ["group", "supergroup"]:
        # Проверяем, когда пользователь последний раз использовал команду
        if user_id in last_hv_usage:
            time_since_last_use = current_time - last_hv_usage[user_id]
            if time_since_last_use < 60:  # 60 секунд
                remaining_time = int(60 - time_since_last_use)
                await update.message.reply_text(
                    f"Вы можете использовать команду /hv только 1 раз в минуту.\n"
                    f"Попробуйте снова через {remaining_time} секунд."
                )
                return

        # Обновляем время последнего использования
        last_hv_usage[user_id] = current_time

    # Отправляем домашнее задание
    await update.message.reply_text(current_homework)


# Команда /rs - отправка расписания
async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule_text = """
📅 *РАСПИСАНИЕ ЗАНЯТИЙ 8Ж КЛАСС*

*ПОНЕДЕЛЬНИК*
1️⃣ Разговор о важном - Казаков С.А.
2️⃣ Русский язык - Александрова А.
3️⃣ Биология - Квитко О.Ф.
4️⃣ Технология - Файзуллин И.А. / Английский язык - Образцова О.С.
5️⃣ Алгебра - Тлюняева Е.В.
6️⃣ Физическая культура - Казаков С.А.
7️⃣ Вероятность и статистика - Тлюняева Е.В.

*ВТОРНИК*
1️⃣ Английский язык - Кадибагомаева З.А. / Английский язык - Образцова О.С.
2️⃣ История - Квитко Д.Ю.
3️⃣ Алгебра - Тлюняева Е.В.
4️⃣ Химия - Ханина А.Г.
5️⃣ Физика - Ушакова О.А.
6️⃣ Геометрия - Тлюняева Е.В.

*СРЕДА*
1️⃣ География - Скворцова Н.П.
2️⃣ Русский язык - Александрова А.
3️⃣ Английский язык - Кодибатомаева З.А. / Информатика - Мухтарова И.Р.
4️⃣ Литература - Александрова А.
5️⃣ Физическая культура - Казаков С.А.
6️⃣ Обществознание - Квитко Д.Ю.
7️⃣ Английский язык - Кадибагомаева З.А. / Технология - Мухтарова И.Р.

*ЧЕТВЕРГ*
1️⃣ Алгебра - Тлюняева Е.В.
2️⃣ ОБЖ - Ефремов Е.Н.
3️⃣ Английский язык - Образцова О.С. / Информатика - Файзуллин И.А.
4️⃣ Химия - Ханина А.Г.
5️⃣ Музыка - Ковалина А.В.
6️⃣ Геометрия - Тлюняева Е.В.
7️⃣ Биология - Квитко О.Ф.

*ПЯТНИЦА*
1️⃣ Алгебра - Тлюняева Е.В.
2️⃣ История - Квитко Д.Ю.
3️⃣ Русский язык - Александрова А.
4️⃣ Литература - Александрова А.
5️⃣ Геометрия - Тлюняева Е.В.
6️⃣ География - Скворцова Н.П.
7️⃣ Физика - Ушакова О.А.
    """

    await update.message.reply_text(schedule_text, parse_mode='Markdown')


# Команда /admin в группе
async def admin_command_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text(
            f"❌ Вы не являетесь администратором.\nВерсия: {versionbot}\n\nЕсли вы администратор и у вас ошибка обратитесь в личные сообщения - @tanzaniao")
        return

    await update.message.reply_text(
        "👨‍💻 Режим администратора.\n\n"
        "Отправьте текст домашнего задания: "
    )

    # Устанавливаем состояние ожидания текста
    context.user_data['waiting_for_homework'] = True


# Обработка текста от администратора
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Проверяем, что сообщение от администратора
    if user_id not in ADMINS:
        return

    # Проверяем, ожидаем ли мы текст ДЗ
    if context.user_data.get('waiting_for_homework'):
        global current_homework
        current_homework = update.message.text
        context.user_data['waiting_for_homework'] = False

        await update.message.reply_text("✅ Текст домашнего задания успешно обновлен!")


# Функция для отправки и закрепления сообщения
async def send_and_pin_message(context: ContextTypes.DEFAULT_TYPE):
    global pinned_message_id

    try:
        # Сначала открепляем старое сообщение, если оно есть
        if pinned_message_id:
            try:
                await context.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=pinned_message_id)
            except Exception:
                pass  # Игнорируем ошибки при откреплении

        # Отправляем новое сообщение
        message = await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"📚 Актуальное домашнее задание:\n\n{current_homework}"
        )

        # Закрепляем сообщение
        await context.bot.pin_chat_message(chat_id=GROUP_CHAT_ID, message_id=message.message_id)
        pinned_message_id = message.message_id

        print(f"✅ Сообщение закреплено в группе. ID: {pinned_message_id}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при закреплении сообщения: {e}")
        return False


# Функция для открепления сообщения в 00:00
async def unpin_message(context: ContextTypes.DEFAULT_TYPE):
    global pinned_message_id

    try:
        if pinned_message_id:
            await context.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=pinned_message_id)
            print(f"✅ Сообщение откреплено в 00:00. ID: {pinned_message_id}")
            pinned_message_id = None
    except Exception as e:
        print(f"❌ Ошибка при откреплении сообщения: {e}")


# Ручная отправка ДЗ с закреплением (для администраторов)
async def send_homework_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    if current_homework != "Администраторы не успели выложить актуальное домашнее задание. Ожидайте!":
        # Используем функцию отправки и закрепления
        success = await send_and_pin_message(context)
        if success:
            await update.message.reply_text("✅ ДЗ отправлено и закреплено в группе!")
        else:
            await update.message.reply_text("❌ Ошибка при отправке ДЗ. Проверьте права бота.")
    else:
        await update.message.reply_text("❌ ДЗ еще не установлено!")


# Обработчик старта для личных сообщений
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для отправки домашних заданий.\n\n"
        "Команды:\n"
        "/admin - установить ДЗ (только для администраторов)\n"
        "/send - отправить ДЗ в группу (с автозакреплением)\n"
        "/msg - отправить сообщение в группу (только для администраторов)\n"
        "/setuchiru - установить ссылку Uchi.ru (только для администраторов)\n"
        "/uchiru - получить ссылку на учебные материалы\n"
        "/addtest - добавить тест (только для администраторов)\n"
        "/tests - посмотреть все тесты\n"
        "/test - информация о конкретном тесте\n"
        "/edittest - редактировать тест (только для администраторов)\n"
        "/deltest - удалить тест (только для администраторов)\n"
        "/rs - показать расписание занятий\n"
        "/birthday - дни рождения одноклассников\n\n"
        "В группе используйте /hv чтобы посмотреть текущее ДЗ\n"
        "⚠️ *Ограничение:* 1 раз в 60 секунд"
    )


# Настройка планировщика
def setup_scheduler(application):
    try:
        moscow_tz = pytz.timezone('Europe/Moscow')

        # Задача для открепления сообщения в 00:00
        application.job_queue.run_daily(
            unpin_message,
            time=time(21, 59, 0, tzinfo=moscow_tz),
            days=tuple(range(7)),
            name="unpin_midnight"
        )

        print("✅ Планировщик настроен: автооткрепление в 00:00")

    except Exception as e:
        print(f"❌ Ошибка настройки планировщика: {e}")


def main():
    # Создаем Application с JobQueue
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд для группы
    application.add_handler(CommandHandler("hv", hv_command))
    application.add_handler(CommandHandler("admin", admin_command_group))
    application.add_handler(CommandHandler("rs", schedule_command))
    application.add_handler(CommandHandler("birthday", birthday_command))

    # Обработчики для личных сообщений
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("send", send_homework_manual))
    application.add_handler(CommandHandler("msg", msg_command))
    application.add_handler(CommandHandler("block", block_command))
    application.add_handler(CommandHandler("unblock", unblock_command))
    application.add_handler(CommandHandler("blocklist", blocklist_command))
    application.add_handler(CommandHandler("setuchiru", set_uchiru_command))
    application.add_handler(CommandHandler("uchiru", uchiru_command))
    application.add_handler(CommandHandler("addtest", addtest_command))
    application.add_handler(CommandHandler("tests", tests_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("edittest", edittest_command))
    application.add_handler(CommandHandler("deltest", deltest_command))
    application.add_handler(CommandHandler("rs", schedule_command))
    application.add_handler(CommandHandler("birthday", birthday_command))
    application.add_handler(CommandHandler("cd", chat_members_command))

    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))

    # Обработчик текстовых сообщений от администраторов
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE,
        handle_admin_message
    ))

    # Настраиваем планировщик
    if application.job_queue:
        setup_scheduler(application)
    else:
        print("⚠️ JobQueue не доступен. Автооткрепление не работает.")

    print("Успешный запуск!")
    print(f"📋 Загружен блок-лист: {BLOCKLIST}")
    print(f"🎓 Ссылка Uchi.ru: {uchiru_link}")
    print(f"📚 Загружено тестов: {len(TESTS)}")
    print(f"🔗 Загружено ссылок: {len(LINKS)}")

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()