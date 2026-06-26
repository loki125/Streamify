from PyQt5.QtCore import QObject, pyqtSignal


class SignalEmitter(QObject):
    """Signals to safely interact with the UI from background threads."""

    status_updated = pyqtSignal(object, str)
    check_finished = pyqtSignal()
