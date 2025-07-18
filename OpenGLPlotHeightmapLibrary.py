import sys
import numpy as np
from PIL import Image, ImageDraw
import moderngl
import glfw
from typing import Optional, Sequence, Dict, List
from line import ULine
import pandas as pd
from skimage.draw import line as sk_line

def check_execution_feasibility():
    print("Проверка теоретической возможности выполнения кода...")

    # Проверка наличия видеокарты
    try:
        import moderngl
        ctx = moderngl.create_standalone_context()
        renderer = ctx.info.get('GL_RENDERER', '')
        vendor = ctx.info.get('GL_VENDOR', '')
        if not renderer or not vendor:
            print("Ошибка: Не удалось определить видеокарту (рендерер или вендор не найдены).")
            ctx.release()
            return False
        print(f"Видеокарта: {vendor} {renderer}")
    except Exception as e:
        print(f"Ошибка при проверке видеокарты: {e}")
        return False

    # Проверка базовых требований OpenGL для ModernGL
    try:
        opengl_version = ctx.version_code
        print(f"Версия OpenGL: {opengl_version // 100}.{opengl_version % 100}")
        if opengl_version < 330:
            print("Ошибка: Требуется OpenGL версии 3.3 или выше.")
            ctx.release()
            return False
        ctx.release()
        print("OpenGL проверка пройдена.")
    except Exception as e:
        print(f"Ошибка при проверке OpenGL: {e}")
        return False

    # Проверка инициализации GLFW
    try:
        import glfw
        if not glfw.init():
            print("Ошибка: Не удалось инициализировать GLFW.")
            return False
        glfw.terminate()
        print("GLFW успешно инициализирован.")
    except Exception as e:
        print(f"Ошибка при проверке GLFW: {e}")
        return False

    print("Все проверки пройдены. Код теоретически может быть выполнен.")
    return True




def generate_initial_lines(weight, height, points_lines, intenses):
    image_array = np.zeros((height, weight), dtype=np.float32)

    for counter, points_line in enumerate(points_lines):
        for i in range(len(points_line) - 1):
            x0, y0 = int(points_line[i][0]), int(points_line[i][1])
            x1, y1 = int(points_line[i + 1][0]), int(points_line[i + 1][1])
            rr, cc = sk_line(y0, x0, y1, x1)  # skimage uses (row, col) = (y, x)
            image_array[rr, cc] = float(intenses[counter])  # значение может быть от 0.0 до 1.0

    return image_array


def generate_heightmap_using_GPU(weight, height, points_lines, intenses, iterations):
   if not glfw.init():
       raise Exception("GLFW init failed")
   glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
   window = glfw.create_window(weight, height, "Hidden", None, None)
   glfw.make_context_current(window)


   ctx = moderngl.create_context()
   # Инициализация
   data = generate_initial_lines(weight, height, points_lines, intenses)

   # Основные текстуры (ping-pong)
   tex_a = ctx.texture((weight, height), 1, data.tobytes(), dtype='f4')
   tex_b = ctx.texture((weight, height), 1, data.tobytes(), dtype='f4')
   tex_a.filter = tex_b.filter = (moderngl.NEAREST, moderngl.NEAREST)

   # Неизменяемая исходная карта
   source_lines = ctx.texture((weight, height), 1, data.tobytes(), dtype='f4')
   source_lines.filter = (moderngl.NEAREST, moderngl.NEAREST)

   fb_a = ctx.framebuffer(color_attachments=[tex_a])
   fb_b = ctx.framebuffer(color_attachments=[tex_b])

   # Шейдерная программа
   prog = ctx.program(
       vertex_shader="""
       #version 330
       in vec2 in_vert;
       out vec2 uv;
       void main() {
           uv = (in_vert + 1.0) / 2.0;
           gl_Position = vec4(in_vert, 0.0, 1.0);
       }
       """,
       fragment_shader=open("Shaders/shader.glsl").read()
   )


   # Квад для рендера на весь экран
   quad = ctx.buffer(np.array([
       -1, -1,  1, -1, -1,  1,
        1, -1,  1,  1, -1,  1,
   ], dtype='f4'))


   vao = ctx.simple_vertex_array(prog, quad, 'in_vert')


   # Назначение текстурных слотов
   tex_a.use(location=0)
   source_lines.use(location=1)
   prog['src'].value = 0
   prog['source_lines'].value = 1


   iterations = 1000
   for i in range(iterations):
       tex_a.use(location=0)
       source_lines.use(location=1)
       fb_b.use()
       vao.render(moderngl.TRIANGLES)
       tex_a, tex_b = tex_b, tex_a
       fb_a, fb_b = fb_b, fb_a

   result = np.frombuffer(tex_a.read(), dtype=np.float32).reshape((height, weight))
   image = Image.fromarray(result, mode='F')
   glfw.terminate()
   return image
