elebot
import mysql.connector
from flask import Flask, request
from telebot import types
from datetime import datetime
import os

# Для сохранения изображений адоптов
IMAGE_DIR = "Image"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

#  Телеграм-бот

token = "7671111074:AAEiJuIE5TqNpPJhvRRgPPyPmoZSjRW4gDQ"
bot = telebot.TeleBot(token, parse_mode="HTML")
# app = Flask(__name__)

# @app.route(f"/{token}", methods=["POST"])
# def webhook():
#     print("Получен запрос от Telegram! - Webhook")
#     json_update = request.get_json()
#     if json_update:
#         print(f"Данные запроса: {json_update}")
#         bot.process_new_updates([telebot.types.Update.de_json(json_update)])
#     else:
#         print("Пустой запрос от Telegram")
#     return "OK", 200

admin_state = {}
user_state = {}
user_orders = {}
current_page = {}
page_size = 1
delete_message_bot ={}
admin_data_publicate = {}
admin_new_price = {}

image_extantion = (".jpg", ".jpeg", ".png", ".gif", )
# Настройки базы данных пользователя

db_config = {
    'unix_socket': '/var/run/mysqld/mysqld.sock',  # Путь к сокету MySQL
    'user': 'root',                                # Пользователь root
    'database': 'ваша_база_данных',               # Имя базы данных
    'raise_on_warnings': True
}

try:
    conn = mysql.connector.connect(**db_config)
    if conn.is_connected():
        print(">> Подключение к MySQL установлено!")
        conn.close()
    else:
        print(">> Подключение не установлено.")
except mysql.connector.Error as e:
    print(f">> Ошибка подключения к MySQL: {e}")

# !ТЕСТ! Выбор единственного администратора
print("1) hiriimosa\n2) piknave\nВыберите администратора:")
choose_admin = 2
if choose_admin==1:
    admin_id = 945985582
    print("Добро пожаловать, Hiriimosa (ID: 945985582)")
else:
    admin_id = 1039505409
    print("Добро пожаловать, Piknave (ID: 1039505409)")
print("Запущен!..")

# Кнопки

button_order            = types.KeyboardButton("Сделать заказ")
button_about_me         = types.KeyboardButton("Обо мне")

button_orders                   = types.KeyboardButton("Заказы")
button_publication_adopt_admin  = types.KeyboardButton("Выложить адопта")

button_published_adopt    = types.KeyboardButton("Адопты")

# Инициализация кнопок для пользователя
keyboard_user = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_user.add(button_order,
                        button_published_adopt)

# Инициализация кнопок для автора
keyboard_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_admin.add(button_orders,
                        button_publication_adopt_admin,
                        button_published_adopt)

def confirming_admin(chat_user_id):
    if chat_user_id == admin_id:
        return False
    else:
        return True

@bot.message_handler(commands=['start'])
def send_start_message(message):
    print(f"Команда /start получена от {message.chat.id}")
    bot.send_message(message.chat.id, "Тестовое сообщение")
    user_id = message.chat.id
    try:
        if user_id == admin_id:
            bot.send_message(admin_id, "Приветствую, piknave!", parse_mode=None, reply_markup=keyboard_admin)
        else:
            folder_Image = "/home/hiriimosa/piknave_TeleBot/Image"  # Абсолютный путь
            group_main_photos = []

            if os.path.exists(folder_Image):
                    for file in os.listdir(folder_Image):
                        if file.lower().endswith(image_extantion):
                            file_path = os.path.join(folder_Image, file)
                            group_main_photos.append(types.InputMediaPhoto(open(file_path, "rb")))

            if group_main_photos:
                    bot.send_media_group(message.chat.id, group_main_photos)
            else:
                print("Нет изображений для отправки")

            bot.send_message(message.chat.id, "Добро пожаловать! Я piknave!", reply_markup=keyboard_user)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Повторите позже.")
    # Просмотр опубликованных адоптов
@bot.message_handler(func = lambda message:message.text == "Адопты")
def view_adoptions(message):
    user_id = message.chat.id

    show_adopt_page(message, user_id )

def get_user_state(user_id):
    if user_id not in user_state:
        user_state[user_id] = {'pages': 0}
    return user_state[user_id]

def get_existing_list_adopts():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM art_lots_links WHERE status = 'активен'"
    cursor.execute(sql)
    adoptions = cursor.fetchall()
    cursor.close()
    conn.close()
    if len(adoptions)==0:
        adoptions = {}
    return adoptions

