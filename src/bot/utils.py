import json
from typing import Any

import tensorflow as tf
from PIL import Image
from starlette.responses import Response


def show_image_buffer(buf):
    im = Image.open(buf)
    im.show()
    buf.close()


def init_tf():
    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(content, ensure_ascii=True, indent=1).encode("utf-8")
