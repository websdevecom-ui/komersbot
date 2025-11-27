import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройки бота
BOT_TOKEN = "7970794244:AAEuzr03ochWMuXExjViAI-3EW8-uP4Ech8"
ADMIN_SECRET_CODE = "komadm-192L-JHAs-O2k9-Klsq"

# Хранилище данных (в реальном проекте лучше использовать базу данных)
admin_users = set()  # Множество ID администраторов
all_users = set()    # Множество всех пользователей, которые начали диалог с ботом

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    all_users.add(user_id)
    
    welcome_text = (
        "👋 Добро пожаловать!\n\n"
        "Это бот для рассылки сообщений. "
        "Обычные пользователи получают сообщения от администратора.\n\n"
        "Для получения прав администратора используйте секретную команду."
    )
    
    await update.message.reply_text(welcome_text)

async def handle_secret_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик секретного кода для получения прав администратора"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    if message_text == ADMIN_SECRET_CODE:
        admin_users.add(user_id)
        await update.message.reply_text(
            "✅ Поздравляем! Вы получили права администратора.\n\n"
            "Теперь вы можете отправлять сообщения всем пользователям бота. "
            "Просто напишите любое сообщение, и оно будет разослано всем."
        )
        logger.info(f"User {user_id} became admin")
    else:
        await update.message.reply_text("❌ Неверная команда")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений от администратора для рассылки"""
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in admin_users:
        await update.message.reply_text(
            "❌ У вас нет прав для отправки сообщений всем пользователям.\n"
            "Для получения прав администратора используйте секретную команду."
        )
        return
    
    message_text = update.message.text
    message_id = update.message.message_id
    
    # Отправляем сообщение всем пользователям
    successful_sends = 0
    failed_sends = 0
    
    for user in all_users.copy():  # Используем копию множества на случай изменений
        try:
            # Пересылаем оригинальное сообщение
            await context.bot.forward_message(
                chat_id=user,
                from_chat_id=update.effective_chat.id,
                message_id=message_id
            )
            successful_sends += 1
        except Exception as e:
            logger.error(f"Failed to send message to user {user}: {e}")
            failed_sends += 1
            # Удаляем пользователя, который заблокировал бота
            all_users.discard(user)
    
    # Отправляем отчет администратору
    report_text = (
        f"📊 Отчет по рассылке:\n"
        f"✅ Успешно отправлено: {successful_sends}\n"
        f"❌ Не удалось отправить: {failed_sends}\n"
        f"👥 Всего пользователей: {len(all_users)}"
    )
    
    await update.message.reply_text(report_text)
    logger.info(f"Admin {user_id} sent broadcast to {successful_sends} users")

async def handle_regular_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных сообщений от пользователей"""
    user_id = update.effective_user.id
    
    # Добавляем пользователя в список, если он еще не там
    if user_id not in all_users:
        all_users.add(user_id)
    
    # Если пользователь не админ, просто подтверждаем получение сообщения
    if user_id not in admin_users:
        await update.message.reply_text(
            "✅ Ваше сообщение получено. "
            "Администратор уведомлен о вашем обращении."
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения статистики (только для администраторов)"""
    user_id = update.effective_user.id
    
    if user_id not in admin_users:
        await update.message.reply_text("❌ У вас нет прав для просмотра статистики.")
        return
    
    stats_text = (
        f"📊 Статистика бота:\n"
        f"👥 Всего пользователей: {len(all_users)}\n"
        f"👑 Администраторов: {len(admin_users)}\n"
        f"🆔 Ваш ID: {user_id}"
    )
    
    await update.message.reply_text(stats_text)

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    
    # Обработчик для секретного кода
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(f'^{ADMIN_SECRET_CODE}$'), 
        handle_secret_code
    ))
    
    # Обработчик для сообщений администратора
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_admin_message
    ))
    
    # Обработчик для обычных сообщений (на случай, если нужно дополнительное поведение)
    application.add_handler(MessageHandler(
        filters.ALL, 
        handle_regular_message
    ))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()