from pathlib import Path

from locust import HttpUser, task


b = Path('/workspace/EECS 6414/voice_cnn/test.wav').read_bytes()


class HelloWorldUser(HttpUser):
    @task
    def hello_world(self):
        files = {'file': b}
        r = self.client.post('/process', files=files)
