from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import json
from image_processor import image_processor
import requests

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Рекомендуется использовать абсолютный путь к frontend'у
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if not os.path.isdir(FRONTEND_DIR):
    print(f"[WARN] Frontend directory not found at {FRONTEND_DIR}")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "calistor_admin_2024")
PRODUCTS_FILE = "products.json"

def load_products():
    try:
        if os.path.exists(PRODUCTS_FILE):
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"[WARN] load_products error: {e}")
        return []

def save_products(products):
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

products = load_products()

if not products:
    products = [
        {
            "id": 1,
            "name": "Футболка box-fit",
            "price": 4000,
            "color": "белый",
            "size": "one size",
            "image": "/static/images/products/product-1-small.webp",
            "image_large": "/static/images/products/product-1-large.webp",
            "composition": "95% хлопок, 5% лайкра",
            "description": "Премиальная футболка идеального кроя. Удобная и стильная для повседневной носки."
        },
        {
            "id": 2,
            "name": "Толстовка", 
            "price": 6000,
            "color": "черный",
            "size": "s",
            "image": "/static/images/products/product-2-small.webp",
            "image_large": "/static/images/products/product-2-large.webp",
            "composition": "94% хлопок, 6% спандекс",
            "description": "Теплая и уютная толстовка для прохладных дней. Качественный материал и аккуратная прострочка."
        }
    ]
    save_products(products)

@app.get("/")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index not found")

@app.get("/api/products")
def get_products():
    return products

@app.get("/style.css")
def serve_css():
    css_path = os.path.join(FRONTEND_DIR, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path)
    raise HTTPException(status_code=404)

@app.get("/app.js")
def serve_js():
    js_path = os.path.join(FRONTEND_DIR, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path)
    raise HTTPException(status_code=404)

@app.get("/images/banner.webp")
def serve_banner():
    banner_path = os.path.join(FRONTEND_DIR, "images", "banner.webp")
    if os.path.exists(banner_path):
        return FileResponse(banner_path)
    raise HTTPException(status_code=404)

# ========== ЭНДПОИНТЫ ДЛЯ ИЗОБРАЖЕНИЙ ==========

@app.get("/static/images/products/{filename}")
def serve_product_image(filename: str):
    """Раздаем изображения товаров"""
    file_path = os.path.join(FRONTEND_DIR, "images", "products", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        # Если файла нет, возвращаем placeholder
        placeholder_path = os.path.join(FRONTEND_DIR, "images", "placeholder.webp")
        if os.path.exists(placeholder_path):
            return FileResponse(placeholder_path)
        raise HTTPException(status_code=404, detail="Image not found")

@app.get("/static/images/{filename}")
def serve_image(filename: str):
    """Раздаем другие изображения"""
    file_path = os.path.join(FRONTEND_DIR, "images", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="Image not found")

# ========== АДМИН ЭНДПОИНТЫ ==========

def verify_admin_token(token: str):
    return token == ADMIN_SECRET

@app.get("/admin")
def serve_admin():
    """Страница админки"""
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="Admin page not found")

@app.post("/api/admin/login")
def admin_login(login_data: dict):
    token = login_data.get("token")
    if verify_admin_token(token):
        return {"status": "success", "message": "Добро пожаловать в админку!"}
    else:
        raise HTTPException(status_code=401, detail="Неверный токен доступа")

@app.get("/api/admin/products")
def get_admin_products(token: str):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")
    return products

@app.post("/api/admin/products")
async def create_product(
    token: str = Form(...),
    name: str = Form(...),
    price: int = Form(...),
    color: str = Form(...),
    size: str = Form(...),
    composition: str = Form(...),
    description: str = Form(...),
    images: list[UploadFile] = File(...)  # Теперь принимаем список файлов
):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    try:
        new_id = max([p["id"] for p in products], default=0) + 1

        # Обрабатываем несколько изображений
        all_image_paths = image_processor.process_multiple_images(images, name, new_id)
        
        if not all_image_paths or len(all_image_paths) == 0:
            raise HTTPException(status_code=500, detail="Ошибка обработки изображений")

        # Формируем списки путей для small и large изображений
        small_images = [img_paths['small'] for img_paths in all_image_paths]
        large_images = [img_paths['large'] for img_paths in all_image_paths]

        new_product = {
            "id": new_id,
            "name": name,
            "price": price,
            "color": color,
            "size": size,
            "images": small_images,        # Список маленьких изображений
            "images_large": large_images,  # Список больших изображений
            "image": small_images[0] if small_images else "/static/images/placeholder.webp",  # Главное изображение
            "image_large": large_images[0] if large_images else "/static/images/placeholder.webp",
            "composition": composition,
            "description": description
        }

        products.append(new_product)
        save_products(products)
        return {"status": "success", "product": new_product}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании товара: {e}")
@app.put("/api/admin/products/{product_id}")
async def update_product(product_id: int, product_data: dict):
    token = product_data.get("token")
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    product_index = next((i for i, p in enumerate(products) if p["id"] == product_id), None)
    if product_index is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    for key, value in product_data.items():
        if key not in ["token", "id"] and value is not None:
            products[product_index][key] = value

    save_products(products)
    return {"status": "success", "product": products[product_index]}

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, token: str):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    global products
    products = [p for p in products if p["id"] != product_id]
    save_products(products)
    return {"status": "success", "message": "Товар удален"}

# ========== ЗАКАЗЫ ==========

@app.post("/api/order")
async def create_order(order_data: dict):
    try:
        bot_token = os.getenv("BOT_TOKEN")
        manager_chat_id = os.getenv("MANAGER_CHAT_ID")
        if not bot_token or not manager_chat_id:
            raise HTTPException(status_code=500, detail="Bot not configured")

        message = format_order_message(order_data)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": manager_chat_id, "text": message, "parse_mode": "HTML"}

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return {"status": "success", "message": "Order sent to manager"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_order_message(order_data):
    products_list = order_data.get("products", [])
    user_info = order_data.get("user", {})
    total_price = order_data.get("total_price", 0)

    message = "🛍️ <b>НОВЫЙ ЗАКАЗ ИЗ MINI APP</b>\n\n"
    message += "<b>Товары:</b>\n"
    for i, product in enumerate(products_list, 1):
        message += f"{i}. {product['name']}\n"
        message += f"   • Размер: {product.get('size','-')}\n"
        message += f"   • Цвет: {product.get('color','-')}\n"
        message += f"   • Цена: {product.get('price','-')}₽\n\n"

    message += f"💰 <b>Итого: {total_price}₽</b>\n\n"
    message += "<b>Информация о покупателе:</b>\n"
    message += f"👤 ID: {user_info.get('id', 'Неизвестно')}\n"
    message += f"📛 Имя: {user_info.get('first_name', 'Неизвестно')}\n"
    message += f"📞 Username: @{user_info.get('username', 'Не указан')}\n"
    return message