def show_adopt_page(message, user_id,edit = False):
    state = get_user_state(user_id)
    current_index = state.get('current_adopt_index', 0)
    adoptions = get_existing_list_adopts()

    if len(adoptions) == 0:
        bot.send_message(user_id, "📭 Список адоптов пуст.")
        return

    current_index = max(0, min(current_index, len(adoptions) - 1))
    state['current_adopt_list'] = current_index
    adopt_info = adoptions[current_index]

    text = (
        f"📌 Адопт №{adopt_info['id']}\n"
        f"👤 Название: {adopt_info['title']}\n"
        f"📝 Описание: {adopt_info['description']}\n"
        f"📅 Нач: {adopt_info['price']} руб./ {adopt_info['price'] / 100} $\n"
        f"📅 Мин: {adopt_info['minimal_bid']} руб. / {adopt_info['minimal_bid'] / 100} $\n"
        f"📝 Актуальная ставка: {adopt_info['current_bid']} руб от пользователя |{adopt_info['last_bidder_username']}|\n\n"
    )

    total_pages = len(adoptions)

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("← Назад", callback_data='adopt_view_back')
    btn_next = types.InlineKeyboardButton("Вперед →", callback_data='adopt_view_forward')
    btn_bet_adopt = types.InlineKeyboardButton("Пост. ставку", callback_data=f"adopt_view_btn_bet_{adopt_info['id']}")

    if total_pages == 2 and current_index != 2 or current_index != 0 and current_index == total_pages - 1:
        markup.add(btn_back)
    if current_index < total_pages - 1:
        if current_index > 0:
            markup.row(btn_back, btn_next)
        else:
            markup.add(btn_next)

    markup.add(btn_bet_adopt)
    if user_id == admin_id:
        btn_edit = types.InlineKeyboardButton("✏️ Редактировать", callback_data=f'adopt_page_edit_{adopt_info["id"]}')
        btn_del = types.InlineKeyboardButton("✏️ Удалить", callback_data=f'adopt_page_del_{adopt_info["id"]}')
        markup.add(btn_edit,btn_del)

    try:
        if edit:
            media = types.InputMediaPhoto(adopt_info['image_url'], caption=text)
            bot.edit_message_media(
                media=media,
                chat_id=user_id,
                message_id=message.message_id,
                reply_markup=markup
            )
        else:
            bot.send_photo(
                chat_id=user_id,
                photo=adopt_info['image_url'],
                caption=text,
                reply_markup=markup
            )
    except Exception as e:
        print(f"Ошибка: {e}")

@bot.callback_query_handler(func = lambda call:call.data.startswith("adopt_page_del_"))
def del_adopt_page(call):
    user_id = call.message.chat.id

    if confirming_admin(user_id):
        return



    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)

    admin_adopt_page_del_yes = types.InlineKeyboardButton("Подтвердить", callback_data='admin_adopt_page_del_yes')
    admin_adopt_page_del_no = types.InlineKeyboardButton("Нет", callback_data='admin_adopt_page_del_no')

    inline_keyboard.add(admin_adopt_page_del_yes, admin_adopt_page_del_no)


    bot.send_message(admin_id, f"Подтвердить удаление?", reply_markup=inline_keyboard)


@bot.callback_query_handler(func= lambda call:call.data.startswith("admin_adopt_page_del_"))
def abs_del_adopt_page(call):

    user_id = call.message.chat.id
    if confirming_admin(user_id):
        bot.answer_callback_query(call.id, "🚫 Доступ запрещен: вы не администратор.")
        return
    state = get_user_state(user_id)
    current_index = state.get('current_adopt_index', 0)
    adopt_page = get_existing_list_adopts()[current_index]

    print(adopt_page["id"])
    if call.data == "admin_adopt_page_del_yes":
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            check_sql = "SELECT id FROM art_lots_links WHERE id = %s;"
            cursor.execute(check_sql, (adopt_page['id'],))
            if not cursor.fetchone():
                bot.send_message(user_id, "❌ Адопт не найден.")
                return
            sql = "DELETE FROM art_lots_links WHERE id = %s;"
            cursor.execute(sql, (adopt_page['id'],))
            conn.commit()
            bot.send_message(user_id, f'Адопт {adopt_page["id"]} был удален.')
            show_adopt_page(call.message, user_id)

        except Exception as e:
            print("Ошибка при удалении адопта:", e)
            bot.send_message(user_id, f"❌ Произошла ошибка при удалении адопта: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    else:
        show_adopt_page(call.message, user_id)

# редактирвоание данных поста адопта
@bot.callback_query_handler(func = lambda call:call.data.startswith("adopt_page_edit_"))
def edit_adopt_page(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id):
        return

    bot.send_message(user_id, "Введите начальную стоимость адопта!")
    bot.register_next_step_handler(call.message, edit_data_adopt_page)

def edit_data_adopt_page(message):
    user_id = message.chat.id
    try:
        price = float(message.text)
        admin_new_price[user_id] = price

        inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
        admin_adopt_page_edit_yes = types.InlineKeyboardButton("Подтвердить",
                                                                callback_data='admin_adopt_page_edit_yes')
        admin_adopt_page_edit_no = types.InlineKeyboardButton("Нет",
                                                                callback_data='admin_adopt_page_edit_no')
        inline_keyboard.add(admin_adopt_page_edit_yes, admin_adopt_page_edit_no)

        bot.send_message(user_id, "Подтвердить?", reply_markup=inline_keyboard)

    except ValueError:
        bot.send_message(user_id, "❌ Неверный формат суммы. Введите число.")
    except Exception as e:
        bot.send_message(user_id, f"❌ Произошла ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_adopt_page_edit_"))
