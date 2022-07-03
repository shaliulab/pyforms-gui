#!/usr/bin/python
# -*- coding: utf-8 -*-

""" pyforms_gui.controls.ControlPlayer.ControlPlayer

"""
__author__ = "Ricardo Ribeiro"
__credits__ = ["Ricardo Ribeiro"]
__license__ = "MIT"
__version__ = "0.0"
__maintainer__ = "Ricardo Ribeiro"
__email__ = "ricardojvr@gmail.com"
__status__ = "Development"

import codetiming
import logging, os, math
from AnyQt.QtWidgets import QStyle
from .multiple_videocapture import MultipleVideoCapture

try:
    import cv2
except:
    raise Exception('OpenCV is not available. ControlPlayer will not be working')


from confapp 	 import conf
from AnyQt 			 import uic, _api
from AnyQt 			 import QtCore
from AnyQt.QtWidgets import QFrame
from AnyQt.QtWidgets import QApplication
from AnyQt.QtWidgets import QMainWindow
from AnyQt.QtWidgets import QMessageBox

from pyforms_gui.controls.control_base import ControlBase

if _api.USED_API == _api.QT_API_PYQT5:
    import platform
    if platform.system() == 'Darwin':
        from pyforms_gui.controls.control_player.VideoQt5GLWidget import VideoQt5GLWidget as VideoGLWidget
    else:
        from pyforms_gui.controls.control_player.VideoGLWidget 	 import VideoGLWidget

elif _api.USED_API == _api.QT_API_PYQT4:
    from pyforms_gui.controls.control_player.VideoGLWidget 		 import VideoGLWidget

try:
    from imgstore.interface import VideoCapture
    TOTAL_NUMBER_OF_FRAMES="TOTAL_NUMBER_OF_FRAMES"
except:
    from cv2 import VideoCapture
    TOTAL_NUMBER_OF_FRAMES=7


logger = logging.getLogger(__name__)

