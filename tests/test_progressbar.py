import time
import unittest

from gnes.client.cli import ProgressBar


class TestProgessbar(unittest.TestCase):
    def setUp(self):
        self.bar_len = 20

    def test_progressbar5(self):
        # should be 5 line
        with ProgressBar(task_name='test', bar_len=self.bar_len) as pb:
            for j in range(5 * self.bar_len):
                pb.update()
                time.sleep(.05)

    def test_progressbar1(self):
        # should be single line
        with ProgressBar(task_name='test', bar_len=self.bar_len) as pb:
            for j in range(self.bar_len):
                pb.update()
                time.sleep(.05)
