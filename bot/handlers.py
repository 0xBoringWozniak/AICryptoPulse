import logging
import requests
from requests.exceptions import RequestException
from telegram import Update
from telegram.ext import CallbackContext, ContextTypes, ConversationHandler

from bot.api import get_all_users
from bot.creds import FASTAPI_BASE_URL
from bot.texts import REGULAR_UPDATE_PROMPT, START_TEXT

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

REGISTERING_PROMPT = 1
SET_NEW_PROMPT = 2


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /start command:
    1. Get the Telegram username from the user (must not be None).
    2. If username is valid, ask the user for their system prompt.
    """
    telegram_username = update.effective_user.username
    if not telegram_username:
        # If user has no Telegram username set
        await update.message.reply_text(
            "You do not have a Telegram username set in your profile, so registration is not possible."
        )
        return ConversationHandler.END
    context.user_data["username"] = telegram_username
    await update.message.reply_text(START_TEXT)

    return REGISTERING_PROMPT


async def register_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Saves the system prompt to FastAPI (/create_user) using the Telegram username.
    """
    system_prompt = update.message.text.strip()
    username = context.user_data["username"]
    chat_id = update.message.chat_id

    payload = {
        "username": username,
        "system_prompt": system_prompt,
        "chat_id": str(chat_id)
    }

    url = f"{FASTAPI_BASE_URL}/create_user"
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200:
            await update.message.reply_text(
                f"I registered your preferences in '{system_prompt}'. You can change it with /set_prompt."
            )
        else:
            # Some error returned by the API
            error_msg = data.get("data", {}).get("message", "Unknown error")
            await update.message.reply_text(f"Could not create user: {error_msg}")
    except RequestException as e:
        logger.error("Error calling /create_user: %s", e)
        await update.message.reply_text(f"Error calling /create_user: {str(e)}")

    return ConversationHandler.END


async def set_prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /set_prompt command:
    Ask the user for their new system prompt.
    """
    telegram_username = update.effective_user.username
    if not telegram_username:
        await update.message.reply_text(
            "You do not have a Telegram username set in your profile. This action is not possible."
        )
        return ConversationHandler.END

    context.user_data["username"] = telegram_username
    await update.message.reply_text("Please enter your new preferences.")

    return SET_NEW_PROMPT


async def update_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save the new prompt for an existing user using the /set_prompt API.
    """
    new_prompt = update.message.text.strip()
    username = context.user_data.get("username")

    logger.info("Updating prompt for user '%s' to '%s'", username, new_prompt)
    payload = {
        "username": username,
        "new_prompt": new_prompt,
    }

    url = f"{FASTAPI_BASE_URL}/set_prompt"
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        if response.status_code == 200:
            await update.message.reply_text(
                f"System prompt was updated successfully for user '{username}'. New prompt: '{new_prompt}'"
            )
        else:
            error_msg = data.get("data", {}).get("message", "Unknown error")
            await update.message.reply_text(f"Could not update prompt: {error_msg}")
    except RequestException as e:
        logger.error("Error calling /set_prompt: %s", e)
        await update.message.reply_text(f"Error calling /set_prompt: {str(e)}")

    return ConversationHandler.END


async def predict_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Whenever a user (who is registered) sends a non-command message,
    call /predict on the FastAPI side and return the response.
    """
    text = update.message.text
    username = update.effective_user.username
    payload = {
        "username": username,
        "prompt": text,
        "daily_report": False,
    }
    url = f"{FASTAPI_BASE_URL}/predict"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if resp.status_code == 200:
            predicted_text = data.get("data", {}).get("response", "")
            await update.message.reply_text(predicted_text)
        else:
            error_msg = data.get("data", {}).get("message", "Unknown error")
            await update.message.reply_text(f"Predict error: {error_msg}")
    except RequestException as e:
        logger.error("Error calling /predict: %s", e)
        await update.message.reply_text(f"Error calling /predict: {str(e)}")


async def daily_predict_job(_context: CallbackContext):
    """
    This job is run once a day. It calls /predict for each registered user
    and sends the result back to them.
    """
    all_users = get_all_users()
    logger.info("Daily job: %d users found.", len(all_users))
    for user_info in all_users:
        chat_id = user_info["chat_id"]
        stored_prompt = user_info["system_prompt"]
        username = user_info["username"]
        payload = {
            "username": username,
            "prompt": stored_prompt + '\n' + REGULAR_UPDATE_PROMPT,
            "daily_report": True,
        }
        url = f"{FASTAPI_BASE_URL}/predict"
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            response_text = data.get("data", {}).get("response", "No response")
        except RequestException as e:
            logger.error("Error calling /predict for daily job: %s", e)
            response_text = f"Error calling /predict: {str(e)}"

        # Send a message back to each user
        await _context.bot.send_message(
            chat_id=chat_id,
            text=response_text
        )


def schedule_daily_job(application):
    """
    Schedule the daily job at a specific time, e.g., 23:59 server time.
    """
    job_queue = application.job_queue
    job_queue.run_repeating(
        callback=daily_predict_job,
        interval=60 * 60 * 24,
        first=0,
        name="regular_report"
    )
