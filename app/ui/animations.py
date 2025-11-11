from PySide6.QtCore import QPropertyAnimation, QEasingCurve

def fade_in(widget, ms=180):
    widget.setWindowOpacity(0.0)
    anim = QPropertyAnimation(widget, b"windowOpacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.InOutQuad)
    anim.start()
    _stash(widget, anim)

def slide_in_y(widget, start_y_delta=16, ms=220):
    geo = widget.geometry()
    anim = QPropertyAnimation(widget, b"geometry", widget)
    anim.setDuration(ms)
    anim.setStartValue(geo.adjusted(0, start_y_delta, 0, start_y_delta))
    anim.setEndValue(geo)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()
    _stash(widget, anim)

def _stash(widget, anim):
    if not hasattr(widget, "_anims"): widget._anims = []
    widget._anims.append(anim)
    if len(widget._anims) > 24: widget._anims.pop(0)
