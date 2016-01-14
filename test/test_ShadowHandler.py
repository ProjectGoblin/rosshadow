from unittest import TestCase
from rosshadow.shadow_api import GoblinShadowHandler


class TestGoblinShadowHandler(TestCase):
    def setUp(self):
        self.handler = GoblinShadowHandler('http://ros:11311', 2)

    def tearDown(self):
        self.handler._shutdown()

    def test_create(self):
        self.handler.lookupService('', '')
        self.assertTrue(self.handler.is_running())
