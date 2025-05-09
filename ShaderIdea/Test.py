import sys

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

if __name__ == '__main__':
    check_execution_feasibility()