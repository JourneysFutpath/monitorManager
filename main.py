import subprocess
import json
import os
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton, QVBoxLayout, QWidget

# Get the list of connected screens using xrandr
def get_connected_screens():
    screens = []
    try:
        xrandr_output = subprocess.check_output("xrandr", shell=True).decode("utf-8").strip().split("\n")
        for line in xrandr_output:
            if " connected" in line:
                parts = line.split()
                screen_name = parts[0]
                resolution = parts[3] if len(parts) > 3 else "1920x1080"
                screens.append({
                    "name": screen_name,
                    "connected": True,
                    "resolution": resolution,
                    "rotation": "normal",  # Default rotation
                    "pos_x": 100,  # Default position
                    "pos_y": 100,  # Default position
                })
    except subprocess.CalledProcessError as e:
        print("Error retrieving screen configuration:", e)
    return screens

# Helper function to apply a batch of xrandr commands in one go
def apply_batch_xrandr(screens):
    cmd = []
    for screen in screens:
        cmd.append(f"--output {screen['name']} --mode {screen['resolution']} --rotate {screen['rotation']}")
        cmd.append(f"--output {screen['name']} --pos {screen['pos_x']}x{screen['pos_y']}")
    subprocess.run(f"xrandr {' '.join(cmd)}", shell=True)

# Function to save the layout to a file in a secure location
def save_layout(screens, file_name="~/monitor-layout.json"):
    layout_data = []
    for screen in screens:
        layout_data.append({
            "name": screen['name'],
            "pos_x": screen['pos_x'],
            "pos_y": screen['pos_y'],
            "resolution": screen['resolution'],
            "rotation": screen['rotation']
        })
    
    layout_path = os.path.expanduser(file_name)  # Expands the ~ to the full user path
    with open(layout_path, 'w') as file:
        json.dump(layout_data, file, indent=4)

# Function to load layout from a secure file
def load_layout(file_name="~/monitor-layout.json"):
    layout_path = os.path.expanduser(file_name)
    try:
        with open(layout_path, 'r') as file:
            layout_data = json.load(file)
        return layout_data
    except (FileNotFoundError, json.JSONDecodeError):
        print("No saved layout found or error reading the layout.")
        return []

# Function to reset layout to defaults
def reset_layout(screens):
    for screen in screens:
        subprocess.run(f"xrandr --output {screen['name']} --auto", shell=True)
        subprocess.run(f"xrandr --output {screen['name']} --rotate normal", shell=True)

# Background thread for handling xrandr operations
class MonitorConfigurator(QThread):
    progress = pyqtSignal(str)

    def __init__(self, screens):
        super().__init__()
        self.screens = screens

    def run(self):
        try:
            apply_batch_xrandr(self.screens)
            self.progress.emit("Configuration complete!")
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")

# GUI for managing monitor layout
class MonitorItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height, name):
        super().__init__(x, y, width, height)
        self.setBrush(QBrush(Qt.blue))
        self.name = name
        self.setFlag(QGraphicsRectItem.ItemIsMovable)

    def mousePressEvent(self, event):
        self.setFlag(QGraphicsRectItem.ItemIsMovable)

    def mouseReleaseEvent(self, event):
        self.setFlag(QGraphicsRectItem.ItemIsMovable)

class MonitorLayout(QGraphicsView):
    def __init__(self, monitors):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setScene(QGraphicsScene(self))

        self.monitor_items = []
        self.monitors = monitors
        
        # Create draggable monitor items
        for monitor in monitors:
            monitor_item = MonitorItem(monitor['pos_x'], monitor['pos_y'], 150, 100, monitor['name'])
            self.scene().addItem(monitor_item)
            self.monitor_items.append(monitor_item)

    def set_layout(self, monitors):
        for monitor_item, monitor in zip(self.monitor_items, monitors):
            monitor_item.setPos(monitor['pos_x'], monitor['pos_y'])

    def save_layout(self):
        # Save the layout to file
        for monitor_item, monitor in zip(self.monitor_items, self.monitors):
            monitor['pos_x'], monitor['pos_y'] = monitor_item.x(), monitor_item.y()
        save_layout(self.monitors)

    def reset_layout(self):
        # Reset layout to defaults
        reset_layout(self.monitors)
        for monitor_item, monitor in zip(self.monitor_items, self.monitors):
            monitor_item.setPos(monitor['pos_x'], monitor['pos_y'])

    def load_layout(self):
        # Load saved layout
        layout_data = load_layout()
        if layout_data:
            for monitor_data, monitor in zip(layout_data, self.monitors):
                monitor['pos_x'], monitor['pos_y'] = monitor_data['pos_x'], monitor_data['pos_y']
                monitor['resolution'], monitor['rotation'] = monitor_data['resolution'], monitor_data['rotation']
            self.set_layout(self.monitors)

def run_gui():
    monitors = get_connected_screens()
    app = QApplication([])
    
    layout = MonitorLayout(monitors)
    
    layout_buttons = QWidget()
    layout_buttons.setFixedSize(800, 100)
    layout_buttons_layout = QVBoxLayout()
    
    save_button = QPushButton("Save Layout")
    save_button.clicked.connect(lambda: layout.save_layout())
    
    load_button = QPushButton("Load Layout")
    load_button.clicked.connect(lambda: layout.load_layout())
    
    reset_button = QPushButton("Reset Layout")
    reset_button.clicked.connect(lambda: layout.reset_layout())
    
    layout_buttons_layout.addWidget(save_button)
    layout_buttons_layout.addWidget(load_button)
    layout_buttons_layout.addWidget(reset_button)
    
    layout_buttons.setLayout(layout_buttons_layout)
    
    layout_layout = QVBoxLayout()
    layout_layout.addWidget(layout)
    layout_layout.addWidget(layout_buttons)
    
    main_window = QWidget()
    main_window.setLayout(layout_layout)
    main_window.setFixedSize(800, 700)
    main_window.show()
    
    # Launch xrandr configuration in the background
    configurator = MonitorConfigurator(monitors)
    configurator.progress.connect(lambda msg: print(msg))  # Log progress or update status
    configurator.start()
    
    app.exec_()

if __name__ == "__main__":
    run_gui()

