from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = [f"{h:02d}" for h in range(24)]

class ScheduleCell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(25, 25)
        self.state = 0   # 0: empty; 1: full; 2: half

    def mousePressEvent(self, event):
        self.state = (self.state + 1) % 3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        r = self.rect().adjusted(0, 0, -1, -1)

        # Draw border
        pen = QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(r)

        # Fill color depends on mode
        mode = getattr(self.parent(), "mode", "blacklist")
        color = QColor("green") if mode == "blacklist" else QColor("red")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))

        if self.state == 1:
            painter.drawRect(r)
        elif self.state == 2:
            triangle = QPolygonF([r.topLeft(), r.topRight(), r.bottomRight()])
            painter.drawPolygon(triangle)

class ScheduleGridWidget(QWidget):
    def __init__(self, mode="blacklist", parent=None):
        super().__init__(parent)
        self.setFixedSize(800, 300)
        self.mode = mode
        self.cells = {}

        mainLayout = QGridLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        # Top-left: blank
        corner = QLabel("")
        corner.setFixedSize(25, 25)
        mainLayout.addWidget(corner, 0, 0)

        # Hour headers
        hourWidget = QWidget()
        hourLayout = QHBoxLayout(hourWidget)
        hourLayout.setSpacing(0)
        hourLayout.setContentsMargins(0, 0, 0, 0)
        for hour in HOURS:
            label = QLabel(hour)
            label.setFixedSize(25, 25)
            label.setAlignment(Qt.AlignCenter)
            hourLayout.addWidget(label)
        mainLayout.addWidget(hourWidget, 0, 1)

        # Day headers
        dayWidget = QWidget()
        dayLayout = QVBoxLayout(dayWidget)
        dayLayout.setSpacing(0)
        dayLayout.setContentsMargins(0, 0, 0, 0)
        for day in DAYS:
            label = QLabel(day)
            label.setFixedSize(25, 25)
            label.setAlignment(Qt.AlignCenter)
            dayLayout.addWidget(label)
        mainLayout.addWidget(dayWidget, 1, 0)

        # Schedule cells
        cellWidget = QWidget()
        cellLayout = QGridLayout(cellWidget)
        cellLayout.setSpacing(0)
        cellLayout.setContentsMargins(0, 0, 0, 0)
        for row, day in enumerate(DAYS):
            for col, hour in enumerate(HOURS):
                cell = ScheduleCell(self)
                self.cells[(day, int(hour))] = cell
                cellLayout.addWidget(cell, row, col)
        mainLayout.addWidget(cellWidget, 1, 1)

        self.setLayout(mainLayout)

    def get_schedule(self):
        schedule = {}
        for day in DAYS:
            for hour in range(24):
                schedule[f"{day},{hour}"] = self.cells[(day, hour)].state
        return schedule

    def set_schedule(self, schedule_dict):
        for key, state in schedule_dict.items():
            try:
                day, hour = key.split(",")
                hour = int(hour)
                if (day, hour) in self.cells:
                    self.cells[(day, hour)].state = state
                    self.cells[(day, hour)].update()
            except Exception:
                continue

    def set_mode(self, mode):
        self.mode = mode
        for cell in self.cells.values():
            cell.update()

    def clear_all(self):
        for cell in self.cells.values():
            cell.state = 0
            cell.update()
