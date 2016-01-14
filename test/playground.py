from rosshadow.shadow import Shadow
from xmlrpclib import ServerProxy


class Playground:
    def __init__(self):
        self.shadow = Shadow(master_uri='http://ros:11311', num_workers=2)
        self.shadow.start()
        self.client = ServerProxy('http://localhost:11411')

    def run(self):
        print(self.client.lookupService('~Playground', '/rosout'))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shadow.stop()


if __name__ == '__main__':
    with Playground() as playground:
        playground.run()
