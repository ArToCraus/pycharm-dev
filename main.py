import asyncio
import json
import datetime
import hashlib
import base64
from typing import Dict, List, Optional

import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8314233287:AAEstEl" + "HTk2-cPRCMe0rcy3WdZ-7k5B1cCM"
GITHUB_TOKEN = "ghp_22tRqvzoe" + "reLyuzU1yLqWjwfldpBpE1k1scj"
REPO_URL = "https://api.github.com/repos/LibyX13/school-portal/contents/date.json"

# Учителя, которых оценивает Михайлов Мирон
TEACHERS = {
    "kadibagomaeva": {
        "full_name": "Кадибагомаева Заира Амирбековна",
        "subjects": ["Иностранный (английский) язык"]
    },
    "kvitko_d": {
        "full_name": "Квитко Дмитрий Юрьевич",
        "subjects": ["Обществознание", "История"]
    },
    "alexandrova": {
        "full_name": "Александрова Анна Алексеевна",
        "subjects": ["Русский язык", "Литература"]
    },
    "naumova": {
        "full_name": "Наумова Наталия Петровна",
        "subjects": ["Физика"]
    },
    "kazakov": {
        "full_name": "Казаков Семён Анатольевич",
        "subjects": ["Физическая культура"]
    },
    "kvitko_o": {
        "full_name": "Квитко Оксана Федоровна",
        "subjects": ["Биология"]
    },
    "tlyunyaeva": {
        "full_name": "Тлюняева Елена Валерьевна",
        "subjects": ["Алгебра", "Геометрия", "Вероятность и статистика"]
    },
    "khanina": {
        "full_name": "Ханина Амина Габдулловна",
        "subjects": ["Химия"]
    },
    "skvortsova": {
        "full_name": "Скворцова Надежда Петровна",
        "subjects": ["География"]
    },
    "ushakova": {
        "full_name": "Ушакова Ольга Алексеевна",
        "subjects": ["Физика"]
    },
    "faizullin": {
        "full_name": "Файзуллин Ирек Ансарович",
        "subjects": ["Информатика", "Труд (технология)"]
    },
    "efremov": {
        "full_name": "Ефремов Евгений Николаевич",
        "subjects": ["ОБЖ"]
    },
    "kovyazina": {
        "full_name": "Ковязина Анна Викторовна",
        "subjects": ["Музыка"]
    }
}

# Учитель, который выставляет оценки (вы)
EVALUATOR = "Михайлов Мирон"

# Расписание по дням недели
SCHEDULE = {
    0: ["Русский язык", "Биология", "Технология", "Алгебра", "Физкультура", "Геометрия"],
    1: ["Английский", "История", "Алгебра", "Химия", "Физика", "Геометрия"],
    2: ["География", "Русский", "Английский", "Литература", "Физкультура", "Обществознание", "Английский"],
    3: ["Алгебра", "ОБЖ", "Информатика", "Химия", "Музыка", "Вероятность", "Биология"],
    4: ["Алгебра", "История", "Русский", "Литература", "Геометрия", "География", "Физика"]
}

# Оценки для учителей
GRADES = ["2", "3", "4", "5", "П"]  # П - пропуск


# Состояния FSM
class GradeStates(StatesGroup):
    selecting_teacher = State()
    selecting_subject = State()
    selecting_date = State()
    selecting_grade = State()


# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Кэш для данных
data_cache = None
cache_time = None


