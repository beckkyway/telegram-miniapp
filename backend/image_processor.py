import os
from PIL import Image
import glob

class ImageProcessor:
    def __init__(self, source_folder="original_images", output_folder="../frontend/images/products"):
        self.source_folder = source_folder
        self.output_folder = output_folder
        self.sizes = {
            'small': (300, 300),   # для карточек товаров
            'large': (600, 600)    # для детальной страницы
        }
        
        # Создаем папки если их нет
        os.makedirs(source_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
    
    def resize_and_crop(self, image, target_size):
        """Обрезает и изменяет размер изображения с сохранением пропорций"""
        # Получаем размеры оригинала
        original_width, original_height = image.size
        target_width, target_height = target_size
        
        # Вычисляем соотношения
        ratio = max(target_width / original_width, target_height / original_height)
        
        # Новые размеры с сохранением пропорций
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # Изменяем размер
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Обрезаем до нужного размера
        left = (new_width - target_width) / 2
        top = (new_height - target_height) / 2
        right = (new_width + target_width) / 2
        bottom = (new_height + target_height) / 2
        
        cropped_image = resized_image.crop((left, top, right, bottom))
        return cropped_image
    
    def process_single_image(self, image_path, product_name):
        """Обрабатывает одно изображение"""
        try:
            # Открываем изображение
            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Обрабатываем для каждого размера
                for size_name, dimensions in self.sizes.items():
                    # Создаем обработанное изображение
                    processed_img = self.resize_and_crop(img, dimensions)
                    
                    # Создаем имя файла
                    base_name = product_name.lower().replace(' ', '-')
                    output_filename = f"{base_name}-{size_name}.webp"
                    output_path = os.path.join(self.output_folder, output_filename)
                    
                    # Сохраняем в WebP с оптимизацией
                    processed_img.save(
                        output_path, 
                        'WEBP', 
                        quality=85,  # Оптимальное качество/размер
                        optimize=True
                    )
                    
                    print(f"✅ Создано: {output_filename} ({dimensions[0]}x{dimensions[1]})")
                    
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обработки {image_path}: {str(e)}")
            return False
    
    def auto_process_folder(self):
        """Автоматически обрабатывает все изображения в папке"""
        # Поддерживаемые форматы
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG']
        
        all_images = []
        for ext in extensions:
            all_images.extend(glob.glob(os.path.join(self.source_folder, ext)))
        
        if not all_images:
            print("📁 Не найдены изображения в папке 'original_images'")
            print("📸 Поместите ваши фото в папку 'backend/original_images/'")
            return
        
        print(f"🔄 Найдено {len(all_images)} изображений для обработки...")
        
        success_count = 0
        for image_path in all_images:
            # Создаем имя продукта из имени файла
            filename = os.path.basename(image_path)
            product_name = os.path.splitext(filename)[0]
            
            if self.process_single_image(image_path, product_name):
                success_count += 1
        
        print(f"\n🎉 Обработка завершена! Успешно: {success_count}/{len(all_images)}")
        
        # Показываем созданные файлы
        self.show_created_files()
    
    def show_created_files(self):
        """Показывает созданные файлы"""
        webp_files = glob.glob(os.path.join(self.output_folder, "*.webp"))
        if webp_files:
            print("\n📁 Созданные файлы:")
            for file in webp_files:
                file_size = os.path.getsize(file) / 1024  # размер в KB
                print(f"   📄 {os.path.basename(file)} ({file_size:.1f} KB)")
    
    def get_image_paths_for_api(self):
        """Возвращает пути для использования в API"""
        webp_files = glob.glob(os.path.join(self.output_folder, "*.webp"))
        product_data = {}
        
        for file_path in webp_files:
            filename = os.path.basename(file_path)
            # Извлекаем имя продукта и размер из имени файла
            parts = filename.replace('.webp', '').split('-')
            product_name = '-'.join(parts[:-1])  # все части кроме последней (размера)
            size = parts[-1]
            
            if product_name not in product_data:
                product_data[product_name] = {}
            
            # Сохраняем путь относительно фронтенда
            relative_path = f"/static/images/products/{filename}"
            product_data[product_name][size] = relative_path
        
        return product_data

# Функция для быстрого запуска
def process_images():
    processor = ImageProcessor()
    processor.auto_process_folder()
    
    # Показываем пути для API
    product_paths = processor.get_image_paths_for_api()
    if product_paths:
        print("\n🖼 Пути для использования в API:")
        for product, sizes in product_paths.items():
            print(f"\n📦 {product}:")
            for size, path in sizes.items():
                print(f"   {size}: '{path}'")

if __name__ == "__main__":
    process_images()