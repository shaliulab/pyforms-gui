import unittest
import os.path
import os
os.environ["TESTING"] = "True"

from AnyQt.QtWidgets import QApplication

from pyforms_gui.controls.control_player.control_player import ControlPlayer
from pyforms_gui.tests import TEST_DATA_DIR
from pyforms.basewidget import BaseWidget


HR_STORE_PATH = os.path.join(TEST_DATA_DIR, "imgstore_1", "metadata.yaml")
LR_STORE_PATH = os.path.join(TEST_DATA_DIR, "imgstore_1", "lowres", "metadata.yaml")

import cv2
import tempfile


tempfolder = tempfile.TemporaryDirectory()
print(tempfolder)

def process_frame_event(frame):
    cv2.imwrite(os.path.join(tempfolder.name, "frame.png"), frame)
    return frame

class TestControlPlayer(unittest.TestCase):

    def setUp(self):
        
        
        self._player = ControlPlayer(
            "Player", enabled=True, visible=True, multiple_files=False
        )

    def test_imgstore_input(self):

        self._player.value = [
            HR_STORE_PATH,
            LR_STORE_PATH
        ]

        self._player.process_frame_event = process_frame_event
        #self._player.forward_one_frame()
        self._player.video_index=20
        self._player.call_next_frame()
        
        current_frame = self._player._current_frame
        frame = cv2.cvtColor(
            cv2.imread(os.path.join(
                tempfolder.name,
                "frame.png"
            )), cv2.COLOR_BGR2GRAY
        )
        self.assertTrue((frame - current_frame).mean() == 0)

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

