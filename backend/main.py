from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import json
import requests
import datetime

# Пытаемся импортировать image_processor, но если его нет - создаем заглушку
try:
    from image_processor import image_processor
except ImportError:
    print("[WARN] image_processor not found, using stub")
    class ImageProcessorStub:
        def process_multiple_images(self, images, name, product_id):
            # Заглушка для обработки изображений
            return [{'small': '/static/images/placeholder.webp', 'large': '/static/images/placeholder.webp'}]
    image_processor = ImageProcessorStub()

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ИСПРАВЛЕННЫЙ ПУТЬ К FRONTEND - поднимаемся на уровень выше
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Поднимаемся на уровень выше backend
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

print(f"[INFO] Base directory: {BASE_DIR}")
print(f"[INFO] Project root: {PROJECT_ROOT}")
print(f"[INFO] Frontend directory: {FRONTEND_DIR}")
print(f"[INFO] Frontend exists: {os.path.exists(FRONTEND_DIR)}")

if os.path.exists(FRONTEND_DIR):
    print(f"[INFO] Frontend contents: {os.listdir(FRONTEND_DIR)}")
    # Монтируем статические файлы только если директория существует
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
else:
    print(f"[ERROR] Frontend directory not found at {FRONTEND_DIR}")
    print(f"[INFO] Current working directory: {os.getcwd()}")
    print(f"[INFO] Directory contents:")
    for item in os.listdir(PROJECT_ROOT):
        print(f"  - {item}")

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "calistorAdminToken")
PRODUCTS_FILE = "products.json"

# ======== Функции загрузки и сохранения ========
def load_products():
    try:
        if os.path.exists(PRODUCTS_FILE):
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[INFO] Loaded {len(data)} products from {PRODUCTS_FILE}")
                return data
        print(f"[INFO] Products file not found, using default")
        return []
    except Exception as e:
        print(f"[ERROR] load_products error: {e}")
        return []

def save_products(products):
    try:
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Saved {len(products)} products to {PRODUCTS_FILE}")
    except Exception as e:
        print(f"[ERROR] save_products error: {e}")

# Загружаем продукты
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
            "image": "/static/images/placeholder.webp",
            "image_large": "/static/images/placeholder.webp",
            "images": ["/static/images/placeholder.webp"],
            "images_large": ["/static/images/placeholder.webp"]
        },
        {
            "id": 2,
            "name": "Толстовка",
            "price": 6000,
            "color": "черный",
            "available_sizes": {"S": 5, "M": 8, "L": 3},
            "composition": "94% хлопок, 6% спандекс",
            "description": "Теплая и уютная толстовка для прохладных дней.",
            "image": "/static/images/placeholder.webp",
            "image_large": "/static/images/placeholder.webp",
            "images": ["/static/images/placeholder.webp"],
            "images_large": ["/static/images/placeholder.webp"]
        }
    ]
    save_products(products)

# ======== Вспомогательные ========

def verify_admin_token(token: str):
    is_valid = token == ADMIN_SECRET
    print(f"[DEBUG] Token verification: {is_valid}")
    return is_valid

# ======== Основные маршруты ========

@app.get("/")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback - возвращаем простую страницу
    return {"message": "Frontend not found. Please check frontend directory."}

@app.get("/admin")
def serve_admin():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    
    # Fallback
    return {"message": "Admin page not found. Please check frontend directory."}

@app.get("/api/products")
def get_products():
    """Возвращает товары для сайта и мини-аппа"""
    print(f"[DEBUG] === ЗАПРОС /api/products ===")
    
    # Всегда загружаем свежие данные из файла
    current_products = load_products()
    print(f"[DEBUG] Загружено из файла: {len(current_products)} товаров")
    
    products_for_client = []
    for product in current_products:
        p = product.copy()
        if "available_sizes" in p:
            p["sizes"] = list(p["available_sizes"].keys())
        else:
            p["sizes"] = []
        products_for_client.append(p)
    
    print(f"[DEBUG] Отправляем клиенту: {len(products_for_client)} товаров")
    return products_for_client

# ======== Статические файлы ========

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

# УНИФИЦИРОВАННЫЙ МАРШРУТ ДЛЯ ВСЕХ ИЗОБРАЖЕНИЙ
@app.get("/images/{path:path}")
def serve_images(path: str):
    if not os.path.exists(FRONTEND_DIR):
        raise HTTPException(status_code=404, detail="Frontend directory not found")
    
    file_path = os.path.join(FRONTEND_DIR, "images", path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail=f"Image not found: {path}")

# ======== Админка API ========