async def load_data() -> Dict:
    """Загружает данные из GitHub с кэшированием"""
    global data_cache, cache_time

    # Проверяем кэш (актуален 30 секунд)
    if data_cache and cache_time and (datetime.datetime.now() - cache_time).seconds < 30:
        return data_cache

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(REPO_URL, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    content = base64.b64decode(data['content']).decode('utf-8')
                    data_cache = json.loads(content)
                    cache_time = datetime.datetime.now()
                    return data_cache
                else:
                    logger.error(f"GitHub API error: {response.status}")
                    return {"grades": []}
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return {"grades": []}


async def save_data(data: Dict) -> bool:
    """Сохраняет данные в GitHub"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # Сначала получаем текущий SHA файла
        async with aiohttp.ClientSession() as session:
            async with session.get(REPO_URL, headers=headers, timeout=10) as response:
                if response.status == 200:
                    file_data = await response.json()
                    sha = file_data['sha']
                else:
                    logger.error(f"Cannot get file SHA: {response.status}")
                    return False

            # Подготавливаем данные для отправки
            content = json.dumps(data, ensure_ascii=False, indent=2)
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

            update_data = {
                "message": f"Update grades {datetime.datetime.now().isoformat()}",
                "content": encoded_content,
                "sha": sha
            }

            # Отправляем обновление
            async with session.put(REPO_URL, headers=headers, json=update_data, timeout=10) as response:
                if response.status == 200:
                    # Обновляем кэш
                    global data_cache, cache_time
                    data_cache = data
                    cache_time = datetime.datetime.now()
                    return True
                else:
                    logger.error(f"Cannot save data: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return False


def get_subject_hash(subject_name: str) -> str:
    """Получает хэш для предмета"""
    return hashlib.md5(subject_name.encode()).hexdigest()[:8]


# Клавиатуры
def get_main_keyboard():
    """Основная клавиатура"""
    buttons = [
        [InlineKeyboardButton(text="📝 Выставить оценку учителю", callback_data="add_grade")],
        [InlineKeyboardButton(text="❌ Удалить оценку", callback_data="delete_grade")],
        [InlineKeyboardButton(text="📊 Посмотреть все оценки", callback_data="view_grades")],
        [InlineKeyboardButton(text="📈 Средний балл учителей за месяц", callback_data="month_average")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_grades_keyboard():
    """Клавиатура с оценками"""
    buttons = []
    row = []
    for grade in GRADES:
        row.append(InlineKeyboardButton(text=grade, callback_data=f"grade_{grade}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_teachers_keyboard():
    """Клавиатура с учителями"""
    buttons = []
    for key, teacher in TEACHERS.items():
        # Сокращаем ФИО для отображения
        display_name = teacher["full_name"]
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."
        buttons.append([InlineKeyboardButton(
            text=display_name,
            callback_data=f"teacher_{key}"
        )])
    buttons.append([InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subjects_keyboard(teacher_key: str):
    """Клавиатура с предметами учителя"""
    buttons = []
    teacher = TEACHERS.get(teacher_key)
    if teacher:
        subjects = teacher["subjects"]
        for subject in subjects:
            sub_hash = get_subject_hash(subject)
            buttons.append([InlineKeyboardButton(
                text=subject,
                callback_data=f"subject_{teacher_key}_{sub_hash}"
            )])
    buttons.append([InlineKeyboardButton(text="↩️ Назад к учителям", callback_data="back_to_teachers")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_dates_keyboard(teacher_key: str, subject_hash: str, subject_name: str):
    """Клавиатура с доступными датами для предмета"""
    buttons = []
    today = datetime.date.today()

    # Находим предмет по хэшу
    teacher = TEACHERS.get(teacher_key)
    subject_found = None
    if teacher:
        for subj in teacher["subjects"]:
            if get_subject_hash(subj) == subject_hash:
                subject_found = subj
                break

    if not subject_found:
        subject_found = subject_name

    # Определяем, в какие дни недели есть этот предмет
    subject_lower = subject_found.lower()
    valid_days = []

    for day_num, subjects in SCHEDULE.items():
        day_subjects = [s.lower() for s in subjects]
        if subject_lower in day_subjects:
            valid_days.append(day_num)

    # Генерируем кнопки на ближайшие 7 дней
    for i in range(7):
        date = today + datetime.timedelta(days=i)
        if date.weekday() in valid_days:
            date_str = date.strftime("%d.%m.%Y")
            date_id = date.strftime("%Y%m%d")
            day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date.weekday()]
            buttons.append([
                InlineKeyboardButton(
                    text=f"{date_str} ({day_name})",
                    callback_data=f"date_{teacher_key}_{subject_hash}_{date_id}"
                )
            ])

    if not buttons:
        buttons.append([InlineKeyboardButton(text="Нет доступных дат", callback_data="no_dates")])

    buttons.append([InlineKeyboardButton(text="↩️ Назад к предметам", callback_data=f"back_to_subjects_{teacher_key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        f"👨‍🏫 Добро пожаловать, {EVALUATOR}!\n\n"
        "Это система оценки работы учителей.\n"
        "Вы можете:\n"
        "• Выставлять оценки коллегам\n"
        "• Удалять оценки\n"
        "• Просматривать все оценки\n"
        "• Смотреть средний балл учителей за месяц\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    """Показ главного меню"""
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )


# Обработчики колбэков для главного меню
@dp.callback_query(F.data == "add_grade")
async def process_add_grade(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса добавления оценки"""
    await state.set_state(GradeStates.selecting_teacher)
    await callback.message.edit_text(
        f"{EVALUATOR}, выберите учителя для оценки:",
        reply_markup=get_teachers_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "delete_grade")
async def process_delete_grade(callback: types.CallbackQuery):
    """Начало процесса удаления оценки"""
    await show_grades_for_deletion(callback)


@dp.callback_query(F.data == "view_grades")
async def process_view_grades(callback: types.CallbackQuery):
    """Просмотр всех оценок"""
    await show_all_grades(callback)


@dp.callback_query(F.data == "month_average")
async def process_month_average(callback: types.CallbackQuery):
    """Средний балл за месяц"""
    await show_month_average(callback)


# Обработка выбора учителя
@dp.callback_query(GradeStates.selecting_teacher, F.data.startswith("teacher_"))
async def process_select_teacher(callback: types.CallbackQuery, state: FSMContext):
    """Выбор учителя"""
    teacher_key = callback.data.replace("teacher_", "")
    teacher = TEACHERS.get(teacher_key)

    if teacher:
        await state.update_data(teacher_key=teacher_key, teacher_name=teacher["full_name"])
        await state.set_state(GradeStates.selecting_subject)

        await callback.message.edit_text(
            f"Учитель: {teacher['full_name']}\nВыберите предмет для оценки:",
            reply_markup=get_subjects_keyboard(teacher_key)
        )
    await callback.answer()


# Обработка выбора предмета
@dp.callback_query(GradeStates.selecting_subject, F.data.startswith("subject_"))
async def process_select_subject(callback: types.CallbackQuery, state: FSMContext):
    """Выбор предмета"""
    data_parts = callback.data.replace("subject_", "").split("_", 1)
    if len(data_parts) != 2:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    teacher_key, subject_hash = data_parts[0], data_parts[1]

    # Находим полное название предмета
    teacher = TEACHERS.get(teacher_key)
    subject_name = "Неизвестный предмет"
    if teacher:
        for subj in teacher["subjects"]:
            if get_subject_hash(subj) == subject_hash:
                subject_name = subj
                break

    await state.update_data(
        teacher_key=teacher_key,
        subject_hash=subject_hash,
        subject_name=subject_name
    )
    await state.set_state(GradeStates.selecting_date)

    await callback.message.edit_text(
        f"Предмет: {subject_name}\nВыберите дату проведения урока:",
        reply_markup=get_dates_keyboard(teacher_key, subject_hash, subject_name)
    )
    await callback.answer()


# Обработка выбора даты
@dp.callback_query(GradeStates.selecting_date, F.data.startswith("date_"))
async def process_select_date(callback: types.CallbackQuery, state: FSMContext):
    """Выбор даты"""
    data_parts = callback.data.replace("date_", "").split("_", 3)
    if len(data_parts) < 3:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    teacher_key, subject_hash, date_id = data_parts[0], data_parts[1], data_parts[2]

    # Преобразуем date_id в формат даты
    try:
        date_obj = datetime.datetime.strptime(date_id, "%Y%m%d")
        date_str = date_obj.strftime("%d.%m.%Y")
    except:
        date_str = date_id

    await state.update_data(date=date_str)
    await state.set_state(GradeStates.selecting_grade)

    data = await state.get_data()
    teacher_name = data.get('teacher_name', 'Неизвестный учитель')
    subject_name = data.get('subject_name', 'Неизвестный предмет')

    await callback.message.edit_text(
        f"📝 Выставление оценки:\n\n"
        f"Оценивающий: {EVALUATOR}\n"
        f"Учитель: {teacher_name}\n"
        f"Предмет: {subject_name}\n"
        f"Дата урока: {date_str}\n\n"
        f"Выберите оценку:",
        reply_markup=get_grades_keyboard()
    )
    await callback.answer()


# Обработка выбора оценки
@dp.callback_query(GradeStates.selecting_grade, F.data.startswith("grade_"))
async def process_save_grade(callback: types.CallbackQuery, state: FSMContext):
    """Сохранение оценки"""
    grade = callback.data.replace("grade_", "")

    data = await state.get_data()

    if not all(k in data for k in ['teacher_name', 'subject_name', 'date']):
        await callback.message.edit_text("❌ Ошибка: недостаточно данных")
        await state.clear()
        return

    # Загружаем текущие данные
    all_data = await load_data()

    # Добавляем новую оценку
    new_grade = {
        "evaluator": EVALUATOR,  # Кто выставил оценку
        "teacher": data['teacher_name'],  # Кому выставили
        "subject": data['subject_name'],
        "date": data['date'],
        "grade": grade,
        "added_at": datetime.datetime.now().isoformat()
    }

    all_data.setdefault("grades", []).append(new_grade)

    # Сохраняем данные
    if await save_data(all_data):
        await callback.message.edit_text(
            f"✅ Оценка успешно выставлена!\n\n"
            f"Оценивающий: {EVALUATOR}\n"
            f"Учитель: {data['teacher_name']}\n"
            f"Предмет: {data['subject_name']}\n"
            f"Дата урока: {data['date']}\n"
            f"Оценка: {grade}"
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сохранении данных. Попробуйте позже."
        )

    await state.clear()
    await callback.answer()


# Обработчики кнопок "Назад"
@dp.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "back_to_teachers")
async def process_back_to_teachers(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору учителя"""
    await state.set_state(GradeStates.selecting_teacher)
    await callback.message.edit_text(
        f"{EVALUATOR}, выберите учителя для оценки:",
        reply_markup=get_teachers_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("back_to_subjects_"))
async def process_back_to_subjects(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору предмета"""
    teacher_key = callback.data.replace("back_to_subjects_", "")
    teacher = TEACHERS.get(teacher_key)

    if teacher:
        await state.update_data(teacher_key=teacher_key, teacher_name=teacher["full_name"])
        await state.set_state(GradeStates.selecting_subject)
        await callback.message.edit_text(
            f"Учитель: {teacher['full_name']}\nВыберите предмет для оценки:",
            reply_markup=get_subjects_keyboard(teacher_key)
        )
    await callback.answer()


# Функции для просмотра и удаления оценок
async def show_all_grades(callback: types.CallbackQuery):
    """Показывает все оценки"""
    data = await load_data()
    grades = data.get("grades", [])

    if not grades:
        await callback.message.edit_text("📭 Оценок пока нет.", reply_markup=get_main_keyboard())
        return

    # Фильтруем только оценки, выставленные текущим пользователем
    user_grades = [g for g in grades if g.get('evaluator') == EVALUATOR]

    if not user_grades:
        await callback.message.edit_text("📭 Вы ещё не выставляли оценок.", reply_markup=get_main_keyboard())
        return

    # Группируем оценки по учителям
    teacher_grades = {}
    for grade in user_grades:
        teacher = grade['teacher']
        if teacher not in teacher_grades:
            teacher_grades[teacher] = []
        teacher_grades[teacher].append(grade)

    # Формируем сообщение
    message_text = f"📋 Все оценки, выставленные {EVALUATOR}:\n\n"

    for teacher, grade_list in teacher_grades.items():
        display_teacher = teacher[:35] + "..." if len(teacher) > 35 else teacher
        message_text += f"👨‍🏫 {display_teacher}:\n"

        # Группируем по предметам
        subject_grades = {}
        for grade in grade_list:
            subject = grade['subject']
            if subject not in subject_grades:
                subject_grades[subject] = []
            subject_grades[subject].append(grade)

        for subject, sub_grades in subject_grades.items():
            display_subject = subject[:30] + "..." if len(subject) > 30 else subject
            message_text += f"  📚 {display_subject}:\n"
            for g in sub_grades:
                message_text += f"    • {g['date']}: {g['grade']}\n"
        message_text += "\n"

    buttons = [[InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")]]

    if len(message_text) > 4000:
        parts = [message_text[i:i + 4000] for i in range(0, len(message_text), 4000)]
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                await callback.message.answer(part, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            else:
                await callback.message.answer(part)
    else:
        await callback.message.edit_text(message_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    await callback.answer()


async def show_grades_for_deletion(callback: types.CallbackQuery):
    """Показывает оценки для удаления"""
    data = await load_data()
    grades = data.get("grades", [])

    # Фильтруем только оценки текущего пользователя
    user_grades = [g for g in grades if g.get('evaluator') == EVALUATOR]

    if not user_grades:
        await callback.message.edit_text("📭 У вас нет оценок для удаления.", reply_markup=get_main_keyboard())
        return

    # Показываем последние 20 оценок для удаления
    buttons = []
    for i, grade in enumerate(user_grades[-20:]):
        real_index = len(grades) - len(user_grades) + i

        # Формируем короткую строку для кнопки
        short_teacher = grade['teacher']
        if len(short_teacher) > 20:
            parts = short_teacher.split()
            if len(parts) >= 2:
                short_teacher = f"{parts[0]} {parts[1][0]}."
            else:
                short_teacher = short_teacher[:17] + "..."

        short_subject = grade['subject']
        if len(short_subject) > 15:
            short_subject = short_subject[:12] + "..."

        btn_text = f"{grade['date']} - {short_teacher} - {grade['grade']}"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text[:40],
                callback_data=f"delete_{real_index}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")])

    await callback.message.edit_text(
        f"Выберите оценку для удаления (ваши последние 20 оценок):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("delete_"))
async def process_confirm_delete(callback: types.CallbackQuery):
    """Подтверждение удаления оценки"""
    try:
        index = int(callback.data.replace("delete_", ""))
    except ValueError:
        await callback.answer("Ошибка индекса", show_alert=True)
        return

    data = await load_data()
    grades = data.get("grades", [])

    if 0 <= index < len(grades):
        grade = grades[index]

        # Проверяем, что это оценка текущего пользователя
        if grade.get('evaluator') != EVALUATOR:
            await callback.answer("Вы можете удалять только свои оценки", show_alert=True)
            return

        buttons = [
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{index}")],
            [InlineKeyboardButton(text="❌ Нет, отмена", callback_data="delete_grade")]
        ]

        await callback.message.edit_text(
            f"Вы уверены, что хотите удалить оценку?\n\n"
            f"Учитель: {grade['teacher']}\n"
            f"Предмет: {grade['subject']}\n"
            f"Дата: {grade['date']}\n"
            f"Оценка: {grade['grade']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_delete_"))
async def process_final_delete(callback: types.CallbackQuery):
    """Финальное удаление оценки"""
    try:
        index = int(callback.data.replace("confirm_delete_", ""))
    except ValueError:
        await callback.answer("Ошибка индекса", show_alert=True)
        return

    data = await load_data()
    grades = data.get("grades", [])

    if 0 <= index < len(grades):
        deleted_grade = grades.pop(index)
        data["grades"] = grades

        if await save_data(data):
            await callback.message.edit_text(
                f"✅ Оценка удалена!\n\n"
                f"Учитель: {deleted_grade['teacher']}\n"
                f"Оценка: {deleted_grade['grade']}"
            )
        else:
            await callback.message.edit_text("❌ Ошибка при удалении.")

    await callback.answer()


async def show_month_average(callback: types.CallbackQuery):
    """Показывает средний балл за месяц"""
    data = await load_data()
    grades = data.get("grades", [])

    if not grades:
        await callback.message.edit_text("📭 Оценок за месяц нет.", reply_markup=get_main_keyboard())
        return

    # Фильтруем оценки за текущий месяц (кроме пропусков)
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year

    monthly_grades = []
    for grade in grades:
        try:
            grade_date = datetime.datetime.strptime(grade['date'], "%d.%m.%Y")
            if (grade_date.month == current_month and
                    grade_date.year == current_year and
                    grade['grade'] != 'П'):
                monthly_grades.append(grade)
        except:
            continue

    if not monthly_grades:
        await callback.message.edit_text("📭 Оценок за текущий месяц нет.", reply_markup=get_main_keyboard())
        return

    # Группируем по учителям и считаем средний балл
    teacher_stats = {}

    for grade in monthly_grades:
        teacher = grade['teacher']
        if teacher not in teacher_stats:
            teacher_stats[teacher] = {"sum": 0, "count": 0, "evaluators": set()}

        if grade['grade'].isdigit():
            teacher_stats[teacher]["sum"] += int(grade['grade'])
            teacher_stats[teacher]["count"] += 1
            if 'evaluator' in grade:
                teacher_stats[teacher]["evaluators"].add(grade['evaluator'])

    # Формируем сообщение
    month_name = datetime.datetime.now().strftime('%B %Y')
    message_text = f"📊 Средние баллы учителей за {month_name}:\n\n"

    for teacher, stats in teacher_stats.items():
        if stats["count"] > 0:
            average = stats["sum"] / stats["count"]
            display_teacher = teacher[:30] + "..." if len(teacher) > 30 else teacher

            message_text += f"👨‍🏫 {display_teacher}:\n"
            message_text += f"  Средний балл: {average:.2f}\n"
            message_text += f"  Количество оценок: {stats['count']}\n"
            if stats["evaluators"]:
                evaluators_list = ", ".join(stats["evaluators"])
                if len(evaluators_list) > 30:
                    evaluators_list = evaluators_list[:27] + "..."
                message_text += f"  Оценивали: {evaluators_list}\n"
            message_text += "\n"

    buttons = [[InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")]]
    await callback.message.edit_text(message_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


# Обработчик для необработанных callback_data
@dp.callback_query()
async def handle_unknown_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик для неизвестных callback_data"""
    logger.warning(f"Unhandled callback data: {callback.data}")

    # Если callback_data начинается с "no_dates", обрабатываем отдельно
    if callback.data == "no_dates":
        await callback.answer("Нет доступных дат для этого предмета", show_alert=True)
        # Возвращаем к выбору предмета
        data = await state.get_data()
        teacher_key = data.get('teacher_key')
        if teacher_key:
            teacher = TEACHERS.get(teacher_key)
            if teacher:
                await state.set_state(GradeStates.selecting_subject)
                await callback.message.edit_text(
                    f"Учитель: {teacher['full_name']}\nВыберите другой предмет:",
                    reply_markup=get_subjects_keyboard(teacher_key)
                )
        return

    await callback.answer("Команда не распознана. Возвращаю в меню...", show_alert=True)
    await state.clear()
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )


# Основная функция
async def main():
    print(f"✅ Бот запущен для {EVALUATOR}...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())