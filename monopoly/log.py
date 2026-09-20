""" Class to keep a log of the game.
The challenge here was to make it thread-safe: simulator plays several games at a time,
but the game log should be written by "whole game" chunks. This is the reason games
will not be in order, as the order games start is different from the order they finish.

Fixed: Uses a shared managed lock passed from the main process to ensure
correct cross-process synchronization on Windows (which uses 'spawn').
"""

from os import PathLike
from typing import Union, Optional
import multiprocessing


class Log:
    """ Class to handle logging of game events.
    The lock must be set via Log.set_lock() from the main process
    and worker initializer to enable cross-process file safety.
    """
    # Shared lock — set externally by the simulation runner
    _lock: Optional[multiprocessing.Lock] = None

    @classmethod
    def set_lock(cls, lock):
        """Set the shared lock for cross-process log file safety.
        Must be called from the main process and from each worker's initializer.
        """
        cls._lock = lock

    def __init__(self, log_file_name: Union[str, PathLike] = "log.txt", disabled: bool = False):
        self.log_file_name = log_file_name
        self.content = []
        self.disabled = disabled

    def add(self, data):
        """ Add a line to a Log
        """
        if self.disabled:
            return
        self.content.append(data)

    def save(self):
        """ Write out the log
        """
        if self.disabled:
            return

        lock = self._lock
        if lock is not None:
            lock.acquire()
        try:
            with open(self.log_file_name, "a", encoding="utf-8") as logfile:
                logfile.write("\n".join(self.content))
                if self.content:
                    logfile.write("\n")
        finally:
            if lock is not None:
                lock.release()

    def reset(self, first_line=""):
        """ Empty the log file, write first_line if provided
        """
        lock = self._lock
        if lock is not None:
            lock.acquire()
        try:
            with open(self.log_file_name, "w", encoding="utf-8") as logfile:
                logfile.write(f"{first_line}\n")
        finally:
            if lock is not None:
                lock.release()
