import re
import time
import logging
import webbrowser
import tkinter as tk
from pathlib import Path
from datetime import date
from tkinter import filedialog

import ttkbootstrap as ttk

import pyexiv2
from gmplot import gmplot
from PIL import Image, ImageTk
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable


def configure_logging(*, log_level=logging.ERROR, log_file=None):
    log_handlers = [logging.StreamHandler()]
    if log_file is not None:
        log_handlers = [logging.FileHandler(log_file, mode='w')]

    logging.basicConfig(
        level=log_level,
        handlers=log_handlers,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def view_image_location_on_map(coordinates):
    latitude, longitude = coordinates
    data_folder = Path('__file__').parents[1] / 'logs'
    data_folder.mkdir(exist_ok=True)

    gmap = gmplot.GoogleMapPlotter(latitude, longitude, 12)
    gmap.marker(latitude, longitude, 'cornflowerblue')
    gmap.draw(str(data_folder) + 'location.html')

    webbrowser.open(str(data_folder) + 'location.html')


class ImageInfo:
    def __init__(self, image_path):
        self.image_path = image_path
        self.get_metadata()

    def get_metadata(self):
        with open(self.image_path, 'rb') as f:
            with pyexiv2.ImageData(f.read()) as image_info:
                self.metadata = image_info.read_exif()

    @property
    def device_model(self):
        return self.metadata.get('Exif.Image.Model')

    @property
    def device_make(self):
        return self.metadata.get('Exif.Image.Make')

    @property
    def date_taken(self):
        date_taken = self.metadata.get('Exif.Image.DateTime')
        if date_taken is None:
            return
        if not any(char.isalpha() for char in date_taken):
            try:
                date_taken = re.split(r'\s+|[:]', date_taken)
                year, month, day, *_ = [int(num) for num in date_taken]
                return date(year, month, day).strftime('%B %d, %Y')
            except ValueError:
                date_taken = int(date_taken[0]) / 1000
                return date.fromtimestamp(date_taken).strftime('%B %d, %Y')
        else:
            year, month, day, *_ = time.strptime(re.findall(r'\w+\s+\d+[,]\s+\d+', date_taken)[0], '%b %d, %Y')
            return date(year, month, day).strftime('%B %d, %Y')

    @property
    def coordinates(self):
        if 'Exif.GPSInfo.GPSLatitude' in self.metadata:
            latitude_data = self.metadata['Exif.GPSInfo.GPSLatitude']
            longitude_data = self.metadata['Exif.GPSInfo.GPSLongitude']

            latitude = [eval(values) for values in latitude_data.split()]
            latitude_deg = latitude[0] + latitude[1] / 60 + latitude[2] / 3600
            longitude = [eval(values) for values in longitude_data.split()]
            longitude_deg = longitude[0] + longitude[1] / 60 + longitude[2] / 3600

            return latitude_deg, longitude_deg

    @property
    def address(self):
        if self.coordinates:
            latitude, longitude = self.coordinates
            geolocator = Nominatim(user_agent="image_locator")
            try:
                location = geolocator.reverse((latitude, longitude), language='en')
                return location.address
            except GeocoderTimedOut:
                logging.error("Geocoding service timed out.")
                return None
            except GeocoderUnavailable:
                logging.error("Geocoding service unavailable.")
                return None
            except Exception as e:
                logging.error(f"Error during geocoding: {e}")
                return None
            finally:
                time.sleep(1)


class ImageViewer:
    def __init__(self, master):
        self.master = master
        self.master.geometry('500x550')
        self.master.title("Image Viewer")

        self.image_path = None
        self.image = None
        # widgets
        self.load_button = ttk.Button(self.master, text="Open Image", command=self.load_image)
        self.info_textbox = tk.Text(self.master, wrap="word", height=5, width=40)
        self.image_label = ttk.Label(self.master)
        # layout
        self.load_button.pack()
        self.info_textbox.pack()
        self.image_label.pack()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if file_path:
            self.image_path = file_path
            self.info = ImageInfo(self.image_path)
            self.display_image()

    def resize(self, image):
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        new_height = int(150 / aspect_ratio)
        image = image.resize((150, new_height), Image.Resampling.LANCZOS)

        return image

    def display_image(self):
        if self.image_path:
            image = Image.open(self.image_path)
            image = self.resize(image)
            self.image = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.image)

            info_text = (
                f'date taken: {self.info.date_taken}\n'
                f'coordinates: {self.info.coordinates}\n'
                f'make of device took: {self.info.device_make}\n'
                f'model of device took: {self.info.device_model}\n'
                f'address where image was taken: {self.info.address}'
            )
            self.info_textbox.delete(1.0, "end")  # Clear previous text
            self.info_textbox.insert("end", info_text)


if __name__ == "__main__":
    configure_logging()
    app = ImageViewer(ttk.Window(themename='darkly'))
    app.master.mainloop()
