import ctypes
import sys, os, colorsys, math
import tkinter as tk
from pynput import mouse
from PIL import ImageGrab, ImageTk, Image

class AdvancedColorPicker:
    SIZE = 250
    PADDING = 12
    SLIDER_WIDTH = 30
    SLIDER_INDICATOR_HEIGHT = 2
    INDICATOR_RADIUS = 6

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Color Picker")
        self.root.geometry("660x300")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.example.ColorPicker")

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass

        # Shared state
        self.hex_var = tk.StringVar(value="#FFFFFF")
        self.r_var = tk.StringVar(value="255")
        self.g_var = tk.StringVar(value="255")
        self.b_var = tk.StringVar(value="255")

        self.hue = 0
        self.sat = 0
        self.val = 1.0

        # Layout
        self.left = tk.Frame(root)
        self.left.pack(side="left", padx=(50,10), pady=10)
        self.right = tk.Frame(root)
        self.right.pack(side="right", padx=(10,50), pady=10)

        # HSV wheel
        self.CENTER = self.SIZE // 2
        self.RADIUS = self.CENTER - self.PADDING

        self.wheel = tk.Canvas(self.left, width=self.SIZE, height=self.SIZE, highlightthickness=0)
        self.wheel.pack(side="left")
        self.slider = tk.Canvas(self.left, width=self.SLIDER_WIDTH, height=self.SIZE, highlightthickness=0)
        self.slider.pack(side="right", padx=20)

        self._draw_wheel()
        self.indicator = self.wheel.create_oval(
            self.CENTER-self.INDICATOR_RADIUS,
            self.CENTER-self.INDICATOR_RADIUS,
            self.CENTER+self.INDICATOR_RADIUS,
            self.CENTER+self.INDICATOR_RADIUS,
            outline="black", width=2
        )

        # Right UI
        self.title = tk.Label(self.right, text="Right-click anywhere on screen", width=30, font=("Arial", 12))
        self.title.pack(pady=5)

        self.preview = tk.Label(self.right, width=18, height=3, bg="#FFFFFF", bd=2, relief="solid")
        self.preview.pack(pady=10)

        self.hex_label = tk.Label(self.right, textvariable=self.hex_var, font=("Arial", 16, "bold"))
        self.hex_label.pack(pady=5)

        self.copy_btn = tk.Button(
            self.right, text="Copy HEX", width=18, font=("Arial", 12), relief="solid",
            command=self.copy_color
        )
        self.copy_btn.pack(pady=8)

        self.rgb_frame = tk.Frame(self.right)
        self.rgb_frame.pack(pady=5)
        self._rgb_entry("R", self.r_var)
        self._rgb_entry("G", self.g_var)
        self._rgb_entry("B", self.b_var)

        # Bindings
        self.wheel.bind("<Button-1>", self.handle_wheel)
        self.wheel.bind("<B1-Motion>", self.handle_wheel)
        self.slider.bind("<Button-1>", self.handle_slider)
        self.slider.bind("<B1-Motion>", self.handle_slider)

        # Mouse listener
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()

        # Load icon
        try:
            self.ICON_IMG = self.pil_img("images/icon.png", (32,32))
            root.iconphoto(False, self.ICON_IMG)
        except Exception as e:
            print("Failed to load icon:", e)

        self.draw_slider()
        self.update_color()

    # ---------------- Helpers ----------------
    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        full_path = os.path.join(base_path, relative_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Resource not found: {full_path}")
        return full_path

    def pil_img(self, path, size=None):
        im = Image.open(self.resource_path(path)).convert("RGBA")
        if size:
            im = im.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(im)

    def _rgb_entry(self, label, var):
        f = tk.Frame(self.rgb_frame)
        f.pack(side="left", padx=5)
        tk.Label(f, text=label, font=("Arial", 10, "bold")).pack()
        e = tk.Entry(f, width=5, textvariable=var, justify="center")
        e.pack()
        e.configure(state="readonly")

    # ---------------- Drawing ----------------
    def _draw_wheel(self):
        for y in range(self.SIZE):
            for x in range(self.SIZE):
                dx = x - self.CENTER
                dy = y - self.CENTER
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= self.RADIUS:
                    s = dist / self.RADIUS
                    h = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                    r, g, b = colorsys.hsv_to_rgb(h, s, 1)
                    self.wheel.create_line(
                        x, y, x+1, y,
                        fill=f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                    )

    def draw_slider(self):
        self.slider.delete("all")
        for y in range(self.SIZE):
            v = 1 - y / self.SIZE
            r, g, b = colorsys.hsv_to_rgb(self.hue, self.sat, v)
            self.slider.create_line(
                0, y, self.SLIDER_WIDTH, y,
                fill=f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            )
        indicator_y = int((1 - self.val) * self.SIZE)
        self.slider.create_rectangle(
            0,
            indicator_y - self.SLIDER_INDICATOR_HEIGHT,
            self.SLIDER_WIDTH,
            indicator_y + self.SLIDER_INDICATOR_HEIGHT,
            fill="black", outline=""
        )

    def move_indicator(self, x, y):
        self.wheel.coords(
            self.indicator,
            x-self.INDICATOR_RADIUS, y-self.INDICATOR_RADIUS,
            x+self.INDICATOR_RADIUS, y+self.INDICATOR_RADIUS
        )

    # ---------------- Event Handlers ----------------
    def handle_wheel(self, event):
        dx = event.x - self.CENTER
        dy = event.y - self.CENTER
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > self.RADIUS:
            dx *= self.RADIUS / dist
            dy *= self.RADIUS / dist
            dist = self.RADIUS

        self.sat = dist / self.RADIUS
        self.hue = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)

        self.move_indicator(self.CENTER + dx, self.CENTER + dy)
        self.draw_slider()
        self.update_color()

    def handle_slider(self, event):
        self.val = max(0, min(1, 1 - event.y / self.SIZE))
        self.draw_slider()
        self.update_color()

    def copy_color(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.hex_var.get())
        self.root.update_idletasks()
        self.title.config(text="Copied ✔")
        self.root.after(1200, lambda: self.title.config(text="Right-click anywhere on screen"))

    # ---------------- Screen Picker ----------------
    def get_color(self, x, y):
        img = ImageGrab.grab()
        r, g, b = img.getpixel((x, y))
        self.set_from_rgb(r, g, b)

    def on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.right:
            self.root.after(0, self.get_color, x, y)

    def set_from_rgb(self, r, g, b):
        self.hue, self.sat, self.val = colorsys.rgb_to_hsv(r/255, g/255, b/255)

        angle = self.hue * 2 * math.pi - math.pi
        dist = self.sat * self.RADIUS
        cx = self.CENTER + math.cos(angle) * dist
        cy = self.CENTER + math.sin(angle) * dist

        self.move_indicator(cx, cy)
        self.draw_slider()
        self.update_color()

    # ---------------- Update Color ----------------
    def update_color(self):
        r, g, b = colorsys.hsv_to_rgb(self.hue, self.sat, self.val)
        R, G, B = int(r*255), int(g*255), int(b*255)
        hex_color = f"#{R:02X}{G:02X}{B:02X}"
        self.hex_var.set(hex_color)
        self.preview.config(bg=hex_color)
        self.r_var.set(str(R))
        self.g_var.set(str(G))
        self.b_var.set(str(B))


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedColorPicker(root)
    root.mainloop()
