from PIL import Image
import os
import glob

def create_full_banner():
    """Создает баннер для полной ширины"""
    
    source_folder = "original_images"
    
    if not os.path.exists(source_folder):
        print(f"❌ Папка '{source_folder}' не найдена!")
        return
    
    # Ищем изображения
    images = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        images.extend(glob.glob(os.path.join(source_folder, ext)))
    
    if not images:
        print("❌ Положите изображение в backend/original_images/")
        return
    
    # Берем первое изображение
    image_path = images[0]
    
    try:
        with Image.open(image_path) as img:
            print(f"🔄 Создаю баннер из: {os.path.basename(image_path)}")
            
            # Конвертируем в RGB если нужно
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Оптимальные размеры для баннера (широкий формат)
            # 800x400 для хорошего качества на всех устройствах
            target_width = 800
            target_height = 400
            
            # Изменяем размер с сохранением пропорций и обрезкой
            # Сначала вычисляем соотношения
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Изображение шире - обрезаем по бокам
                new_height = target_height
                new_width = int(img.width * (target_height / img.height))
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Обрезаем по ширине
                left = (new_width - target_width) // 2
                right = left + target_width
                banner = img_resized.crop((left, 0, right, target_height))
                
            else:
                # Изображение выше - обрезаем сверху и снизу
                new_width = target_width
                new_height = int(img.height * (target_width / img.width))
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Обрезаем по высоте
                top = (new_height - target_height) // 2
                bottom = top + target_height
                banner = img_resized.crop((0, top, target_width, bottom))
            
            # Сохраняем
            os.makedirs("../frontend/images", exist_ok=True)
            output_path = "../frontend/images/banner.webp"
            banner.save(output_path, "WEBP", quality=85, optimize=True)
            
            file_size = os.path.getsize(output_path) / 1024
            print(f"✅ Баннер создан: {output_path}")
            print(f"📊 Размер: {banner.width}x{banner.height} px, Вес: {file_size:.1f} KB")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🖼 Создание баннера на всю ширину")
    print("=" * 40)
    create_full_banner()