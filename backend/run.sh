#!/bin/bash
# === Calistor backend launcher ===

# Переходим в директорию скрипта (на случай, если запускаешь из другого места)
cd "$(dirname "$0")"

# Проверяем, существует ли виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "⚠️  Виртуальное окружение не найдено. Создаю..."
    python3 -m venv .venv
fi

# Активируем виртуальное окружение
source .venv/bin/activate

# Обновляем pip и зависимости, если нужно
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null

# Запускаем сервер
echo "🚀 Запускаю Uvicorn сервер..."
uvicorn main:app --reload --port 8000
