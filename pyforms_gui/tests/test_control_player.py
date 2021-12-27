import unittest
import os.path

from AnyQt.QtWidgets import QApplication

from pyforms_gui.controls.control_player.control_player import ControlPlayer
from pyforms_gui.tests import TEST_DATA_DIR
from pyforms.basewidget import BaseWidget


HR_STORE_PATH = os.path.join(TEST_DATA_DIR, "imgstore_1", "metadata.yaml")
LR_STORE_PATH = os.path.join(TEST_DATA_DIR, "imgstore_1", "lowres", "metadata.yaml")


class TestControlPlayer(unittest.TestCase):

    def setUp(self):
        
        
        self._player = ControlPlayer(
            "Player", enabled=False, multiple_files=True
        )

    def test_imgstore_input(self):

        self._player.value = [
            HR_STORE_PATH,
            LR_STORE_PATH
        ]
        self.formset = ([("_player")])        

def main():
    
    app = QApplication([])    
    
    from pyforms_gui import resources_settings
    from confapp import conf
    conf += resources_settings

    unittest.main()
    # test = TestControlPlayer()
    # test.init_form()


if __name__ == "__main__":
    main()

