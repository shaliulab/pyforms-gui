import os.path
import logging

import cv2
import imgstore

from cv2 import CAP_PROP_POS_FRAMES as POS_FRAMES


logger = logging.getLogger(__name__)

QUICK=True

class MultiFeedCapture:

    def __init__(self, resource):

        self._resource = resource
        self._synced = False

        if isinstance(resource, int):
            self._cap = cv2.VideoCapture(resource)
            self._store = None

        elif isinstance(resource, str):

            path = resource
            dirname = os.path.dirname(path)
            video_name = os.path.basename(path)
            lowres_path = os.path.join(dirname, "lowres", "metadata.yaml")
            self._chunk = int(os.path.basename(self._resource).split(".")[0])

            avi_files = sorted([file for file in os.listdir(dirname) if file[::-1][:4][::-1] == ".avi"])
            
            CHUNK_MAX = len(avi_files)

            if QUICK:
                chunk_numbers = list(range(max(0, self._chunk-10), min(CHUNK_MAX, self._chunk + 10), 1))
            else:
                chunk_numbers = None

            self._cap = cv2.VideoCapture(path)
            self._store = imgstore.new_for_filename(dirname, chunk_numbers=chunk_numbers)
            self._lowres_store = imgstore.new_for_filename(lowres_path, chunk_numbers=chunk_numbers)
            self._last_frame_in_chunk = 0


    def get(self, index):
        # something here with the imgstore
        return self._cap.get(index)


    def set(self, index, value):
        # something here with the imgstore
        if index == POS_FRAMES:
            self.sync_store(value)

        return self._cap.set(index, value)


    def compute_timestamp(self, frame_in_chunk):    
        index = int(min(
            len(self._store._get_chunk_metadata(self._chunk)["frame_time"])-1,
            frame_in_chunk
        ))

        timestamp = self._store._get_chunk_metadata(self._chunk)["frame_time"][index]
        return timestamp



    def sync_store(self, frame_in_chunk):
        """
        Sets the lowres store to the same timestamp as that of the frame just read
        using cv2
        """
        timestamp = self.compute_timestamp(frame_in_chunk)
        logger.debug(f"Syncing lowres store to timestamp {timestamp} - (frame {frame_in_chunk} in chunk {self._chunk})")
        img, (frame_number, timestamp_lowres) = self._lowres_store._get_image_by_time(timestamp)
        self._lowres_store.get_image(frame_number-1)
        self._last_frame_in_chunk = frame_in_chunk


    def release(self):
        self._cap.release()
        if self._store is not None:
            self._store.close()
            self._lowres_store.close()


    @staticmethod
    def annotate_img(img, label):

        pos = (int(img.shape[1] * 0.1), int(img.shape[0] * 0.9))
        if len(img.shape) == 2:
            nchannels = 1
        else:
            nchannels = img.shape[2]

        color = (200,) * nchannels

        img = cv2.putText(
            img,
            label,
            org=pos,
            fontFace=cv2.FONT_HERSHEY_PLAIN,
            fontScale=1,
            color=color,
            thickness=2,
            lineType=cv2.LINE_AA,
        ) 

        return img


    def show_extra(self, img, metadata, window=False):
        """
        Process the extra frames.
        Either show them in a new window or save them to a file
        """

        frame_number, frame_time = metadata

        img = self.annotate_img(img, f"Time: {frame_time} ms")

        if window:
            cv2.imshow(self._lowres_store.fullpath, img)
        else:
            cv2.imwrite("/tmp/python-video-annotator_extra-frame.png", img)

    def read(self):

        print("Reading new frame")
        status, frame = self._cap.read()


        frame_in_chunk = int(self._cap.get(1))

        if abs(frame_in_chunk - self._last_frame_in_chunk) == 1:
            timestamp = self.compute_timestamp(frame_in_chunk)
            self._lowres_store.view_store(timestamp)
        else:
            self.sync_store(frame_in_chunk)
            img, metadata = self._lowres_store.get_next_image()
            self.show_extra(img, metadata)
    
        # img = cv2.resize(img, frame.shape[:2][::-1], cv2.INTER_AREA)
        # frame = np.hstack([frame, img])
        return status, frame

