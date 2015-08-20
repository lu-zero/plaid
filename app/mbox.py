## Monkeypatch mbox to be able to use directly a file

from mailbox import mbox, mboxMessage

def __file_init__(self, fp):
    self._message_factory = mboxMessage
    self._factory = None
    self._path = None
    self._file_length = None
    self._locked = False
    self._pending_sync = False
    self._pending = False
    self._next_key = 0
    self._toc = None
    self._file = fp

mbox.__init__ = __file_init__
