"""Bot handlers for Wish Map Bot."""
import base64
import os
from typing import List

import httpx
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.bot.dialog import Dialog, format_keyboard
from app.config import BACKEND_URL

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Dialog.waiting_selfie)
    await message.answer(
        "Привет! Я создам для тебя карту желаний с твоим фото.\n\n"
        "Отправь своё селфи (фото лица)."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "/start — начать заново\n"
        "/cancel — отменить диалог\n\n"
        "Процесс:\n"
        "1. Отправь своё селфи\n"
        "2. Выбери формат карты\n"
        "3. Введи от 3 до 9 желаний (каждое отдельным сообщением)\n"
        "4. Напиши ГОТОВО, чтобы завершить"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог сброшен. Отправь /start, чтобы начать заново.")


@router.message(Dialog.waiting_selfie, F.photo)
async def handle_selfie(message: Message, state: FSMContext, bot: Bot):
    """Handle selfie photo upload."""
    photo = message.photo[-1]  # Get highest quality
    file = await bot.get_file(photo.file_id)
    
    # Download photo
    file_bytes = await bot.download_file(file.file_path)
    photo_data = file_bytes.read()
    
    # Convert to base64 for storage/transmission
    photo_b64 = base64.b64encode(photo_data).decode()
    
    # Get file URL (Telegram file URL)
    photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    await state.update_data(selfie_b64=photo_b64, selfie_url=photo_url)
    await state.set_state(Dialog.choosing_format)
    
    await message.answer(
        "Фото получено! Теперь выбери формат карты:",
        reply_markup=format_keyboard()
    )


@router.callback_query(Dialog.choosing_format)
async def choose_format(callback: CallbackQuery, state: FSMContext):
    format_key = callback.data
    if format_key not in ["phone", "pc", "a4"]:
        await callback.answer("Неизвестный формат", show_alert=True)
        return
    
    await state.update_data(format=format_key, wishes=[])
    await state.set_state(Dialog.collecting_wishes)
    
    format_names = {
        "phone": "Phone Wallpaper",
        "pc": "Computer Wallpaper",
        "a4": "Print A4",
    }
    
    await callback.message.answer(
        f"Формат выбран: {format_names[format_key]}\n\n"
        "Теперь введи от 3 до 9 желаний.\n"
        "Каждое желание — отдельным сообщением.\n"
        "Когда закончишь — напиши ГОТОВО."
    )
    await callback.answer()


@router.message(Dialog.collecting_wishes, F.text)
async def handle_wish(message: Message, state: FSMContext):
    text = message.text.strip()
    
    if text.upper() == "ГОТОВО":
        data = await state.get_data()
        wishes: List[str] = data.get("wishes", [])
        
        if len(wishes) < 3:
            await message.answer("Нужно минимум 3 желания. Введи ещё.")
            return
        
        await state.set_state(Dialog.confirmation)
        await message.answer(
            f"Отлично! Получено {len(wishes)} желаний. "
            f"Начинаю генерацию карты... Это может занять несколько минут."
        )
        await trigger_generation(message, state)
        return
    
    data = await state.get_data()
    wishes: List[str] = data.get("wishes", [])
    
    if len(wishes) >= 9:
        await message.answer("Максимум 9 желаний. Напиши ГОТОВО, чтобы завершить.")
        return
    
    wishes.append(text)
    await state.update_data(wishes=wishes)
    
    remaining = 9 - len(wishes)
    if remaining > 0:
        await message.answer(
            f"Принято ({len(wishes)}/9). "
            f"Можно добавить ещё {remaining} желаний или написать ГОТОВО."
        )
    else:
        await message.answer(f"Принято ({len(wishes)}/9). Напиши ГОТОВО, чтобы завершить.")


async def trigger_generation(message: Message, state: FSMContext):
    """Trigger map generation via backend API."""
    data = await state.get_data()
    wishes: List[str] = data.get("wishes", [])
    format_key = data.get("format")
    selfie_url = data.get("selfie_url")
    
    if not wishes or not format_key or not selfie_url:
        await message.answer("Не хватает данных. Начни заново /start.")
        await state.clear()
        return
    
    # Show progress
    progress_msg = await message.answer("⏳ Генерирую карту... Это может занять 5-10 минут.")
    
    payload = {
        "wishes": wishes,
        "format": format_key,
        "selfie_url": selfie_url,
    }
    
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for Kolors
            resp = await client.post(f"{BACKEND_URL}/api/assemble_map", json=payload)
            resp.raise_for_status()
            result = resp.json()
    except httpx.TimeoutException:
        await progress_msg.delete()
        await message.answer(
            "⏱️ Превышено время ожидания. "
            "Генерация может занять больше времени. Попробуй ещё раз /start."
        )
        await state.clear()
        return
    except httpx.HTTPStatusError as e:
        await progress_msg.delete()
        error_detail = "Неизвестная ошибка"
        try:
            error_data = e.response.json()
            error_detail = error_data.get("detail", str(e))
        except:
            error_detail = str(e)
        await message.answer(f"❌ Ошибка при генерации: {error_detail}\nПопробуй ещё раз /start.")
        await state.clear()
        return
    except Exception as err:
        await progress_msg.delete()
        await message.answer(f"❌ Ошибка при генерации: {err}\nПопробуй ещё раз /start.")
        await state.clear()
        return
    
    # Check result
    if result.get("status") != "success":
        await progress_msg.delete()
        await message.answer("❌ Генерация не удалась. Попробуй ещё раз /start.")
        await state.clear()
        return
    
    map_b64 = result.get("map_b64")
    if map_b64:
        try:
            await progress_msg.delete()
            photo_bytes = base64.b64decode(map_b64)
            await message.answer_photo(
                photo=BufferedInputFile(photo_bytes, filename="wish-map.png"),
                caption="✨ Ваша карта желаний готова!"
            )
        except Exception as send_err:
            await message.answer(f"Карта сгенерирована, но не удалось отправить: {send_err}")
    else:
        await progress_msg.delete()
        await message.answer("Карта сгенерирована, но файл не получен. Попробуй ещё раз /start.")
    
    await state.clear()
