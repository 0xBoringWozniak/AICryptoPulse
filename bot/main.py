from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.creds import TELEGRAM_BOT_TOKEN
from bot.handlers import (
    REGISTERING_PROMPT,
    SET_NEW_PROMPT,
    predict_message,
    register_prompt,
    schedule_daily_job,
    set_prompt_command,
    start,
    update_prompt,
)


def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("set_prompt", set_prompt_command),
        ],
        states={
            REGISTERING_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_prompt)
            ],
            SET_NEW_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_prompt),
            ],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, predict_message)
    )
    schedule_daily_job(application)
    application.run_polling()


if __name__ == "__main__":
    main()