def abs_edit_adopt_page(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id):
        bot.answer_callback_query(call.id, "🚫 Доступ запрещен: вы не администратор.")
        return

    state = get_user_state(user_id)
    current_index = state.get('current_adopt_index', 0)
    adopt_page = get_existing_list_adopts()[current_index]
    price = admin_new_price[user_id]
    print(adopt_page)
    if call.data == "admin_adopt_page_edit_yes":
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            sql = "UPDATE art_lots_links SET price = %s WHERE id = %s"
            cursor.execute(sql, (price, adopt_page['id']))
            conn.commit()

            bot.send_message(user_id, f'У адопта {adopt_page["id"]} была изменена нач. на {price}')
            show_adopt_page(call.message, user_id)

        except Exception as e:
            print("Ошибка при изменении адопта:", e)
            bot.send_message(user_id, f"❌ Произошла ошибка при изменении адопта: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    else:
        show_adopt_page(call.message, user_id)



@bot.callback_query_handler(func = lambda call:call.data.startswith("adopt_view_btn_bet_"))
def betting_adopt(call):
    user_id = call.message.chat.id
    row_id = int((call.data.split("_"))[-1])
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM art_lots_links WHERE id = %s;", (row_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if len(result) == 0:
        bot.send_message(user_id,"📭 Список адоптов пуст")
        return
    if result == None:
        bot.send_message(user_id, "Данного адопта не существует или скрыт!")
        return

    bot.send_message(user_id, f"Пожалуйста введите сумму не меньше, чем минимальная ставка")
    bot.register_next_step_handler(call.message, get_betting_price)

def get_betting_price(message):
    user_id = message.chat.id
    state = get_user_state(user_id)
    if message.text in ["Отмена","Адопты","Сделать заказ"]:
        bot.send_message(user_id, "Ваше действие было отклонено!")
        return
    current_index = state.get('current_adopt_index', 0)
    adopt_page = get_existing_list_adopts()[current_index]
    adopt_id = adopt_page["id"]
    price = adopt_page["price"]
    current_price= adopt_page["current_bid"]

    try :
        current_bid = float(message.text)
        minimal_bid  = adopt_page["minimal_bid"]
        last_bidder_id = user_id
        last_bidder_username = get_username_by_id(user_id)

        # print(adopt_page)
        # print(current_bid, current_price, minimal_bid)
        if  current_bid == price and current_price == 0.00 or current_bid >= minimal_bid + current_price :

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            sql = "UPDATE art_lots_links SET current_bid = %s, last_bidder_id = %s, last_bidder_username = %s WHERE id = %s"
            cursor.execute(sql, (current_bid, last_bidder_id, last_bidder_username , adopt_id))
            conn.commit()
            cursor.close()
            conn.close()

            bot.send_message(user_id, "Ваша ставка поставлена!")
            if user_id != admin_id:
                bot.send_message(user_id, "Ожидайте связи автора с вами!")
            show_adopt_page(message, user_id)
        else:
            bot.send_message(user_id,"Ваша ставка либо меньше актуальной, либо не превосходит актуальную на минимальную ставку!")
            show_adopt_page(message, user_id)
    except ValueError:
        bot.send_message(user_id, "Ошибка! Введите корректное число для цены!")
        bot.register_next_step_handler(message,get_betting_price)

@bot.callback_query_handler(func=lambda call: call.data in ["adopt_view_back", "adopt_view_forward"])
def change_adopt_page(call):
    user_id = call.message.chat.id
    state = get_user_state(user_id)
    current_index = state.get('current_adopt_index', 0)

    if call.data == "adopt_view_back":
        current_index -= 1
    elif call.data == "adopt_view_forward":
        current_index += 1

    state['current_adopt_index'] = current_index
    show_adopt_page(call.message, user_id, edit=True)

# Публикация адопта
@bot.message_handler(func = lambda message:message.text == "Выложить адопта")
def publicate_adopt(message):
    global admin_data_publicate
    admin_data_publicate = {}
    if confirming_admin(message.chat.id):
        bot.answer_callback_query(message.chat.id, text="🚫 Доступ запрещен")
        return

    chat_id = message.chat.id
    bot.send_message(chat_id, "Пожалуйста. отправьте изображение адопта! (для отмены напишите 'Отмена')")
    bot.register_next_step_handler(message, get_adopt_image)
# 1 - сохранение id изобображения
def get_adopt_image(message):
    chat_id = message.chat.id
    if message.text == "Отмена":
        bot.send_message(chat_id, "Публикация прервана!")
        return

    if message.photo:
        file_id = message.photo[-1].file_id
        admin_data_publicate['file_id'] = file_id

        bot.send_message(chat_id, "Введите название адопта/адоптов!")
        bot.register_next_step_handler(message,get_adopt_title)


        # bot.send_photo(chat_id,file_id, caption="ваше фото")
        # file_info = bot.get_file(file_id)
        # file_url = f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"
        # file_name = f"piknave_{file_id}.jpg"
        # file_path = os.path.join(IMAGE_DIR, file_name)
        #
        # response = requests.get(file_url)
        # with open(file_path, "wb") as file:
        #     file.write(response.content)
        # admin_data_publicate['image_path'] = file_path
    else:
        bot.send_message(chat_id, "Ошибка! Пожалуйста, убедитесь, что отправлено сжатое изображение, а не файл!")
        bot.register_next_step_handler(message,get_adopt_image)
# 2 - сохранение названия
def get_adopt_title(message):
    chat_id = message.chat.id
    admin_data_publicate["title"] = message.text
    bot.send_message(chat_id, "Введите описание работы! Цену указывать в конце описания")
    bot.register_next_step_handler(message,get_adopt_description)
# 3 - сохранение описания
def get_adopt_description(message):
    chat_id = message.chat.id
    admin_data_publicate["description"] = message.text
    bot.send_message(chat_id, "Введите начальную цену и минимальную ставку (default = 100 руб.\n"
                              "Введите через пробел\n")
    bot.register_next_step_handler(message,get_adopt_price)
# 4 - сохранение цены
def get_adopt_price(message):
    chat_id = message.chat.id
    try:
        text_message = (message.text).split()
        price = float(text_message[0])
        min_bid = 100
        if text_message == 2:
            min_bid = float(text_message[1])
        admin_data_publicate["price"] = price
        admin_data_publicate["minimal_bid"] = min_bid

        inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
        button_order_requests = types.InlineKeyboardButton("Подтвердить",callback_data='admin_confirming_adopt_yes')
        button_order_confirmed = types.InlineKeyboardButton("Изменить", callback_data='admin_confirming_adopt_no')
        inline_keyboard.add(button_order_confirmed,button_order_requests)

        text_full_adopt_lot = (f"Название - {admin_data_publicate['title']}\n"
                               f"Описание:\n"
                               f"{admin_data_publicate['description']}\n"
                               f"Цена: {admin_data_publicate['price']} руб. / {admin_data_publicate['price']/100} $\n"
                               f"Минимальная ставка {min_bid} руб./ {min_bid / 100} $\n\n"
                               f"Подтвердить?")
        msg = bot.send_photo(chat_id, admin_data_publicate['file_id'], caption=text_full_adopt_lot,reply_markup=inline_keyboard)
        delete_message_bot[chat_id] = msg.message_id
    except ValueError:
        bot.send_message(chat_id, "Ошибка! Введите корректное число для цены!")
        bot.register_next_step_handler(message,get_adopt_price)
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_confirming_adopt_"))
def pre_final_adopt_publishing(call):
    global admin_data_publicate
    chat_id = call.message.chat.id
    if chat_id != admin_id:
        bot.answer_callback_query(chat_id, text="🚫 Доступ запрещен")
        return

    if call.data == "admin_confirming_adopt_yes":
        image_id = admin_data_publicate['file_id']
        title = admin_data_publicate['title']
        description = admin_data_publicate['description']
        price = admin_data_publicate['price']
        min_bid = admin_data_publicate['minimal_bid']
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM art_lots_links WHERE image_url = %s", (image_id,))
            existing_adopt_image = cursor.fetchall()
            if existing_adopt_image:
                if chat_id in delete_message_bot:
                    bot.delete_message(chat_id, delete_message_bot[chat_id])
                    del delete_message_bot[chat_id]
                else:
                    bot.send_message(chat_id, "Нет сообщений для удаления!")

                bot.send_message(chat_id, "Этот адопт уже существует! Пожалуйста, проверьте существующие!")
                admin_data_publicate = {}
                return
            else:
                save_lot_to_db(chat_id, title, description, image_id, price, min_bid)
                bot.send_message(chat_id, "Новый адопт успешно добавлен!")
            cursor.close()
            conn.close()
        except Exception as e:
            print("Ошибка!", e)
    else:
        if chat_id in delete_message_bot:
            bot.delete_message(chat_id, delete_message_bot[chat_id])
            del delete_message_bot[chat_id]
        else:
            bot.send_message(chat_id, "Нет сообщений для удаления!")

        bot.send_message(chat_id, "Пожалуйста. отправьте изображение адопта!")
        bot.register_next_step_handler(call.message, get_adopt_image)


@bot.message_handler(func = lambda message:message.text == "Заказы")
def orders_for_admin(message):
    if confirming_admin(message.chat.id):
        bot.answer_callback_query(message.chat.id, text="🚫 Доступ запрещен")
        return
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)

    button_order_requests = types.InlineKeyboardButton("Запросы",callback_data='admin_order_requests')
    button_order_confirmed = types.InlineKeyboardButton("Подтвержденные", callback_data='admin_order_confirmed')

    inline_keyboard.add(button_order_confirmed,button_order_requests)

    request_order = len(get_order_lists("ожидает"))
    confirmed_order = len(get_order_lists("выполняется"))

    bot.send_message(admin_id,f"Ваши заказы:\nОжидают подтверждения - {request_order}"
                                                f"\nПодтверждено - {confirmed_order}",reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["admin_order_requests", "admin_order_confirmed"])
