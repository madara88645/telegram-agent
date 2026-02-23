import difflib
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional
import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, ContextTypes, MessageHandler,
                          filters)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))
WORKSPACE_DIR = Path(os.getenv("TELEGRAM_WORKSPACE", os.getcwd())).resolve()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

MAX_OUTPUT_CHARS = 3500
COMMAND_TIMEOUT = 300

ALLOWED_COMMANDS = {
    "status": ["git", "status", "-sb"],
    "tests": ["python", "-m", "pytest", "-q"],
    "pip_list": ["python", "-m", "pip", "list"],
    "pwd": ["powershell", "-Command", "Get-Location"],
    "workspace": ["powershell", "-Command", f"echo {WORKSPACE_DIR}"],
}


class PendingPlan:
    def __init__(self, kind: str, description: str, command: Optional[list] = None,
                 file_path: Optional[Path] = None, new_content: Optional[str] = None,
                 diff_text: Optional[str] = None):
        self.kind = kind
        self.description = description
        self.command = command
        self.file_path = file_path
        self.new_content = new_content
        self.diff_text = diff_text


PENDING: Dict[int, PendingPlan] = {}


def is_allowed(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == ALLOWED_USER_ID


def format_output(text: str) -> str:
    text = text.strip() or "(Cikti yok)"
    if len(text) > MAX_OUTPUT_CHARS:
        text = text[:MAX_OUTPUT_CHARS] + "\n...(kisaltilmis)"
    return text


def safe_path(relative_path: str) -> Optional[Path]:
    candidate = (WORKSPACE_DIR / relative_path).resolve()
    if WORKSPACE_DIR not in candidate.parents and candidate != WORKSPACE_DIR:
        return None
    return candidate


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "Agent hazir. /help ile komutlari gorebilirsin."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    commands = ", ".join(ALLOWED_COMMANDS.keys())
    await update.message.reply_text(
        "Kullanilabilir komutlar:\n"
        f"- /run <komut_anahtari> (ornek: /run status)\n"
        "- /ask <soru> - OpenRouter LLM ile sohbet\n"
        "- edit <dosya_yolu> + icerik (format asagida)\n\n"
        "Yeni icerik formati:\n"
        "edit <dosya_yolu>\n<<<\n(yeni icerik)\n>>>\n\n"
        f"Komut anahtarlari: {commands}"
    )


async def ask_llm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    
    if not OPENROUTER_API_KEY:
        await update.message.reply_text("OPENROUTER_API_KEY tanimli degil.")
        return
    
    if not context.args:
        await update.message.reply_text("/ask <soru> formatinda yaz.")
        return
    
    question = " ".join(context.args)
    await update.message.reply_text("Dusunuyorum...")
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": question}]
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        await update.message.reply_text(format_output(answer))
    except Exception as exc:
        await update.message.reply_text(f"Hata: {exc}")


async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    if not context.args:
        await update.message.reply_text("/run <komut_anahtari> kullan.")
        return

    key = context.args[0].strip()
    command = ALLOWED_COMMANDS.get(key)
    if not command:
        await update.message.reply_text("Bu komut whitelist disi.")
        return

    plan = PendingPlan(kind="command", description=f"Komut: {key}", command=command)
    PENDING[update.effective_chat.id] = plan

    keyboard = [[
        InlineKeyboardButton("Onayla", callback_data="approve"),
        InlineKeyboardButton("Iptal", callback_data="cancel"),
    ]]
    await update.message.reply_text(
        f"Plan: {plan.description}\nOnayliyor musun?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def parse_edit_message(text: str) -> Optional[tuple]:
    if not text.startswith("edit "):
        return None
    if "\n<<<\n" not in text or "\n>>>" not in text:
        return None
    header, rest = text.split("\n", 1)
    _, path_part = header.split(" ", 1)
    content = text.split("\n<<<\n", 1)[1]
    new_content = content.split("\n>>>", 1)[0]
    return path_part.strip(), new_content


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    text = update.message.text.strip()
    edit_payload = parse_edit_message(text)
    if not edit_payload:
        await update.message.reply_text(
            "Komut bulunamadi. /help ile ornekleri gorebilirsin."
        )
        return

    relative_path, new_content = edit_payload
    file_path = safe_path(relative_path)
    if not file_path:
        await update.message.reply_text("Gecersiz dosya yolu.")
        return

    if not file_path.exists():
        await update.message.reply_text("Dosya bulunamadi.")
        return

    old_content = file_path.read_text(encoding="utf-8")
    diff = "\n".join(
        difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            fromfile=str(file_path),
            tofile=str(file_path),
            lineterm="",
        )
    )
    diff_text = diff if diff else "(Degisiklik yok)"

    plan = PendingPlan(
        kind="file_edit",
        description=f"Dosya guncelleme: {relative_path}",
        file_path=file_path,
        new_content=new_content,
        diff_text=diff_text,
    )
    PENDING[update.effective_chat.id] = plan

    keyboard = [[
        InlineKeyboardButton("Onayla", callback_data="approve"),
        InlineKeyboardButton("Iptal", callback_data="cancel"),
    ]]

    await update.message.reply_text(
        f"Plan: {plan.description}\nDiff:\n{format_output(diff_text)}\n\nOnayliyor musun?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    query = update.callback_query
    await query.answer()

    plan = PENDING.get(query.message.chat_id)
    if not plan:
        await query.edit_message_text("Bekleyen plan yok.")
        return

    if query.data == "cancel":
        PENDING.pop(query.message.chat_id, None)
        await query.edit_message_text("Iptal edildi.")
        return

    if plan.kind == "command" and plan.command:
        try:
            result = subprocess.run(
                plan.command,
                cwd=str(WORKSPACE_DIR),
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT,
            )
            output = format_output(result.stdout + "\n" + result.stderr)
            await query.edit_message_text(f"Calistirildi.\nCikti:\n{output}")
        except Exception as exc:
            await query.edit_message_text(f"Hata: {exc}")
        finally:
            PENDING.pop(query.message.chat_id, None)
        return

    if plan.kind == "file_edit" and plan.file_path:
        try:
            plan.file_path.write_text(plan.new_content or "", encoding="utf-8")
            await query.edit_message_text("Dosya guncellendi.")
        except Exception as exc:
            await query.edit_message_text(f"Hata: {exc}")
        finally:
            PENDING.pop(query.message.chat_id, None)
        return


def main() -> None:
    if not BOT_TOKEN or not ALLOWED_USER_ID:
        raise SystemExit("TELEGRAM_BOT_TOKEN ve TELEGRAM_USER_ID tanimli olmali.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ask", ask_llm))
    app.add_handler(CommandHandler("run", run_command))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