@app.post("/api/admin/verify-token")
async def verify_token(data: dict):
    """Проверка валидности токена"""
    token = data.get('token')
    print(f"[DEBUG] Verify token request: {token}")
    
    if verify_admin_token(token):
        return {"status": "valid"}
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/admin/login")
def admin_login(login_data: dict):
    token = login_data.get("token")
    print(f"[DEBUG] Login attempt with token: {token}")
    
    if verify_admin_token(token):
        return {"status": "success", "message": "Добро пожаловать в админку!"}
    raise HTTPException(status_code=401, detail="Неверный токен доступа")

@app.get("/api/admin/products")
def get_admin_products(token: str):
    print(f"[DEBUG] Get admin products with token: {token}")
    
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")
    
    current_products = load_products()
    enriched = []
    for p in current_products:
        x = p.copy()
        x["sizes"] = list(p.get("available_sizes", {}).keys())
        enriched.append(x)
    
    print(f"[DEBUG] Returning {len(enriched)} products to admin")
    return enriched

@app.get("/api/admin/statistics")
def get_statistics(token: str):
    print(f"[DEBUG] Get statistics with token: {token}")
    
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    current_products = load_products()
    total_products = len(current_products)
    total_items = 0
    size_breakdown = {}

    for product in current_products:
        for size, qty in product.get("available_sizes", {}).items():
            total_items += qty
            size_breakdown[size] = size_breakdown.get(size, 0) + qty

    products_stats = []
    for product in current_products:
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
    print(f"[DEBUG] Create product: {name}")
    
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    try:
        current_products = load_products()
        new_id = max([p["id"] for p in current_products], default=0) + 1
        sizes_data = json.loads(available_sizes)

        print(f"[DEBUG] Processing {len(images)} images for product {new_id}")
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

        current_products.append(new_product)
        save_products(current_products)
        
        print(f"[DEBUG] Product created successfully: {new_id}")
        return {"status": "success", "product": new_product}

    except Exception as e:
        print(f"[ERROR] Create product error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании товара: {e}")

@app.post("/api/admin/banner")
async def upload_banner(
    token: str = Form(...),
    banner_image: UploadFile = File(...)
):
    """Загрузка баннера"""
    print(f"[DEBUG] Upload banner request")
    
    # 1. Проверка токена
    if not verify_admin_token(token):
        # 🚨 Ваша главная проблема, судя по скриншотам, вот здесь (401)
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    # 2. Проверка и создание директории
    if not os.path.exists(FRONTEND_DIR):
        raise HTTPException(status_code=500, detail="Frontend directory not found")

    image_dir = os.path.join(FRONTEND_DIR, "images")
    # 🟢 Создание папки, если она не существует (это у вас уже есть)
    os.makedirs(image_dir, exist_ok=True) 
    
    output_path = os.path.join(image_dir, 'banner.webp')
    
    try:
        # 3. Чтение файла и сохранение
        content = await banner_image.read()
        
        with open(output_path, "wb") as buffer:
            buffer.write(content)
            
        print(f"[DEBUG] Banner saved to: {output_path}")
        return {"status": "success", "message": "Баннер успешно обновлен!", "path": output_path}
        
    except Exception as e:
        print(f"[ERROR] Banner upload error: {e}")
        # Возвращаем 500 ошибку, если что-то пошло не так при сохранении
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения баннера: {e}")
    
@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, token: str):
    print(f"[DEBUG] Delete product: {product_id}")
    
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Доступ запрещен")

    try:
        current_products = load_products()
        updated_products = [p for p in current_products if p["id"] != product_id]
        
        if len(updated_products) == len(current_products):
            raise HTTPException(status_code=404, detail="Товар не найден")
            
        save_products(updated_products)
        print(f"[DEBUG] Product {product_id} deleted successfully")
        return {"status": "success", "message": "Товар удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Delete product error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении товара: {e}")

# ======== Отладочные маршруты ========

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

@app.get("/api/debug/paths")
def debug_paths():
    """Отладочный эндпоинт для проверки путей"""
    return {
        "base_dir": BASE_DIR,
        "project_root": PROJECT_ROOT,
        "frontend_dir": FRONTEND_DIR,
        "frontend_exists": os.path.exists(FRONTEND_DIR),
        "products_file": os.path.abspath(PRODUCTS_FILE),
        "products_file_exists": os.path.exists(PRODUCTS_FILE),
        "current_working_dir": os.getcwd()
    }

@app.get("/api/test")
def test_endpoint():
    return {
        "status": "ok", 
        "message": "Сервер работает",
        "timestamp": datetime.datetime.now().isoformat()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
