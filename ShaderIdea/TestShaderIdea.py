import numpy as np
from PIL import Image
import moderngl
import glfw

W, H = 512, 512

def generate_initial_lines():
    # Простая тестовая карта: горизонтальные линии разной "высоты"
    img = np.zeros((H, W), dtype=np.float32)
    for i in range(5):
        y = int((i + 1) * H / 6)
        img[y-1:y+1] = i * 0.2  # высоты: 0.2, 0.4, 0.6, ...
    return img

def main():
    if not glfw.init():
        raise Exception("GLFW init failed")
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(W, H, "Hidden", None, None)
    glfw.make_context_current(window)

    ctx = moderngl.create_context()

    # Инициализация
    data = generate_initial_lines()

    # Основные текстуры (ping-pong)
    tex_a = ctx.texture((W, H), 1, data.tobytes(), dtype='f4')
    tex_b = ctx.texture((W, H), 1, data.tobytes(), dtype='f4')
    tex_a.filter = tex_b.filter = (moderngl.NEAREST, moderngl.NEAREST)

    # Неизменяемая исходная карта
    source_lines = ctx.texture((W, H), 1, data.tobytes(), dtype='f4')
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
        fragment_shader=open("shader.glsl").read()
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

    # Считываем результат
    result = np.frombuffer(tex_a.read(), dtype=np.float32).reshape((H, W))
    Image.fromarray((result * 255).astype(np.uint8)).save("result.png")

    glfw.terminate()

if __name__ == '__main__':
    main()

