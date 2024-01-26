import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import ttkbootstrap as ttk
from PIL import Image, ImageTk

from image_info import ImageInfo
from configs import configure_logging, logs_folder

LOG_FILE = logs_folder / "logs.txt"


class InfoWindow(ttk.Toplevel):
    def __init__(self, image_info, info_needed, master=None):
        super().__init__(master)
        self.title(info_needed)
        self.geometry('300x150')

        self.image_info = image_info
        self.info_needed = info_needed
        self.is_open = False

        self.create_widgets()

    def create_widgets(self):
        info_text = {
            "Date taken": f"{self.image_info.date_taken}",
            "Location": f"""
                Coordinates:
                {self.image_info.coordinates}
                Address:
                {self.image_info.address}""",
            "Device used": f"""
                Make: {self.image_info.device_make}
                Model: {self.image_info.device_model}"""
        }.get(self.info_needed)

        view_map_frame = ttk.Frame(self)
        view_map_frame.pack(side='bottom')

        info_label = ttk.Label(self, text=info_text, justify=ttk.LEFT)
        info_label.pack()

        if self.info_needed == 'Location' and self.image_info.address is not None:
            view_map_button = ttk.Button(
                view_map_frame,
                text="view on map",
                pady=5,
                command=self.image_info.view_location_on_map
            )
            view_map_button.pack()


class ImageViewer:
    IMAGE_FILES = ('.png', '.jpg', '.jpeg', '.gif')

    def __init__(self, master):
        self.master = master
        self.master.geometry('500x550')
        self.master.title("Image Viewer")

        self.image_label = ttk.Label(self.master)
        self.image_label.pack(pady=5)

        self.info_menu = None
        self.info_window = None
        self.is_info_menu_open = False

        self.configure_ui()

    def configure_ui(self):
        # Menu bar
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.load_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.destroy)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Full Screen", command=self.toggle_fullscreen)
        self.menu_bar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Navigation bar
        self.nav_frame = ttk.Frame(self.master)
        self.nav_frame.pack(side='bottom', fill='x')

        # Navigation Buttons
        self.prev_button = tk.Button(self.nav_frame, text="Previous", command=self.show_previous_image)
        self.next_button = tk.Button(self.nav_frame, text="Next", command=self.show_next_image)

        # Status bar
        self.status_bar = ttk.Label(self.master, text="", anchor=tk.W)
        self.status_bar.pack(side="bottom")

        # Keyboard shortcuts
        self.master.bind("<Left>", lambda event: self.show_previous_image())
        self.master.bind("<Right>", lambda event: self.show_next_image())
        self.master.bind("<F11>", lambda event: self.toggle_fullscreen())

    @property
    def image_path(self):
        self.current_index = max(0, min(self.current_index, len(self.image_list) - 1))
        return self.image_list[self.current_index]

    @property
    def image_info(self):
        return ImageInfo(self.image_path)

    def is_image(self, file):
        return file.is_file() and file.suffix.lower() in self.IMAGE_FILES

    def add_info_menu(self):
        if self.is_info_menu_open:
            self.remove_info_menu()

        info_menu = tk.Menu(self.menu_bar, tearoff=0)
        info_menu.add_command(label="Date taken", command=lambda: self.show_image_info('Date taken'))
        info_menu.add_separator()
        info_menu.add_command(label="Location", command=lambda: self.show_image_info('Location'))
        info_menu.add_separator()
        info_menu.add_command(label="Device used", command=lambda: self.show_image_info('Device used'))
        self.menu_bar.add_cascade(label="Info", menu=info_menu)

        self.is_info_menu_open = True
        self.info_menu = info_menu

    def remove_info_menu(self):
        if self.info_menu:
            self.menu_bar.delete("Info")
            self.is_info_menu_open = False
            self.info_menu = None

    def show_previous_image(self):
        self.current_index -= 1
        self.display_image()
        self.close_info_window()

    def show_next_image(self):
        self.current_index += 1
        self.display_image()
        self.close_info_window()

    def show_nav_buttons(self):
        self.prev_button.pack(side='left', padx=5)
        self.next_button.pack(side='right', padx=5)

    def update_nav_button_state(self):
        self.prev_button.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_index < len(self.image_list) - 1 else tk.DISABLED)

    def update_status_bar(self):
        status_text = f"Image {self.current_index + 1} of {len(self.image_list)}"
        self.status_bar.config(text=status_text)

    def toggle_fullscreen(self):
        self.master.attributes("-fullscreen", not self.master.attributes("-fullscreen"))

    def show_about_dialog(self):
        about_text = "Image Viewer App\nVersion 1.0\n\n© 2024 Kirby Image Viewer App"
        tk.messagebox.showinfo("About", about_text)

    def show_image_info(self, info_needed):
        self.info_window = InfoWindow(self.image_info, info_needed, self.master)
        self.info_window.is_open = True
        self.info_window.mainloop()

    def close_info_window(self):
        if self.info_window and self.info_window.is_open:
            self.info_window.destroy()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if file_path:
            file_path = Path(file_path)
            self.image_folder = file_path.parent
            self.image_list = [file for file in self.image_folder.glob("*") if self.is_image(file)]
            self.current_index = self.image_list.index(file_path)
            self.display_image()
            self.close_info_window()

    def display_image(self):
        if self.image_path:
            image = Image.open(self.image_path)
            image = self.resize_image(image)
            self.image = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.image)
            self.update_status_bar()
            self.update_nav_button_state()
            self.show_nav_buttons()
            self.add_info_menu()

    def resize_image(self, image, desired_width=450):
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        # Calculate the new dimensions while preserving the aspect ratio
        if aspect_ratio > 1:  # Landscape image
            new_width = desired_width
            new_height = int(desired_width / aspect_ratio)
        else:  # Portrait or square image
            new_width = int(desired_width * aspect_ratio)
            new_height = desired_width

        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return resized_image


if __name__ == "__main__":
    configure_logging()
    app = ImageViewer(ttk.Window(themename='darkly'))
    app.master.mainloop()
