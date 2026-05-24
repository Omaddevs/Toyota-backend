"""
Telegram botni long-polling orqali ishlatish (lokal dev uchun).
Ishlatish: python manage.py run_bot

Production'da bu emas, webhook ishlatiladi:
  /api/telegram/webhook/
"""

import json
import time
import urllib.request
import urllib.error

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone


class Command(BaseCommand):
    help = "Telegram botni long-polling orqali ishlatadi (dev uchun)"

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not token:
            self.stderr.write("TELEGRAM_BOT_TOKEN .env faylida yo'q!")
            return

        bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "bot")
        self.stdout.write(self.style.SUCCESS(
            f"Bot ishga tushdi: @{bot_username}\n"
            f"To'xtatish uchun Ctrl+C bosing.\n"
        ))

        base_url = f"https://api.telegram.org/bot{token}"
        offset = 0

        while True:
            try:
                updates = self._get_updates(base_url, offset)
            except KeyboardInterrupt:
                self.stdout.write("\nBot to'xtatildi.")
                break
            except Exception as e:
                self.stderr.write(f"getUpdates xatosi: {e}")
                time.sleep(5)
                continue

            for update in updates:
                offset = update["update_id"] + 1
                try:
                    self._process_update(base_url, update)
                except Exception as e:
                    self.stderr.write(f"Update xatosi: {e}")

    def _get_updates(self, base_url, offset):
        url = f"{base_url}/getUpdates?timeout=30&offset={offset}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read())
        if not data.get("ok"):
            return []
        return data.get("result", [])

    def _send_message(self, base_url, chat_id, text):
        url = f"{base_url}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            self.stderr.write(f"sendMessage xatosi: {e}")

    def _process_update(self, base_url, update):
        from catalog.models import PhoneOTP

        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()
        if not chat_id or not text:
            return

        self.stdout.write(f"[{chat_id}] {text}")

        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            param = parts[1].strip() if len(parts) > 1 else ""

            if param.startswith("otp"):
                try:
                    otp_id = int(param[3:])
                    otp = PhoneOTP.objects.get(id=otp_id, is_used=False)
                except (ValueError, PhoneOTP.DoesNotExist):
                    self._send_message(
                        base_url, chat_id,
                        "❌ Tasdiqlash kodi topilmadi yoki muddati o'tgan. "
                        "Qaytadan ro'yxatdan o'ting."
                    )
                    return

                if otp.is_expired():
                    self._send_message(
                        base_url, chat_id,
                        "⏰ Tasdiqlash kodining muddati o'tib ketdi. "
                        "Qaytadan ro'yxatdan o'ting."
                    )
                    return

                otp.telegram_chat_id = chat_id
                otp.save(update_fields=["telegram_chat_id"])

                self._send_message(
                    base_url, chat_id,
                    f"🔐 Sizning tasdiqlash kodingiz:\n\n"
                    f"<b>{otp.code}</b>\n\n"
                    f"Bu kodni ToyMakon saytiga kiriting.\n"
                    f"Kod 10 daqiqa amal qiladi."
                )
                self.stdout.write(self.style.SUCCESS(
                    f"  → Kod yuborildi: {otp.code} → chat {chat_id}"
                ))
            else:
                self._send_message(
                    base_url, chat_id,
                    "👋 Assalomu alaykum! <b>ToyMakon</b> botiga xush kelibsiz!\n\n"
                    "Bu bot orqali ro'yxatdan o'tish uchun tasdiqlash kodini olasiz.\n"
                    "ToyMakon saytiga o'ting va ro'yxatdan o'tish tugmasini bosing."
                )
        else:
            self._send_message(
                base_url, chat_id,
                "❓ Buyruq tanilmadi. ToyMakon saytidan ro'yxatdan o'ting."
            )
