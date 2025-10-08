from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

# Попробуем импортировать requests с обработкой ошибки
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Библиотека 'requests' не установлена. Установите: pip install requests")

load_dotenv()

app = FastAPI()

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем папку фронтенда как статические файлы
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Тестовые данные товаров
products = [
    {
        "id": 1,
        "name": "Футболка box-fit",
        "price": 4000,
        "color": "белый", 
        "size": "one size",
        "image": "/static/images/products/wewe-small.webp",
        "image_large": "/static/images/products/large.webp",
        "composition": "95% хлопок, 5% лайкра",
        "description": "Премиальная футболка идеального кроя."
    },
    {
        "id": 2,
        "name": "Футболка box-fit",
        "price": 4000,
        "color": "белый", 
        "size": "one size",
        "image": "/static/images/products/dada-small.webp",
        "image_large": "/static/images/products/dada-large.webp",
        "composition": "95% хлопок, 5% лайкра",
        "description": "Премиальная футболка идеального кроя."
    },
    {
        "id": 3,
        "name": "Футболка box-fit",
        "price": 4000,
        "color": "белый", 
        "size": "one size",
        "image": "/static/images/products/obraz1.webp",
        "image_large": "/static/images/products/obraz2.webp",
        "composition": "95% хлопок, 5% лайкра",
        "description": "Премиальная футболка идеального кроя."
    },
    {
        "id": 4,
        "name": "Футболка box-fit",
        "price": 4000,
        "color": "белый", 
        "size": "one size",
        "image": "/static/images/products/kaif1.webp",
        "image_large": "/static/images/products/kaif.webp",
        "composition": "95% хлопок, 5% лайкра",
        "description": "Премиальная футболка идеального кроя."
    },
    # ... остальные товары
]
# Главная страница - отдаем HTML
@app.get("/")
def serve_frontend():
    return FileResponse("../frontend/index.html")

# API endpoint для товаров
@app.get("/api/products")
def get_products():
    return products

# Отдаем другие фронтенд-файлы
@app.get("/style.css")
def serve_css():
    return FileResponse("../frontend/style.css")

@app.get("/app.js")
def serve_js():
    return FileResponse("../frontend/app.js")

# Endpoint для заказов
@app.post("/api/order")
async def create_order(order_data: dict):
    try:
        if not REQUESTS_AVAILABLE:
            raise HTTPException(
                status_code=500, 
                detail="Сервер не настроен. Установите: pip install requests"
            )
        
        bot_token = os.getenv("BOT_TOKEN")
        manager_chat_id = os.getenv("MANAGER_CHAT_ID")
        
        if not bot_token:
            raise HTTPException(
                status_code=500, 
                detail="BOT_TOKEN не настроен. Добавьте в .env файл"
            )
        
        if not manager_chat_id:
            raise HTTPException(
                status_code=500, 
                detail="MANAGER_CHAT_ID не настроен. Добавьте в .env файл"
            )
        
        # Формируем сообщение
        message = format_order_message(order_data)
        
        # Отправляем сообщение через Telegram Bot API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": manager_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Order sent to manager"}
        else:
            error_info = response.json()
            raise HTTPException(
                status_code=500, 
                detail=f"Telegram API error: {error_info.get('description', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_order_message(order_data):
    products = order_data.get("products", [])
    user_info = order_data.get("user", {})
    total_price = order_data.get("total_price", 0)
    
    message = "🛍️ <b>НОВЫЙ ЗАКАЗ ИЗ MINI APP</b>\n\n"
    message += "<b>Товары:</b>\n"
    
    for i, product in enumerate(products, 1):
        message += f"{i}. {product['name']}\n"
        message += f"   • Размер: {product['size']}\n"
        message += f"   • Цвет: {product['color']}\n"
        message += f"   • Цена: {product['price']}₽\n\n"
    
    message += f"💰 <b>Итого: {total_price}₽</b>\n\n"
    message += "<b>Информация о покупателе:</b>\n"
    message += f"👤 ID: {user_info.get('id', 'Неизвестно')}\n"
    message += f"📛 Имя: {user_info.get('first_name', 'Неизвестно')}\n"
    message += f"📞 Username: @{user_info.get('username', 'Не указан')}\n"
    
    return message

@app.get("/images/banner.webp")
def serve_banner():
    return FileResponse("../frontend/images/banner.webp")