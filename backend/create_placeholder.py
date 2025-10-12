from PIL import Image, ImageDraw

def create_placeholder():
    """Создает placeholder изображение"""
    img = Image.new('RGB', (300, 300), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Добавляем крестик
    draw.line([(50, 50), (250, 250)], fill='#ccc', width=3)
    draw.line([(250, 50), (50, 250)], fill='#ccc', width=3)
    
    # Текст
    draw.text((150, 150), "No Image", fill='#999', anchor="mm")
    
    # Сохраняем
    os.makedirs("../frontend/images", exist_ok=True)
    img.save("../frontend/images/placeholder.webp", "WEBP")
    print("✅ Placeholder создан")

if __name__ == "__main__":
    create_placeholder()