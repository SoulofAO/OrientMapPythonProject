import time
import random
from PIL import Image, ImageFilter
from concurrent.futures import ThreadPoolExecutor

def generate_random_image(width, height):
    """Создаем изображение с случайными пикселями."""
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for x in range(width):
        for y in range(height):
            pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    return image

def process_block(image, left, upper, right, lower):
    """Применение двух фильтров к указанному блоку изображения для увеличения сложности."""
    block = image.crop((left, upper, right, lower))
    # Применяем сначала размытие, затем повышение резкости
    block = block.filter(ImageFilter.GaussianBlur(5))
    block = block.filter(ImageFilter.SHARPEN)
    image.paste(block, (left, upper))

def process_image_sequential(image):
    """Последовательная обработка всех блоков изображения."""
    width, height = image.size
    block_size = 100
    for left in range(0, width, block_size):
        for upper in range(0, height, block_size):
            right = min(left + block_size, width)
            lower = min(upper + block_size, height)
            process_block(image, left, upper, right, lower)
    return image

def process_image_parallel(image, num_threads=8):
    """Параллельная обработка всех блоков изображения с использованием нескольких потоков."""
    width, height = image.size
    block_size = 100
    blocks = [(image, left, upper, min(left + block_size, width), min(upper + block_size, height))
              for left in range(0, width, block_size)
              for upper in range(0, height, block_size)]

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(lambda args: process_block(*args), blocks)
    return image

# Генерация случайного изображения 2000x2000
width, height = 2000, 2000
image_sequential = generate_random_image(width, height)
image_parallel = image_sequential.copy()



# Замер времени для параллельной обработки с 8 потоками
start_time = time.time()
process_image_parallel(image_parallel, num_threads=8)
parallel_time = time.time() - start_time
print(f"Время параллельной обработки с 8 потоками: {parallel_time:.2f} секунд")


# Замер времени для последовательной обработки
start_time = time.time()
process_image_sequential(image_sequential)
sequential_time = time.time() - start_time
print(f"Время последовательной обработки: {sequential_time:.2f} секунд")
