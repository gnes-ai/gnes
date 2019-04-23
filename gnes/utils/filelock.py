import os
import fcntl


class FileLock(object):
    """
    Implements the Posix based file locking (Linux, Ubuntu, MacOS, etc.)
    """

    def __init__(self, lock_file: str = "LOCK"):
        self._lock_file = lock_file
        self._lock_file_fd = None

    @property
    def is_locked(self):
        return self._lock_file_fd is not None

    def acquire(self):
        open_mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        fd = os.open(self._lock_file, open_mode)

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_file_fd = fd
        except (IOError, OSError):
            os.close(fd)

    def release(self):
        fd = self._lock_file_fd
        self._lock_file_fd = None
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