class ControlPlayer(ControlBase, QFrame):

    def __init__(self, *args, **kwargs):
        self._video_widget = None  # GL widget

        QFrame.__init__(self)
        ControlBase.__init__(self, *args, **kwargs)

        self._multiple_files = kwargs.get('multiple_files', False)

        self._current_frame = None  # current frame image
        self._current_frame_index = None # current frame index

        self.process_frame_event = kwargs.get('process_frame_event', self.process_frame_event)

        self._speed = 1
        self.logger = logging.getLogger('pyforms')

        self._update_video_frame  = True # if true update the spinbox with the current frame
        self._update_video_slider = True  # if true update the slider with the current frame

        self._scroll_frames_action = self.add_popup_menu_option('Use scroll to move between frames', lambda x: x)
        self._scroll_frames_action.setCheckable(True)

    def __scroll_move_between_frames_evt(self):
        pass
        #self._scroll_frames_action.setIcon(QStyle.SP_DesktopIcon)

    def init_form(self):
        # Get the current path of the file
        rootPath = os.path.dirname(__file__)

        # Load the UI for the self instance
        uic.loadUi(os.path.join(rootPath, "video.ui"), self)


        # Define the icon for the Play button
        self.videoPlay.setIcon(conf.PYFORMS_ICON_VIDEOPLAYER_PAUSE_PLAY)
        self.detach_btn.setIcon(conf.PYFORMS_ICON_VIDEOPLAYER_DETACH)

        self.detach_btn.clicked.connect(self.__detach_player_evt)

        self._video_widget = VideoGLWidget()
        self._video_widget._control = self
        self.videoLayout.addWidget(self._video_widget)
        self.videoPlay.clicked.connect(self.videoPlay_clicked)
        self.videoFrames.valueChanged.connect(self.video_frames_value_changed)
        self.videoProgress.valueChanged.connect(self.videoProgress_valueChanged)
        self.videoProgress.sliderReleased.connect(self.videoProgress_sliderReleased)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.call_next_frame)

        self.form.horizontalSlider.valueChanged.connect(self.__rotateZ)
        self.form.verticalSlider.valueChanged.connect(self.__rotateX)

        self._current_frame = None

        self.view_in_3D = False



    ##########################################################################
    ############ FUNCTIONS ###################################################
    ##########################################################################

    def save_form(self, data, path=None):
        return data

    def load_form(self, data, path=None):
        pass

    def hide(self):
        QFrame.hide(self)

    def show(self):
        QFrame.show(self)

    def play(self):
        """
        Play the video.
        :return:
        """
        try:
            self.videoPlay.setChecked(True)
            self._timer.start( 1000.0/float(self.fps+1) )
        except Exception as e:
            self.videoPlay.setChecked(False)
            logger.error(e, exc_info=True)

    def stop(self):
        """
        Stop the video
        :return:
        """
        self.videoPlay.setChecked(False)
        self._timer.stop()

    def toggle_playing(self):
        """
        Play or pause the video.
        :return:
        """
        if self.is_playing:
            self.stop()
        else:
            self.play()

    def refresh(self):
        """
        Refresh the frame in the player.
        :return:
        """
        if self._current_frame is not None:
            frame = self.process_frame_event(self._current_frame.copy())
            if isinstance(frame, list) or isinstance(frame, tuple):
                self._video_widget.paint(frame)
            else:
                self._video_widget.paint([frame])
        else:
            self._video_widget.paint(None)

    def jump_forward(self):
        """
        Jump 20 seconds forward.
        :return:
        """
        self.video_index += 20 * self.fps
        self.call_next_frame()

    def jump_backward(self):
        """
        Jump 20 seconds backward.
        :return:
        """
        self.video_index -= 20 * self.fps
        self.call_next_frame()

    def back_one_frame(self):
        """
        Back one frame.
        :return:
        """
        self.video_index -= 2
        self.call_next_frame()

    def forward_one_frame(self):
        """
        Forward one frame.
        :return:
        """
        self.call_next_frame()


    def set_speed_1x(self):
        """
        Set video playing speed 1x.
        :return:
        """
        self.next_frame_step = 1
        self.video_widget.show_tmp_msg('Speed: 1x')

    def set_speed_2x(self):
        """
        Set video playing speed 2x.
        :return:
        """
        self.next_frame_step = 2
        self.video_widget.show_tmp_msg('Speed: 2x')

    def set_speed_3x(self):
        """
        Set video playing speed 3x.
        :return:
        """
        self.next_frame_step = 3
        self.video_widget.show_tmp_msg('Speed: 3x')

    def set_speed_4x(self):
        """
        Set video playing speed 4x.
        :return:
        """
        self.next_frame_step = 4
        self.video_widget.show_tmp_msg('Speed: 4x')

    def set_speed_5x(self):
        """
        Set video playing speed 5x.
        :return:
        """
        self.next_frame_step = 5
        self.video_widget.show_tmp_msg('Speed: 5x')

    def set_speed_6x(self):
        """
        Set video playing speed 6x.
        :return:
        """
        self.next_frame_step = 6
        self.video_widget.show_tmp_msg('Speed: 6x')

    def set_speed_7x(self):
        """
        Set video playing speed 7x.
        :return:
        """
        self.next_frame_step = 7
        self.video_widget.show_tmp_msg('Speed: 7x')

    def set_speed_8x(self):
        """
        Set video playing speed 8x.
        :return:
        """
        self.next_frame_step = 8
        self.video_widget.show_tmp_msg('Speed: 8x')

    def set_speed_9x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 9
        self.video_widget.show_tmp_msg('Speed: 9x')

    def set_speed_10x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 10
        self.video_widget.show_tmp_msg('Speed: 10x')

    def set_speed_20x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 20
        self.video_widget.show_tmp_msg('Speed: 20x')

    def set_speed_30x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 30
        self.video_widget.show_tmp_msg('Speed: 30x')

    def set_speed_40x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 40
        self.video_widget.show_tmp_msg('Speed: 40x')

    def set_speed_50x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 50
        self.video_widget.show_tmp_msg('Speed: 50x')

    def set_speed_60x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 60
        self.video_widget.show_tmp_msg('Speed: 60x')

    def set_speed_70x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 70
        self.video_widget.show_tmp_msg('Speed: 70x')

    def set_speed_80x(self):
        """
        Set video playing speed 9x.
        :return:
        """
        self.next_frame_step = 80
        self.video_widget.show_tmp_msg('Speed: 80x')

    def set_speed_90x(self):
        """
        Set video playing speed 90x.
        :return:
        """
        self.next_frame_step = 90
        self.video_widget.show_tmp_msg('Speed: 90x')


    ##########################################################################
    ############ EVENTS ######################################################
    ##########################################################################

    def process_frame_event(self, frame): return frame

    @property
    def double_click_event(self): return self._video_widget.onDoubleClick
    @double_click_event.setter
    def double_click_event(self, value): self._video_widget.onDoubleClick = value

    @property
    def click_event(self): return self._video_widget.onClick
    @click_event.setter
    def click_event(self, value):  self._video_widget.onClick = value

    @property
    def drag_event(self): return self._video_widget.onDrag
    @drag_event.setter
    def drag_event(self, value): self._video_widget.onDrag = value

    @property
    def end_drag_event(self): return self._video_widget.onEndDrag
    @end_drag_event.setter
    def end_drag_event(self, value): self._video_widget.onEndDrag = value

    @property
    def key_press_event(self):
        return self._video_widget.on_key_press
    @key_press_event.setter
    def key_press_event(self, value):
        self._video_widget.on_key_press = value

    @property
    def key_release_event(self): return self._video_widget.on_key_release
    @key_release_event.setter
    def key_release_event(self, value): self._video_widget.on_key_release = value

    ##########################################################################
    ############ PROPERTIES ##################################################
    ##########################################################################

    @property
    def video_widget(self): return self._video_widget

    @property
    def next_frame_step(self): return self._speed
    @next_frame_step.setter
    def next_frame_step(self, value): self._speed = value

    @property
    def view_in_3D(self): return self._video_widget.onEndDrag
    @view_in_3D.setter
    def view_in_3D(self, value):
        self.form.horizontalSlider.setVisible(value)
        self.form.verticalSlider.setVisible(value)

    @property
    def video_index(self):
        if self._value:
            # This self._value. query is OK
            return int(self._value.get(1))
        else:
            return None

    @video_index.setter
    def video_index(self, value):
        if value<0: value = 0
        if value>=self.max: value = self.max-1
        # This self._value. query is OK
        self._value.set(1, value)

    @property
    def max(self):
        if self._value is None or self._value=='':
            return 0

        # This self._value. query is OK
        return int(self._value.get(TOTAL_NUMBER_OF_FRAMES))

    @property
    def frame(self): return self._current_frame

    @frame.setter
    def frame(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self._video_widget.paint(value)
        elif value is not None:
            self._video_widget.paint([value])
        else:
            self._video_widget.paint(None)
        QApplication.processEvents()

    @property
    def fps(self):
        """
            Return the video frames per second
        """
        # This self._value. query is OK
        return self._value.get(5)

    @property
    def scroll_frames(self):
        return self._scroll_frames_action.isChecked()

    @property
    def help_text(self): return self._video_widget._helpText

    @help_text.setter
    def help_text(self, value): self._video_widget._helpText = value

    @property
    def form(self): return self

    @property
    def frame_width(self):
        # This self._value. query is OK
        return self._value.get(3)

    @property
    def frame_height(self):
        # This self._value. query is OK
        return self._value.get(4)

    @property
    def is_playing(self): return self._timer.isActive()

    @property
    def value(self): return ControlBase.value.fget(self)

    @property
    def multiple_files(self):
        return isinstance(self._value, MultipleVideoCapture)

    @value.setter
    def value(self, value):
        self.form.setUpdatesEnabled(False)
        if value is None:
            self.stop()
            self.videoControl.setEnabled(False)
            self.refresh()
        self._video_widget.reset()

        if value == 0:
            self._value = VideoCapture(0)
        elif isinstance(value, str) and value:

            open_multiplefiles = self._multiple_files

            if open_multiplefiles:
                open_multiplefiles = len(MultipleVideoCapture.search_files(value))>0

            if open_multiplefiles:
                msg = "Multiple files were found with the same folder, do you wish to combine then in a single video with the following order?\n\n"
                for filepath in MultipleVideoCapture.search_files(value):
                    msg += "- {filename}\n".format(filename=os.path.basename(filepath))

                reply = QMessageBox(
                    QMessageBox.Question,
                    'Open multiple files',
                    msg,
                    QMessageBox.No | QMessageBox.Yes
                ).exec_()

                if reply == QMessageBox.Yes:
                    open_multiplefiles = True
                else:
                    open_multiplefiles = False

            if open_multiplefiles:
                self._value = MultipleVideoCapture(value)
            else:
                self._value = VideoCapture(value)
        else:
            self._value = value

        if self._value and value != 0:
            self.videoProgress.setMinimum(0)
            self.videoProgress.setValue(0)
            self.videoProgress.setMaximum(
                # This self._value. query is OK
                self._value.get(TOTAL_NUMBER_OF_FRAMES))
            self.videoFrames.setMinimum(0)
            self.videoFrames.setValue(0)
            self.videoFrames.setMaximum(
                # This self._value. query is OK
                self._value.get(TOTAL_NUMBER_OF_FRAMES)
            )

        if self._value:
            self.videoControl.setEnabled(True)

        self.refresh()
        self.form.setUpdatesEnabled(True)


    ##########################################################################
    ############ PRIVATE FUNCTIONS ###########################################
    ##########################################################################

    def __rotateX(self):
        self._video_widget.rotateX = self.form.verticalSlider.value()
        self.refresh()

    def __rotateZ(self):
        self._video_widget.rotateZ = self.form.horizontalSlider.value()
        self.refresh()





    def call_next_frame(self, update_slider=True, update_number=True, increment_frame=True):
        # move the player to the next frame
        self.form.setUpdatesEnabled(False)

        self._current_frame_index = self.video_index

        # if the player is not visible, stop
        if not self.visible:
            self.stop()
            self.form.setUpdatesEnabled(True)
            return

        # if no video is selected
        if self.value is None:
            self._current_frame = None
            self._current_frame_index = None
            return

        # read next frame
        with codetiming.Timer(text="self.value.read took {:.8f} seconds", logger=logger.debug):
            (success, self._current_frame) = self.value.read()

        # increment frame index if the step is bigger than 1
        if increment_frame and self.next_frame_step > 1:
            self.video_index += self.next_frame_step

        # no frame available. leave the function
        if not success:
            self.stop()
            self.form.setUpdatesEnabled(True)
            return

        frame = self.process_frame_event(
            self._current_frame.copy()
        )

        # draw the frame
        if isinstance(frame, list) or isinstance(frame, tuple):
            self._video_widget.paint(frame)
        else:
            self._video_widget.paint([frame])

        if not self.videoProgress.isSliderDown():

            if update_slider and self._update_video_slider:
                self._update_video_slider = False
                self.videoProgress.setValue(self._current_frame_index)
                self._update_video_slider = True

            if update_number:
                self._update_video_frame = False
                self.videoFrames.setValue(self._current_frame_index)
                self._update_video_frame = True

        self.form.setUpdatesEnabled(True)


    def __detach_player_evt(self):
        """
        Called by the detach button
        """
        self._old_layout = self.parentWidget().layout()
        self._old_layout_index = self._old_layout.indexOf(self)
        self._detach_win = QMainWindow(parent=self.parent)
        self._detach_win.setWindowTitle('Player')
        self._detach_win.setCentralWidget(self)
        self.detach_btn.hide()
        self._detach_win.closeEvent = self.__detach_win_closed_evt
        self._detach_win.show()

    def __detach_win_closed_evt(self, event):
        """
        Called when the detached window is closed
        """
        self._old_layout.insertWidget(self._old_layout_index, self)
        self.detach_btn.show()
        self._detach_win.close()
        del self._detach_win

    def videoPlay_clicked(self):
        """Slot for Play/Pause functionality."""
        if self.is_playing:
            self.stop()
        else:
            self.play()

    def convertFrameToTime(self, totalMilliseconds):
        if math.isnan(totalMilliseconds): return 0, 0, 0
        totalseconds = int(totalMilliseconds / 1000)
        minutes = int(totalseconds / 60)
        seconds = totalseconds - (minutes * 60)
        milliseconds = totalMilliseconds - (totalseconds * 1000)
        return (minutes, seconds, milliseconds)

    def videoProgress_valueChanged(self):
        # This self._value. query is OK
        milli = self._value.get(0)
        (minutes, seconds, milliseconds) = self.convertFrameToTime(milli)
        self.videoTime.setText(
            "%02d:%02d:%03d" % (minutes, seconds, milliseconds))



    def videoProgress_sliderReleased(self):

        if not self.is_playing and self._update_video_slider:
            new_index = self.videoProgress.value()
            # This self._value. query is OK
            self._value.set(1, new_index)
            self.call_next_frame(update_slider=False, increment_frame=False)

    def video_frames_value_changed(self, pos):

        if not self.is_playing and self._update_video_frame:
            # This self._value. query is OK
            self._value.set(1, pos) # set the video position
            self.call_next_frame(update_number=False, increment_frame=False)

