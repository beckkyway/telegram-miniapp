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

# ======== Функции загрузки и сохранения ========
def load_products():
    try:
        if os.path.exists(PRODUCTS_FILE):
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
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
            "available_sizes": {"one size": 10},
            "composition": "95% хлопок, 5% лайкра",
            "description": "Премиальная футболка идеального кроя. Удобная и стильная для повседневной носки.",
            "image": "/static/images/products/product-1-small.webp",
            "image_large": "/static/images/products/product-1-large.webp",
            "images": ["/static/images/products/product-1-small.webp"],
            "images_large": ["/static/images/products/product-1-large.webp"]
        },
        {
            "id": 2,
            "name": "Толстовка",
            "price": 6000,
            "color": "черный",
            "available_sizes": {"S": 5, "M": 8, "L": 3},
            "composition": "94% хлопок, 6% спандекс",
            "description": "Теплая и уютная толстовка для прохладных дней.",
            "image": "/static/images/products/product-2-small.webp",
            "image_large": "/static/images/products/product-2-large.webp",
            "images": ["/static/images/products/product-2-small.webp"],
            "images_large": ["/static/images/products/product-2-large.webp"]
        }
    ]
    save_products(products)

# ======== Вспомогательные ========
def verify_admin_token(token: str):
    return token == ADMIN_SECRET

# ======== Основные маршруты ========

@app.get("/")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index not found")

@app.get("/api/products")
def get_products():
    """Возвращает товары для сайта и мини-аппа"""
    print(f"[DEBUG] === ЗАПРОС /api/products ===")
    print(f"[DEBUG] Глобальная переменная products: {len(products)} товаров")
    
    # Всегда загружаем свежие данные из файла
    current_products = load_products()
    print(f"[DEBUG] Загружено из файла: {len(current_products)} товаров")
    
    products_for_client = []
    for product in current_products:
        print(f"[DEBUG] Обрабатываем товар: {product['name']}")
        print(f"[DEBUG] available_sizes: {product.get('available_sizes', {})}")
        
        p = product.copy()
        if "available_sizes" in p:
            p["sizes"] = list(p["available_sizes"].keys())
            print(f"[DEBUG] Созданы sizes: {p['sizes']}")
        else:
            p["sizes"] = []
            print(f"[DEBUG] Нет available_sizes")
        products_for_client.append(p)
    
    print(f"[DEBUG] Отправляем клиенту: {len(products_for_client)} товаров")
    return products_for_client

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

# ======== Картинки ========

@app.get("/static/images/products/{filename}")
def serve_product_image(filename: str):
    file_path = os.path.join(FRONTEND_DIR, "images", "products", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    placeholder = os.path.join(FRONTEND_DIR, "images", "placeholder.webp")
    if os.path.exists(placeholder):
        return FileResponse(placeholder)
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/static/images/{filename}")
def serve_image(filename: str):
    file_path = os.path.join(FRONTEND_DIR, "images", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Image not found")

# ======== Админка ========

@app.get("/admin")
def serve_admin():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="Admin page not found")

@app.post("/api/admin/login")
def admin_login(login_data: dict):
    token = login_data.get("token")
    if verify_admin_token(token):
        return {"status": "success", "message": "Добро пожаловать в админку!"}
    raise HTTPException(status_code=401, detail="Неверный токен доступа")

@app.get("/api/admin/products")
def get_admin_products(token: str):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")
    enriched = []
    for p in products:
        x = p.copy()
        x["sizes"] = list(p.get("available_sizes", {}).keys())
        enriched.append(x)
    return enriched

@app.get("/api/admin/statistics")
def get_statistics(token: str):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    total_products = len(products)
    total_items = 0
    size_breakdown = {}

    for product in products:
        for size, qty in product.get("available_sizes", {}).items():
            total_items += qty
            size_breakdown[size] = size_breakdown.get(size, 0) + qty

    products_stats = []
    for product in products:
        total = sum(product.get("available_sizes", {}).values())
        products_stats.append({
            "id": product["id"],
            "name": product["name"],
            "total": total,
            "sizes": product.get("available_sizes", {})
        })

    return {
        "total_products": total_products,
        "total_items": total_items,
        "size_breakdown": size_breakdown,
        "products_stats": products_stats
    }

@app.post("/api/admin/products")
async def create_product(
    token: str = Form(...),
    name: str = Form(...),
    price: int = Form(...),
    color: str = Form(...),
    composition: str = Form(...),
    description: str = Form(...),
    available_sizes: str = Form(...),
    images: list[UploadFile] = File(...)
):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    try:
        new_id = max([p["id"] for p in products], default=0) + 1
        sizes_data = json.loads(available_sizes)

        all_image_paths = image_processor.process_multiple_images(images, name, new_id)
        small = [img['small'] for img in all_image_paths]
        large = [img['large'] for img in all_image_paths]

        new_product = {
            "id": new_id,
            "name": name,
            "price": price,
            "color": color,
            "available_sizes": sizes_data,
            "composition": composition,
            "description": description,
            "images": small,
            "images_large": large,
            "image": small[0] if small else "/static/images/placeholder.webp",
            "image_large": large[0] if large else "/static/images/placeholder.webp"
        }

        products.append(new_product)
        save_products(products)
        return {"status": "success", "product": new_product}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании товара: {e}")

@app.put("/api/admin/products/{product_id}")
async def update_product(product_id: int, product_data: dict):
    token = product_data.get("token")
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    idx = next((i for i, p in enumerate(products) if p["id"] == product_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if "available_sizes" in product_data and isinstance(product_data["available_sizes"], str):
        product_data["available_sizes"] = json.loads(product_data["available_sizes"])

    for k, v in product_data.items():
        if k not in ["token", "id"]:
            products[idx][k] = v

    save_products(products)
    return {"status": "success", "product": products[idx]}

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, token: str):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    global products
    products = [p for p in products if p["id"] != product_id]
    save_products(products)
    return {"status": "success", "message": "Товар удален"}

@app.get("/api/debug/products")
def debug_products():
    """Отладочный эндпоинт для проверки товаров"""
    file_exists = os.path.exists(PRODUCTS_FILE)
    products_data = load_products()
    
    return {
        "file_exists": file_exists,
        "file_path": os.path.abspath(PRODUCTS_FILE),
        "products_count": len(products_data),
        "products": products_data
    }

@app.get("/api/test")
def test_endpoint():
    return {
        "status": "ok", 
        "message": "Сервер работает",
        "timestamp": datetime.now().isoformat()
    }

# ======== Заказы ========

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
        raise HTTPException(status_code=500, detail="Failed to send message")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_order_message(order_data):
    products_list = order_data.get("products", [])
    user_info = order_data.get("user", {})
    total_price = order_data.get("total_price", 0)

    msg = "🛍️ <b>НОВЫЙ ЗАКАЗ ИЗ MINI APP</b>\n\n"
    msg += "<b>Товары:</b>\n"
    for i, p in enumerate(products_list, 1):
        msg += f"{i}. {p['name']}\n"
        msg += f"   • Размер: {p.get('size','-')}\n"
        msg += f"   • Цвет: {p.get('color','-')}\n"
        msg += f"   • Цена: {p.get('price','-')}₽\n\n"
    msg += f"💰 <b>Итого: {total_price}₽</b>\n\n"
    msg += "<b>Информация о покупателе:</b>\n"
    msg += f"👤 ID: {user_info.get('id', 'Неизвестно')}\n"
    msg += f"📛 Имя: {user_info.get('first_name', 'Неизвестно')}\n"
    msg += f"📞 Username: @{user_info.get('username', 'Не указан')}\n"
    return msg
