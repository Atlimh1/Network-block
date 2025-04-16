from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = [f"{h:02d}" for h in range(24)]

class ScheduleCell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Each cell is a tight 20×20 box.
        self.setFixedSize(25, 25)
        self.state = 0   # 0: empty; 1: full; 2: half

    def mousePressEvent(self, event):
        # Cycle through states: 0 → 1 → 2 → 0.
        self.state = (self.state + 1) % 3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Get the cell's rectangle and adjust it by 1 pixel on the right and bottom
        r = self.rect().adjusted(0, 0, -1, -1)

        # Draw a thin black border around the cell.
        pen = QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(r)

        # Determine fill color from parent's mode.
        # In this project: "blacklist" → green; "whitelist" → red.
        mode = getattr(self.parent(), "mode", "blacklist")
        color = QColor("green") if mode == "blacklist" else QColor("red")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))

        if self.state == 1:
            # Fill the entire cell.
            painter.drawRect(r)
        elif self.state == 2:
            # Half-cell fill: draw a triangle (from top-left to top-right to bottom-right)
            triangle = QPolygonF([r.topLeft(), r.topRight(), r.bottomRight()])
            painter.drawPolygon(triangle)
        # state 0: leave empty.

class ScheduleGridWidget(QWidget):
    """
    This widget separates the header from the schedule grid.
    
    It creates a 2×2 grid:
      - Top-left: a blank corner.
      - Top-right: a horizontal layout of hour labels.
      - Bottom-left: a vertical layout of day labels.
      - Bottom-right: the 7×24 schedule cells.
    
    The header areas have a white background and no grid lines drawn behind them.
    """
    def __init__(self, mode="blacklist", parent=None):
        super().__init__(parent)
        # You can adjust this fixed size if needed.
        self.setFixedSize(800, 300)
        self.mode = mode
        self.cells = {}

        mainLayout = QGridLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        # Top-left: Empty corner.
        corner = QLabel("")
        corner.setFixedSize(25, 25)
        mainLayout.addWidget(corner, 0, 0)

        # Top-right: Hour labels.
        hourWidget = QWidget()
        hourLayout = QHBoxLayout()
        hourLayout.setSpacing(0)
        hourLayout.setContentsMargins(0, 0, 0, 0)
        for hour in HOURS:
            label = QLabel(hour)
            label.setFixedSize(25, 25)
            label.setAlignment(Qt.AlignCenter)
            # Optionally, remove or adjust the white background style below
            # label.setStyleSheet("background-color: white;")
            hourLayout.addWidget(label)
        hourWidget.setLayout(hourLayout)
        mainLayout.addWidget(hourWidget, 0, 1)

        # Bottom-left: Day labels.
        dayWidget = QWidget()
        dayLayout = QVBoxLayout()
        dayLayout.setSpacing(0)
        dayLayout.setContentsMargins(0, 0, 0, 0)
        for day in DAYS:
            label = QLabel(day)
            label.setFixedSize(25, 25)
            label.setAlignment(Qt.AlignCenter)
            # label.setStyleSheet("background-color: white;")
            dayLayout.addWidget(label)
        dayWidget.setLayout(dayLayout)
        mainLayout.addWidget(dayWidget, 1, 0)

        # Bottom-right: The schedule grid (7 rows x 24 columns).
        cellWidget = QWidget()
        cellLayout = QGridLayout()
        cellLayout.setSpacing(0)
        cellLayout.setContentsMargins(0, 0, 0, 0)
        for row, day in enumerate(DAYS):
            for col, hour in enumerate(HOURS):
                cell = ScheduleCell(self)
                self.cells[(day, int(hour))] = cell
                cellLayout.addWidget(cell, row, col)
        cellWidget.setLayout(cellLayout)
        mainLayout.addWidget(cellWidget, 1, 1)

        self.setLayout(mainLayout)

    def get_schedule(self):
        """Returns a dictionary mapping 'Mon,0' -> state, etc."""
        schedule = {}
        for day in DAYS:
            for hour in range(24):
                schedule[f"{day},{hour}"] = self.cells[(day, hour)].state
        return schedule

    def set_schedule(self, schedule_dict):
        """Sets the cell states from a dictionary."""
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
        """Switch mode ('blacklist' or 'whitelist') and update all cells."""
        self.mode = mode
        for cell in self.cells.values():
            cell.update()

    def clear_all(self):
        """Resets all cells to empty (state = 0)."""
        for cell in self.cells.values():
            cell.state = 0
            cell.update()
