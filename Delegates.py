class UDelegate:
    def __init__(self):
        self._callbacks = []

    def add(self, callback):
        if callable(callback):
            if not callback in self._callbacks:
             self._callbacks.append(callback)

    def remove(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def invoke(self, *args, **kwargs):
        for callback in self._callbacks:
            callback(*args, **kwargs)