def handle_order_lists(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id):
        bot.answer_callback_query(user_id, text="🚫 Доступ запрещен")
        return

    state = get_admin_state(user_id)
    list_type = 'ожидает' if call.data == 'admin_order_requests' else 'выполняется'
    state['current_list'] = list_type
    state['pages'][list_type] = 0

    show_order_page(call.message, user_id, list_type)


@bot.callback_query_handler(func=lambda call: call.data in ["requestOrder_back", "requestOrder_forward"])
def change_order_page(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id):
        bot.answer_callback_query(user_id, text="🚫 Доступ запрещен")
        return

    state = get_admin_state(user_id)
    current_list = state['current_list']
    current_page = state['pages'][current_list]
    orders = get_order_lists(current_list)
    total_pages = max(1, (len(orders) + page_size - 1) // page_size)

    if call.data == "requestOrder_back":
        if current_page > 0:
            state['pages'][current_list] -= 1
    elif call.data == "requestOrder_forward":
        if current_page < total_pages - 1:
            state['pages'][current_list] += 1

    try:
        show_order_page(call.message, user_id, current_list)
    except Exception as e:
        bot.answer_callback_query(call.id, text=f"Ошибка: {e}")

def get_admin_state(user_id):
    if user_id not in admin_state:
        admin_state[user_id] = {
            'current_list': 'ожидает',
            'pages': {'ожидает': 0, 'выполняется': 0}
        }
    return admin_state[user_id]


def show_order_page(message, user_id, list_type):
    state = get_admin_state(user_id)
    current_page = state['pages'][list_type]
    orders = get_order_lists(list_type)
    total_orders = len(orders)
    total_pages = max(1, (total_orders + page_size - 1) // page_size)

    start_idx = current_page * page_size
    end_idx = start_idx + page_size
    orders_to_show = orders[start_idx:end_idx]

    # Формируем текст сообщения
    if not orders_to_show:
        text = "📭 Список заказов пуст."
        markup = types.InlineKeyboardMarkup()
    else:
        order = orders_to_show[0]
        status_emoji = "⏳" if list_type == 'ожидает' else '✅'
        text = (
            f"📌 Заказ №{order['id']}\n"
            f"👤 Пользователь: @{order['username']} (ID: {order['user_id']})\n"
            f"📝 Описание: {order['order_details']}\n"
            f"{status_emoji} Статус: {list_type}\n"
            f"📅 Дата: {order['created_at']}"
        )
        # Создаем клавиатуру
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("← Назад", callback_data='requestOrder_back')
        btn_next = types.InlineKeyboardButton("Вперед →", callback_data='requestOrder_forward')
        if list_type == 'ожидает':
            btn_confirm = types.InlineKeyboardButton(   "✅ Подтвердить",    callback_data='requestOrder_confirm')
            btn_reject = types.InlineKeyboardButton(    "❌ Отклонить",      callback_data='requestOrder_rejection')
        else:
            btn_confirm = types.InlineKeyboardButton("✅ Завершить", callback_data='confirmedOrder_confirm')
            btn_reject = types.InlineKeyboardButton("❌ Отклонить", callback_data='confirmedOrder_rejection')

        # Управление кнопками навигации
        if  total_pages ==2 and current_page != 2 or current_page!=0 and current_page == total_pages-1:
            print(total_pages, current_page)
            markup.add(btn_back)
        if current_page < total_pages - 1:
            if current_page > 0:
                markup.row(btn_back, btn_next)
            else:
                markup.add(btn_next)

        markup.row(btn_confirm, btn_reject)

    try:
        if hasattr(message, 'message_id'):  # Проверяем, можно ли редактировать
            bot.edit_message_text(
                text,
                chat_id=user_id,
                message_id=message.message_id,
                reply_markup=markup
            )
        else:
            bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=markup
            )
    except Exception as e:
        bot.send_message(user_id, f"Ошибка обновления: {e}")

def get_order_lists(status):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, user_id, username, order_details, status, created_at FROM orders ORDER BY created_at ASC")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    if not orders:
        print("список  пусть")
        return []

    if status == "ожидает":
        return [o for o in orders if o["status"] == "ожидает"]
    elif status == "выполняется":
        return [o for o in orders if o["status"] == "выполняется"]

# отказ/Завершение заказов
@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmedOrder'))
def update_order_status(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id):
        bot.answer_callback_query(user_id, text="🚫 Доступ запрещен")
        return
    list_request_confirm = get_order_lists("выполняется")
    if len(list_request_confirm) >0:
        user_data_confirming = list_request_confirm[admin_state[user_id]['pages']['выполняется']]
        order_id = user_data_confirming["id"]
    print(user_data_confirming)

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
        result = cursor.fetchone()

        if "confirm" in call.data:
            print("Заказ завершен")
            if result:
                user_id = result[0]
                bot.send_message(user_id, f"🔄 Ваш заказ #{order_id} Завершен! Пожалуйста, обратитесь к художнику (@piknave) за оригиналми изображений!")

            bot.send_message(call.message.chat.id, f"✅ Статус заказа #{order_id} обновлён: завершен")

        elif "rejection" in call.data:
            print("Отказ заказа")

            if result:
                user_id = result[0]
                bot.send_message(user_id, f"❌ Ваш заказ #{order_id} был отменён.")

            bot.send_message(call.message.chat.id, f"🚫 Заказ #{order_id} отменён.")
            return
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка обновления заказа: {e}")


# отказ/принятие запроса на заказ
@bot.callback_query_handler(func=lambda call: call.data.startswith('requestOrder'))
def update_order_status(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id):
        bot.answer_callback_query(user_id, text="🚫 Доступ запрещен")
        return
    list_request_confirm = get_order_lists("ожидает")
    if len(list_request_confirm):
        user_data_confirming = list_request_confirm[admin_state[user_id]['pages']['ожидает']]
        order_id = user_data_confirming["id"]
    print(user_data_confirming)

    try:
        if "confirm" in call.data:
            print("Принят заказ")
            new_status = "выполняется"

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
            conn.commit()
            cursor.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                bot.send_message(user_id, f"🔄 Ваш заказ #{order_id} теперь выполняется!")

            bot.send_message(call.message.chat.id, f"✅ Статус заказа #{order_id} обновлён: {new_status}")

            cursor.close()
            conn.close()

        elif "rejection" in call.data:
            # Получаем user_id заказчика
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM orders WHERE id = %s", (order_id))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                user_id = result[0]
                bot.send_message(user_id, f"❌ Ваш заказ #{order_id} был отменён.")

            bot.send_message(call.message.chat.id, f"🚫 Заказ #{order_id} отменён.")
            return
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка обновления заказа: {e}")

# Create-order
@bot.message_handler(func = lambda message:message.text == "Сделать заказ")
def place_an_order(message):
    user_id = message.chat.id
    if confirming_admin(user_id) == False:
        return



    # Проверка активных заказов
    active_orders = get_order_lists("ожидает") + get_order_lists("выполняется")
    if any(order["user_id"] == user_id and order["status"] == "ожидает" for order in active_orders):
        order = [order for order in active_orders if order["user_id"] == user_id][0]


        inline_kb = types.InlineKeyboardMarkup(row_width=2)
        button_yes  = types.InlineKeyboardButton("Подтвердить?", callback_data='order_cancellation_yes')
        button_no   = types.InlineKeyboardButton("Отмена", callback_data='order_cancellation_no')
        inline_kb.add(button_yes, button_no)

        msg = bot.send_message(user_id,
                         f"❌ Превышен лимит в один заказ на человека.\n"
                         f"Пожалуйста, дождитесь выполнения текущего заказа.\n"
                         f"Заказ |id = {order['id']}| от {order['username']}\n"
                         f"Описание: |{order['order_details']}|\n"
                         f"Дата подачи: |{order['created_at']}|\n"
                         f"Отменить заказ?",
                         parse_mode="HTML",
                         reply_markup= inline_kb)
        delete_message_bot[user_id] = msg.message_id
        return

    inline_keyboard = types.InlineKeyboardMarkup(row_width=3)

    button_commission = types.InlineKeyboardButton("Commission",callback_data='commission')
    button_fullArt = types.InlineKeyboardButton("Art with background",callback_data='fullArt')
    button_custom = types.InlineKeyboardButton("Custom order", callback_data='custom_order')

    inline_keyboard.add(button_commission, button_fullArt, button_custom)
    msg = bot.send_message(user_id, "Выберите тип рисунка:", reply_markup=inline_keyboard)
    delete_message_bot[user_id] = msg.message_id

# Commission
@bot.callback_query_handler(func=lambda call: call.data == "commission")
def commisssion_detail(call):
    user_id = call.message.chat.id
    if confirming_admin(call.message.chat.id) == False:
        return
    # Удалить предыдущее сообщение
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]

    inline_keyboard = types.InlineKeyboardMarkup(row_width=4)
    button_comm_FullBody = types.InlineKeyboardButton("В полный рост", callback_data='commission_FullBody')
    button_comm_HalfBody = types.InlineKeyboardButton("До пояса", callback_data='commission_HalfBody')
    button_comm_toShoulders = types.InlineKeyboardButton("До плеч", callback_data='commission_toShoulders')
    button_comm_chibi = types.InlineKeyboardButton("Чиби", callback_data='commission_chibi')

    inline_keyboard.add(button_comm_FullBody, button_comm_HalfBody, button_comm_toShoulders,button_comm_chibi)
    msg = bot.send_message(call.message.chat.id,
                                         "Вы выбрали Commission. Пожалуйста, выберите категорию:", reply_markup=inline_keyboard)
    delete_message_bot[user_id] = msg.message_id



