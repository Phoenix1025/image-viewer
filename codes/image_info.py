import re
import time
import logging
import webbrowser
from datetime import date

import pyexiv2
from gmplot import gmplot
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

from configs import data_folder


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
                logging.error(f"Image {self.image_path}: Geocoding service timed out.")
                return None
            except GeocoderUnavailable:
                logging.error(f"Image {self.image_path}: Geocoding service unavailable.")
                return None
            except Exception as e:
                logging.error(f"Image {self.image_path}: Error during geocoding: {e}")
                return None
            finally:
                time.sleep(1)

    def view_location_on_map(self):
        latitude, longitude = self.coordinates

        gmap = gmplot.GoogleMapPlotter(latitude, longitude, 12)
        gmap.marker(latitude, longitude, 'cornflowerblue')
        gmap.draw(data_folder / 'location.html')

        webbrowser.open(data_folder / 'location.html')
