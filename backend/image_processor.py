import os
import re
from PIL import Image
import glob

class ImageProcessor:
    def __init__(self, source_folder="original_images", output_folder="../frontend/images/products"):
        self.source_folder = os.path.abspath(source_folder)
        self.output_folder = os.path.abspath(output_folder)
        self.sizes = {
            'small': (300, 300),   # для карточек товаров
            'large': (600, 600)    # для детальной страницы
        }

        os.makedirs(self.source_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

    def resize_and_crop(self, image: Image.Image, target_size):
        """Обрезает и изменяет размер изображения с сохранением пропорций (cover)."""
        try:
            original_width, original_height = image.size
            target_width, target_height = target_size

            ratio = max(target_width / original_width, target_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            left = int((new_width - target_width) / 2)
            top = int((new_height - target_height) / 2)
            right = left + target_width
            bottom = top + target_height

            cropped_image = resized_image.crop((left, top, right, bottom))
            return cropped_image

        except Exception as e:
            print(f"[ImageProcessor] Ошибка при изменении размера: {e}")
            return image.resize(target_size, Image.Resampling.LANCZOS)

    def clean_filename(self, filename: str):
        """Очищает имя файла от недопустимых символов и пробелов."""
        cleaned = re.sub(r'[^\w\s-]', '', filename)
        cleaned = re.sub(r'[-\s]+', '-', cleaned)
        return cleaned.strip().lower()

    def _ensure_rgb(self, img: Image.Image, background=(255,255,255)):
        """Если изображение с альфа-каналом, заливаем альфу белым фоном и конвертируем в RGB."""
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background_img = Image.new("RGB", img.size, background)
            img_conv = img.convert("RGBA")
            background_img.paste(img_conv, mask=img_conv.split()[3])
            return background_img
        if img.mode != 'RGB':
            return img.convert('RGB')
        return img

    def process_multiple_images(self, uploaded_files, product_name, product_id):
        """
        Обрабатывает несколько загруженных файлов.
        Возвращает список путей к обработанным изображениям.
        """
        try:
            image_paths = []
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Перемещаем указатель в начало
                uploaded_file.file.seek(0)

                with Image.open(uploaded_file.file) as img:
                    img = self._ensure_rgb(img)
                    
                    result_paths = {}
                    base_name = f"product-{product_id}-{i+1}"

                    for size_name, dimensions in self.sizes.items():
                        processed_img = self.resize_and_crop(img, dimensions)
                        output_filename = f"{base_name}-{size_name}.webp"
                        output_path = os.path.join(self.output_folder, output_filename)

                        processed_img.save(output_path, format='WEBP', quality=85, method=6)
                        relative_path = f"/static/images/products/{output_filename}"
                        result_paths[size_name] = relative_path

                        print(f"✅ Обработано изображение {i+1}: {output_filename}")

                    # Добавляем пути этого изображения в общий список
                    image_paths.append(result_paths)

            return image_paths

        except Exception as e:
            print(f"❌ Ошибка обработки нескольких изображений: {e}")
            return None

    def process_single_image(self, image_path, product_name, product_id=None):
        """Обрабатывает одно изображение с диска"""
        try:
            with Image.open(image_path) as img:
                img = self._ensure_rgb(img)
                result_paths = {}

                base_name = f"product-{product_id}" if product_id else self.clean_filename(product_name)

                for size_name, dimensions in self.sizes.items():
                    processed_img = self.resize_and_crop(img, dimensions)
                    output_filename = f"{base_name}-{size_name}.webp"
                    output_path = os.path.join(self.output_folder, output_filename)

                    processed_img.save(output_path, format='WEBP', quality=85, method=6)
                    relative_path = f"/static/images/products/{output_filename}"
                    result_paths[size_name] = relative_path

                    print(f"✅ Создано: {output_filename}")

                return result_paths

        except Exception as e:
            print(f"❌ Ошибка обработки {image_path}: {e}")
            return None

    def auto_process_folder(self):
        """Автоматически обрабатывает все изображения в source_folder"""
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG']
        all_images = []
        for ext in extensions:
            all_images.extend(glob.glob(os.path.join(self.source_folder, ext)))

        if not all_images:
            print("📁 Не найдены изображения в папке 'original_images'")
            return

        print(f"🔄 Найдено {len(all_images)} изображений для обработки...")
        success_count = 0
        for image_path in all_images:
            filename = os.path.basename(image_path)
            product_name = os.path.splitext(filename)[0]
            if self.process_single_image(image_path, product_name):
                success_count += 1

        print(f"\n🎉 Обработка завершена! Успешно: {success_count}/{len(all_images)}")
        self.show_created_files()

    def show_created_files(self):
        webp_files = glob.glob(os.path.join(self.output_folder, "*.webp"))
        if webp_files:
            print("\n📁 Созданные файлы:")
            for file in webp_files:
                file_size = os.path.getsize(file) / 1024
                print(f"   📄 {os.path.basename(file)} ({file_size:.1f} KB)")

# Глобальный экземпляр
image_processor = ImageProcessor()