@bot.callback_query_handler(func=lambda call: call.data.startswith("commission_"))
def commission_order(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id) == False:
        return
    # Удаление предыдущее сообщение
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]

    type_commission = None
    if call.data == "commission_FullBody":
        type_commission = "Полный рост"
    elif call.data == "commission_HalfBody":
        type_commission = "До пояса"
    elif call.data == "commission_toShoulders":
        type_commission = "До плеч"
    elif call.data == "commission_chibi":
        type_commission = "Чиби"
    user_orders[user_id] = f"{type_commission}\n"
    order_description = bot.send_message(call.message.chat.id,
                                         f"Вы выбрали Commission ***{type_commission}***. Пожалуйста, опишите подробности заказа:")
    bot.register_next_step_handler(order_description, get_custom_order_datails)


# Рисунок с фоном
@bot.callback_query_handler(func=lambda call: call.data == "fullArt")
def fullArt_detail(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id) == False:
        return
    # Удалить предыдущее сообщение
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]

    inline_keyboard = types.InlineKeyboardMarkup(row_width=4)
    button_comm_FullBody = types.InlineKeyboardButton("В полный рост", callback_data='fullArt_FullBody')
    button_comm_HalfBody = types.InlineKeyboardButton("До пояса", callback_data='fullArt_HalfBody')
    button_comm_toShoulders = types.InlineKeyboardButton("До плеч", callback_data='fullArt_toShoulders')
    button_comm_chibi = types.InlineKeyboardButton("Чиби", callback_data='fullArt_chibi')

    inline_keyboard.add(button_comm_FullBody, button_comm_HalfBody, button_comm_toShoulders, button_comm_chibi)
    msg = bot.send_message(call.message.chat.id,
                           "Вы выбрали Рисунок вместе с фоном. Пожалуйста, выберите категорию:", reply_markup=inline_keyboard)
    delete_message_bot[user_id] = msg.message_id


