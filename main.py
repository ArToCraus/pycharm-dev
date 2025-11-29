import asyncio
import logging
from datetime import datetime, time, timedelta
import pytz
import json
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import time as time_module

# Отключаем логирование
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.disable(logging.CRITICAL)

# Конфигурация
BOT_TOKEN = "8236867741:AAEWPBaBOH-kK6KRc9QB7EO4X1dG6DGMCdE"
GROUP_CHAT_ID = "-1002364657409"
GITHUB_TOKEN = "ghp_LoFmLz9T4iPEQbj33" + "34pgnDnIDEMUV2qCDLC"
GITHUB_REPO = "LibyX13/test"  # Замените на ваш репозиторий
GITHUB_FILE_PATH = "data.json"

versionbot = "3.2.12 - Stable"

# Список администраторов
ADMINS = [5403608788, 6879963816, 1295169352, 6283747542]


# Структура данных
class DataManager:
    def __init__(self, github_token: str, repo: str, file_path: str):
        self.github_token = github_token
        self.repo = repo
        self.file_path = file_path
        self.base_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Данные по умолчанию
        self.default_data = {
            "blocklist": [],
            "tests": {},
            "links": {"uchiru": "https://example.com"},
            "homework": "Администраторы не успели выложить актуальное домашнее задание. Ожидайте!",
            "birthdays": [
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
        }

        self.data = self.default_data.copy()

    async def load_data(self) -> bool:
        """Загружает данные из GitHub"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.json()
                        import base64
                        decoded_content = base64.b64decode(content['content']).decode('utf-8')
                        self.data = json.loads(decoded_content)
                        print("✅ Данные успешно загружены из GitHub")
                        return True
                    else:
                        print("⚠️ Файл не найден, используются данные по умолчанию")
                        self.data = self.default_data.copy()
                        return await self.save_data()
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            self.data = self.default_data.copy()
            return False

    async def save_data(self) -> bool:
        """Сохраняет данные в GitHub"""
        try:
            # Сначала получаем текущий SHA файла
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, headers=self.headers) as response:
                    sha = None
                    if response.status == 200:
                        content = await response.json()
                        sha = content['sha']

            # Подготавливаем данные для отправки
            import base64
            content = json.dumps(self.data, ensure_ascii=False, indent=2)
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

            data = {
                "message": f"Auto-update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": encoded_content,
                "sha": sha
            }

            # Отправляем запрос на обновление
            async with aiohttp.ClientSession() as session:
                async with session.put(self.base_url, headers=self.headers, json=data) as response:
                    if response.status in [200, 201]:
                        print("✅ Данные успешно сохранены в GitHub")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Ошибка сохранения: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")
            return False

    def get_blocklist(self):
        return self.data.get("blocklist", [])

    def get_tests(self):
        return self.data.get("tests", {})

    def get_links(self):
        return self.data.get("links", {"uchiru": "https://example.com"})

    def get_homework(self):
        return self.data.get("homework", "Администраторы не успели выложить актуальное домашнее задание. Ожидайте!")

    def get_birthdays(self):
        return self.data.get("birthdays", [])

    async def update_blocklist(self, blocklist):
        self.data["blocklist"] = blocklist
        return await self.save_data()

    async def update_tests(self, tests):
        self.data["tests"] = tests
        return await self.save_data()

    async def update_links(self, links):
        self.data["links"] = links
        return await self.save_data()

    async def update_homework(self, homework):
        self.data["homework"] = homework
        return await self.save_data()


# Инициализация менеджера данных
data_manager = DataManager(GITHUB_TOKEN, GITHUB_REPO, GITHUB_FILE_PATH)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_for_homework = State()


# Переменные для временного хранения
pinned_message_id = None
last_hv_usage = {}


# Вспомогательные функции
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


def is_user_blocked(user_id: int) -> bool:
    return user_id in data_manager.get_blocklist()


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
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
    await message.answer(text)


# Команда /hv в группе
@dp.message(Command("hv"))
async def cmd_hv(message: Message):
    user_id = message.from_user.id

    if is_user_blocked(user_id):
        return

    current_time = time_module.time()
    is_admin_user = is_admin(user_id)

    # Проверка флуда для не-админов
    if not is_admin_user and message.chat.type in ["group", "supergroup"]:
        if user_id in last_hv_usage:
            time_since_last_use = current_time - last_hv_usage[user_id]
            if time_since_last_use < 60:
                remaining_time = int(60 - time_since_last_use)
                await message.answer(
                    f"Вы можете использовать команду /hv только 1 раз в минуту.\n"
                    f"Попробуйте снова через {remaining_time} секунд."
                )
                return
        last_hv_usage[user_id] = current_time

    homework = data_manager.get_homework()
    await message.answer(homework)


# Команда /admin
@dp.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    await message.answer("👨‍💻 Режим администратора.\n\nОтправьте текст домашнего задания:")
    await state.set_state(AdminStates.waiting_for_homework)

from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, ADMINISTRATOR

# Обработка текста ДЗ от администратора
@dp.message(AdminStates.waiting_for_homework)
async def process_homework(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    success = await data_manager.update_homework(message.text)
    if success:
        await message.answer("✅ Текст домашнего задания успешно обновлен!")
    else:
        await message.answer("❌ Ошибка при сохранении ДЗ!")

    await state.clear()


# Команда /send
@dp.message(Command("send"))
async def cmd_send(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    homework = data_manager.get_homework()
    if homework != "Администраторы не успели выложить актуальное домашнее задание. Ожидайте!":
        success = await send_and_pin_message(homework)
        if success:
            await message.answer("✅ ДЗ отправлено и закреплено в группе!")
        else:
            await message.answer("❌ Ошибка при отправке ДЗ. Проверьте права бота.")
    else:
        await message.answer("❌ ДЗ еще не установлено!")


async def send_and_pin_message(text: str):
    global pinned_message_id
    try:
        # Открепляем старое сообщение
        if pinned_message_id:
            try:
                await bot.unpin_chat_message(GROUP_CHAT_ID, pinned_message_id)
            except Exception:
                pass

        # Отправляем и закрепляем новое
        full_text = f"📚 Актуальное домашнее задание:\n\n{text}"
        message = await bot.send_message(GROUP_CHAT_ID, full_text)
        await bot.pin_chat_message(GROUP_CHAT_ID, message.message_id)
        pinned_message_id = message.message_id
        return True
    except Exception as e:
        print(f"❌ Ошибка при закреплении: {e}")
        return False


# Команда /msg
@dp.message(Command("msg"))
async def cmd_msg(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    if not command.args:
        await message.answer(
            "💬 *Отправка сообщения в группу*\n\n"
            "Использование:\n"
            "/msg <текст сообщения>\n\n"
            "Пример:\n"
            "/msg Всем привет! Напоминаю о собрании завтра."
        )
        return

    try:
        await bot.send_message(GROUP_CHAT_ID, command.args)
        await message.answer("✅ Сообщение успешно отправлено в группу!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке сообщения: {e}")


# Команда /uchiru
@dp.message(Command("uchiru"))
async def cmd_uchiru(message: Message):
    links = data_manager.get_links()
    uchiru_link = links.get("uchiru", "https://example.com")

    await message.answer(
        f"🎓 *Доступ к учебным материалам:*\n\n"
        f"🔗 {uchiru_link}\n\n"
        f"Приятного обучения! 📚"
    )


# Команда /setuchiru
@dp.message(Command("setuchiru"))
async def cmd_set_uchiru(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    if not command.args:
        links = data_manager.get_links()
        current_link = links.get("uchiru", "https://example.com")
        await message.answer(
            "🎓 *Установка ссылки для команды /uchiru*\n\n"
            "Использование:\n"
            "/setuchiru <ссылка>\n\n"
            "Пример:\n"
            "/setuchiru https://uchi.ru/classroom\n\n"
            f"Текущая ссылка: {current_link}"
        )
        return

    links = data_manager.get_links()
    links["uchiru"] = command.args
    success = await data_manager.update_links(links)

    if success:
        await message.answer(f"✅ Ссылка для команды /uchiru успешно обновлена!\n\nНовая ссылка: {command.args}")
    else:
        await message.answer("❌ Ошибка при сохранении ссылки!")


# Команда /addtest
@dp.message(Command("addtest"))
async def cmd_addtest(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    if not command.args:
        await message.answer(
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

    args = command.args.split()
    if len(args) < 5:
        await message.answer("❌ Недостаточно аргументов. Нужно: номер_теста предмет количество_заданий варианты ссылка")
        return

    try:
        test_number = args[0]
        subject = args[1]
        tasks_count = int(args[2])
        has_variants = args[3].lower() in ['да', 'yes', 'true', '1']
        test_link = " ".join(args[4:])

        tests = data_manager.get_tests()
        tests[test_number] = {
            "subject": subject,
            "tasks_count": tasks_count,
            "has_variants": has_variants,
            "link": test_link,
            "added_date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        success = await data_manager.update_tests(tests)
        if success:
            await message.answer(
                f"✅ *Тест #{test_number} добавлен!*\n\n"
                f"📚 Предмет: {subject}\n"
                f"📊 Заданий: {tasks_count}\n"
                f"🎲 Разные варианты: {'Да' if has_variants else 'Нет'}\n"
                f"🔗 Ссылка: {test_link}\n"
                f"📅 Дата добавления: {tests[test_number]['added_date']}"
            )
        else:
            await message.answer("❌ Ошибка при сохранении теста!")

    except ValueError:
        await message.answer("❌ Неверный формат количества заданий. Должно быть число.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении теста: {e}")


# Команда /tests
@dp.message(Command("tests"))
async def cmd_tests(message: Message):
    tests = data_manager.get_tests()

    if not tests:
        await message.answer("📝 Тестов пока нет.")
        return

    tests_text = "📚 *Список тестов:*\n\n"
    for test_num, test_data in sorted(tests.items(), key=lambda x: x[0]):
        tests_text += (
            f"🔹 *Тест #{test_num}*\n"
            f"   📖 {test_data['subject']}\n"
            f"   📊 Заданий: {test_data['tasks_count']}\n"
            f"   🎲 Варианты: {'Да' if test_data['has_variants'] else 'Нет'}\n"
            f"   🔗 Ссылка: {test_data['link']}\n"
            f"   📅 {test_data['added_date']}\n\n"
        )

    await message.answer(tests_text)


# Команда /test
@dp.message(Command("test"))
async def cmd_test(message: Message, command: CommandObject):
    if not command.args:
        await message.answer(
            "ℹ️ *Информация о тесте*\n\n"
            "Использование:\n"
            "/test <номер_теста>\n\n"
            "Пример:\n"
            "/test 1"
        )
        return

    test_number = command.args.strip()
    tests = data_manager.get_tests()

    if test_number in tests:
        test_data = tests[test_number]

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="📝 Перейти к тесту", url=test_data['link']))

        await message.answer(
            f"📚 *Тест #{test_number}*\n\n"
            f"📖 Предмет: {test_data['subject']}\n"
            f"📊 Количество заданий: {test_data['tasks_count']}\n"
            f"🎲 Разные варианты: {'Да' if test_data['has_variants'] else 'Нет'}\n"
            f"🔗 Ссылка: {test_data['link']}\n"
            f"📅 Добавлен: {test_data['added_date']}",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(f"❌ Тест #{test_number} не найден.")


# Команда /deltest
@dp.message(Command("deltest"))
async def cmd_deltest(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    if not command.args:
        await message.answer(
            "🗑️ *Удаление теста*\n\n"
            "Использование:\n"
            "/deltest <номер_теста>\n\n"
            "Пример:\n"
            "/deltest 1"
        )
        return

    test_number = command.args.strip()
    tests = data_manager.get_tests()

    if test_number in tests:
        del tests[test_number]
        success = await data_manager.update_tests(tests)
        if success:
            await message.answer(f"✅ Тест #{test_number} удален!")
        else:
            await message.answer("❌ Ошибка при удалении теста!")
    else:
        await message.answer(f"❌ Тест #{test_number} не найден.")


# Команда /edittest
@dp.message(Command("edittest"))
async def cmd_edittest(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    if not command.args:
        await message.answer(
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

    args = command.args.split()
    if len(args) < 3:
        await message.answer("❌ Недостаточно аргументов. Нужно: номер_теста поле новое_значение")
        return

    test_number = args[0]
    field = args[1]
    new_value = " ".join(args[2:])

    tests = data_manager.get_tests()
    if test_number not in tests:
        await message.answer(f"❌ Тест #{test_number} не найден.")
        return

    if field not in ['subject', 'tasks_count', 'has_variants', 'link']:
        await message.answer("❌ Неверное поле. Доступные поля: subject, tasks_count, has_variants, link")
        return

    try:
        old_value = tests[test_number][field]

        if field == 'tasks_count':
            new_value = int(new_value)
        elif field == 'has_variants':
            new_value = new_value.lower() in ['да', 'yes', 'true', '1']

        tests[test_number][field] = new_value
        tests[test_number]['updated_date'] = datetime.now().strftime("%d.%m.%Y %H:%M")

        success = await data_manager.update_tests(tests)
        if success:
            await message.answer(
                f"✅ *Тест #{test_number} обновлен!*\n\n"
                f"📝 Поле: {field}\n"
                f"📄 Старое значение: {old_value}\n"
                f"🆕 Новое значение: {new_value}"
            )
        else:
            await message.answer("❌ Ошибка при обновлении теста!")

    except ValueError:
        await message.answer("❌ Неверный формат значения для этого поля.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при редактировании теста: {e}")


# Команда /block
@dp.message(Command("block"))
async def cmd_block(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    if not command.args:
        await message.answer(
            "🚫 *Управление блок-листом*\n\n"
            "Использование:\n"
            "/block <user_id> - добавить пользователя в блок-лист\n"
            "/unblock <user_id> - удалить пользователя из блок-листа\n"
            "/blocklist - показать текущий блок-лист\n\n"
        )
        return

    try:
        target_user_id = int(command.args)

        if target_user_id in ADMINS:
            await message.answer("❌ Нельзя заблокировать администратора.")
            return

        blocklist = data_manager.get_blocklist()
        if target_user_id in blocklist:
            await message.answer("⚠️ Этот пользователь уже в блок-листе.")
            return

        blocklist.append(target_user_id)
        success = await data_manager.update_blocklist(blocklist)
        if success:
            await message.answer(f"✅ Пользователь {target_user_id} добавлен в блок-лист.")
        else:
            await message.answer("❌ Ошибка при сохранении блок-листа!")

    except ValueError:
        await message.answer("❌ Неверный формат user_id. User_id должен быть числом.")


# Команда /unblock
@dp.message(Command("unblock"))
async def cmd_unblock(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    if not command.args:
        await message.answer("Использование:\n/unblock <user_id> - удалить пользователя из блок-листа")
        return

    try:
        target_user_id = int(command.args)
        blocklist = data_manager.get_blocklist()

        if target_user_id in blocklist:
            blocklist.remove(target_user_id)
            success = await data_manager.update_blocklist(blocklist)
            if success:
                await message.answer(f"✅ Пользователь {target_user_id} удален из блок-листа.")
            else:
                await message.answer("❌ Ошибка при сохранении блок-листа!")
        else:
            await message.answer("⚠️ Этот пользователь не найден в блок-листе.")

    except ValueError:
        await message.answer("❌ Неверный формат user_id. User_id должен быть числом.")


# Команда /blocklist
@dp.message(Command("blocklist"))
async def cmd_blocklist(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return

    blocklist = data_manager.get_blocklist()
    if not blocklist:
        await message.answer("📝 Блок-лист пуст.")
        return

    blocklist_text = "🚫 *Текущий блок-лист:*\n\n"
    for i, user_id in enumerate(blocklist, 1):
        blocklist_text += f"{i}. `{user_id}`\n"

    await message.answer(blocklist_text)


# Команда /rs
@dp.message(Command("rs"))
async def cmd_rs(message: Message):
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
    await message.answer(schedule_text)


# Команда /birthday
@dp.message(Command("birthday"))
async def cmd_birthday(message: Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎂 Все дни рождения", callback_data="all_birthdays"))
    builder.add(InlineKeyboardButton(text="🎁 Ближайший день рождения", callback_data="next_birthday"))

    await message.answer(
        "🎉 *Дни рождения класса*\n\nВыберите опцию:",
        reply_markup=builder.as_markup()
    )


# Обработчики кнопок для дней рождения
@dp.callback_query(F.data == "all_birthdays")
async def show_all_birthdays(callback: CallbackQuery):
    birthdays = data_manager.get_birthdays()
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

    await callback.message.edit_text(text)


@dp.callback_query(F.data == "next_birthday")
async def show_next_birthday(callback: CallbackQuery):
    birthdays = data_manager.get_birthdays()
    now = datetime.now()
    current_date = now.strftime("%d.%m")

    next_bd = None
    days_until = 365

    for bd in birthdays:
        bd_date = datetime.strptime(bd['date'] + f".{now.year}", "%d.%m.%Y")

        if bd_date < now:
            bd_date = datetime.strptime(bd['date'] + f".{now.year + 1}", "%d.%m.%Y")

        days = (bd_date - now).days

        if days < days_until:
            days_until = days
            next_bd = bd

    if next_bd:
        if days_until == 0:
            emoji = "🎉"
            message_text = "СЕГОДНЯ!"
        elif days_until <= 7:
            emoji = "🎁"
            message_text = f"через {days_until} дней"
        elif days_until <= 30:
            emoji = "📅"
            message_text = f"через {days_until} дней"
        else:
            emoji = "🗓️"
            message_text = f"через {days_until} дней"

        text = (
            f"{emoji} *Ближайший день рождения:*\n\n"
            f"👤 *{next_bd['name']}*\n"
            f"📅 {next_bd['date']}\n"
            f"⏰ {message_text}"
        )
    else:
        text = "❌ Не удалось найти ближайший день рождения"

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="all_birthdays"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# Функция автооткрепления сообщения
async def unpin_message():
    global pinned_message_id
    try:
        if pinned_message_id:
            await bot.unpin_chat_message(GROUP_CHAT_ID, pinned_message_id)
            print(f"✅ Сообщение откреплено в 00:00. ID: {pinned_message_id}")
            pinned_message_id = None
    except Exception as e:
        print(f"❌ Ошибка при откреплении сообщения: {e}")


# Задача для планировщика
async def scheduled_unpin():
    moscow_tz = pytz.timezone('Europe/Moscow')
    while True:
        now = datetime.now(moscow_tz)
        target_time = now.replace(hour=21, minute=59, second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        await unpin_message()


# Основная функция
async def main():
    # Загружаем данные при старте
    await data_manager.load_data()

    print("Успешный запуск!")
    print(f"📋 Загружен блок-лист: {data_manager.get_blocklist()}")
    print(f"🎓 Ссылка Uchi.ru: {data_manager.get_links().get('uchiru', 'https://example.com')}")
    print(f"📚 Загружено тестов: {len(data_manager.get_tests())}")
    print(f"📝 Текущее ДЗ: {data_manager.get_homework()[:50]}...")

    # Запускаем задачу автооткрепления
    asyncio.create_task(scheduled_unpin())

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
