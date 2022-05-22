import tensorflow as tf
from PIL import Image


def show_image_buffer(buf):
    im = Image.open(buf)
    im.show()
    buf.close()


def init_tf():
    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