@bot.callback_query_handler(func=lambda call: call.data.startswith("fullArt_"))
def fullArt_order(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id) == False:
        return
    # Удаление предыдущее сообщение
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]

    type_commission = None
    if call.data == "fullArt_FullBody":
        type_commission = "Полный рост"
    elif call.data == "fullArt_HalfBody":
        type_commission = "До пояса"
    elif call.data == "fullArt_toShoulders":
        type_commission = "До плеч"
    elif call.data == "fullArt_chibi":
        type_commission = "Чиби"
    user_orders[user_id] = f"{type_commission}"
    order_description = bot.send_message(call.message.chat.id,
                                         f"Вы выбрали Рисунок вместе с фоном ***{type_commission}***. Пожалуйста, опишите подробности заказа:")
    bot.register_next_step_handler(order_description, get_custom_order_datails)


@bot.callback_query_handler(func=lambda call: call.data == "custom_order")
def custom_order_detail(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id) == False:
        return
    # Удаление предыдущее сообщение
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]

    order_description = bot.send_message(call.message.chat.id,
                                         "Вы выбрали Custom order. Пожалуйста, опишите подробности индивидуального заказа:")
    bot.register_next_step_handler(order_description, get_custom_order_datails)

def get_custom_order_datails(message):
    user_id = message.chat.id
    # Удаление предыдущее сообщение
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]
    order_details = message.text
    back_user_orders = user_orders[user_id]
    user_orders[user_id] = f"{back_user_orders}\n {order_details}"
    buttons_yes_no = types.InlineKeyboardMarkup(row_width=2)
    buttons_yes_no.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data='order_confirmation_yes'),
        types.InlineKeyboardButton("❌ Изменить", callback_data='order_confirmation_no')
    )

    msg = bot.send_message(user_id, f"Спасибо! Ваше описание заказа:\n\"{order_details}\".\nПодтвердить?", reply_markup=buttons_yes_no)
    delete_message_bot[user_id] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("order_cancellation_"))
def user_order_cancellation(call):
    user_id = call.message.chat.id
    # Удаление предыдущего сообщения
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]

    if call.data == "order_cancellation_yes":
        try:

            active_orders = get_order_lists("ожидает")
            order = [order for order in active_orders if order["user_id"] == user_id][0]

            print(order['id'])
            if order:
                order_id = order["id"]
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                sql = "DELETE FROM orders WHERE id = %s"
                cursor.execute(sql, (order_id,))
                conn.commit()
                cursor.close()
                conn.close()
                bot.send_message(user_id, "✅ Ваш заказ успешно отменен!")
            else:
                bot.send_message(user_id, "❌ Активный заказ не найден.")
        except Exception as e:
            print(f"Ошибка при отмене заказа: {e}")
            bot.send_message(user_id, "❌ Произошла ошибка при отмене заказа. Пожалуйста, попробуйте позже.")
    else:
        bot.send_message(user_id, "Ваш заказ остается в ожидании подтверждения! Дождитесь ответа!")


@bot.callback_query_handler(func=lambda call: call.data.startswith('order_confirmation_'))
def order_confirmtion_handler(call):
    user_id = call.message.chat.id
    if confirming_admin(user_id) == False:
        return
    # Удаление предыдущего сообщения
    if user_id in delete_message_bot:
        bot.delete_message(user_id, delete_message_bot[user_id])
        del delete_message_bot[user_id]

    if call.data == "order_confirmation_yes":
        username = call.from_user.username or "Без никнейма"
        order_details = user_orders[user_id]

        if order_details:
            save_order_to_db(user_id, username, order_details)
            bot.send_message(user_id, "✅ Ваш заказ принят. Ожидайте подтверждения на выполнение.")

        else:
            bot.send_message(user_id, "Ошибка: Нет описания. Пожалуйста, попробуйте снова.")

    elif call.data == "order_confirmation_no":
        bot.send_message(user_id, "Пожалуйста, введите новое описание заказа:")
        bot.register_next_step_handler(call.message, get_custom_order_datails)




def save_order_to_db(user_id, username, order_details):
    global admin_data_publicate
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO orders (user_id, username, order_details, created_at) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (user_id, username, order_details, created_time))
        conn.commit()
        order_id = cursor.lastrowid
        cursor.close()
        conn.close()
        admin_data_publicate = {}
        return  order_id, created_time
    except Exception as error:
        print("ошибка в записи бд заказа",error)
        return None

# Сохранение в ДБ данные адопта
def save_lot_to_db(user_id, title, description, image_url, price, minimal_bid):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        sql = "INSERT INTO art_lots_links (title, description, image_url, price, minimal_bid) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (title, description, image_url, price, minimal_bid))
        conn.commit()
        order_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return  order_id
    except mysql.connector.Error as error:
        print(f"Ошибка при записи в БД: {error}")
        return None

# Обновленеи статуса адопта (спрвка для статуса: активен/продан/скрыт)
def update_lot_status(adopt_id, new_status):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        sql = "UPDATE art_lots_links SET status = %s WHERE id = %s"
        cursor.execute(sql, (new_status, adopt_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as error:
        print(f"Ошибка! При изменении статуса - {error}")
        return False

def get_username_by_id(user_id):
    try:
        chat = bot.get_chat(user_id)
        username = chat.username
        return username
    except Exception as e:
        print(f"Ошибка : {e}")
        return "Аноним"

# @app.route("/set_webhook", methods=["GET"])
# def set_webhook():
#     webhook_url = f"https://hiriimosa.pythonanywhere.com/{token}"  # URL PythonAnywhere
#     bot.remove_webhook()
#     bot.set_webhook(url=webhook_url)
#     return "Webhook установлен!", 200


if __name__ == '__main__':
    print("Starting bot...")
    app.run(host="0.0.0.0", port=5000)



