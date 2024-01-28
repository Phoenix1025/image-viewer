import re
import time
import logging
import datetime
import webbrowser

import folium
import pyexiv2
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

from configs import data_folder


class ImageInfo:
    def __init__(self, image_path):
        self.image_path = image_path

    @property
    def metadata(self):
        with open(self.image_path, 'rb') as f:
            with pyexiv2.ImageData(f.read()) as image_info:
                return image_info.read_exif()

    @property
    def device_model(self):
        return self.metadata.get('Exif.Image.Model')

    @property
    def device_make(self):
        return self.metadata.get('Exif.Image.Make')

    @property
    def date(self):
        datetime_info = self.get_datetime_info()
        if not datetime_info:
            return None
        if not any(char.isalpha() for char in datetime_info):
            try:
                date_taken = re.split(r'\s+|[:]', datetime_info)
                year, month, day, *_ = [int(num) for num in date_taken]
                return datetime.date(year, month, day).strftime('%B %d, %Y')
            except ValueError:
                date_taken = int(datetime_info) / 1000
                return datetime.date.fromtimestamp(date_taken).strftime('%B %d, %Y')
        else:
            year, month, day, *_ = time.strptime(re.findall(r'\w+\s+\d+[,]\s+\d+', datetime_info)[0], '%b %d, %Y')
            return datetime.date(year, month, day).strftime('%B %d, %Y')

    @property
    def time(self):
        datetime_info = self.get_datetime_info()
        if not datetime_info:
            return None
        if not any(char.isalpha() for char in datetime_info):
            try:
                time_taken = re.split(r'\s+|[:]', datetime_info)
                *_, hrs, mins, secs = [int(num) for num in time_taken]
                return datetime.time(hrs, mins, secs).strftime('%I:%M %p')
            except ValueError:
                time_taken = int(datetime_info) / 1000
                return datetime.datetime.fromtimestamp(time_taken).strftime('%I:%M %p')
        else:
            _, _, _, hrs, mins, secs, *_ = time.strptime(re.findall(r'\d+[:]\d+[:]\d+', datetime_info)[0], '%H:%M:%S')
            return datetime.time(hrs, mins, secs).strftime('%I:%M %p')

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
            except GeocoderTimedOut:
                logging.error(f"Image {self.image_path}: Geocoding service timed out.")
                return None
            except GeocoderUnavailable:
                logging.error(f"Image {self.image_path}: Geocoding service unavailable.")
                return None
            except Exception as e:
                logging.error(f"Image {self.image_path}: Error during geocoding: {e}")
                return None
            else:
                return location.address

    def view_location_on_map(self):
        latitude, longitude = self.coordinates
        map_location = folium.Map(location=[latitude, longitude], zoom_start=12)

        folium.Marker([latitude, longitude], popup='Image Location').add_to(map_location)
        map_file = data_folder / 'location.html'
        map_location.save(map_file)
        webbrowser.open(map_file)

    def get_datetime_info(self):
        exif_datetime_keys = ('Exif.Image.DateTime', 'Exif.Photo.DateTimeOriginal')
        datetime_info = [self.metadata.get(key) for key in exif_datetime_keys if self.metadata.get(key)]

        datetime_info = datetime_info[0] if datetime_info else None
        if datetime_info is None and self.metadata:
            logging.error(f'No DateTime info extracted from {self.image_path}')

        return datetime_info


if __name__ == '__main__':
    from pathlib import Path

    def individual_test(test_path):
        img_info = ImageInfo(test_path)
        print(img_info.metadata)
        print()
        print(img_info.image_path, 'date taken:', img_info.date, img_info.time)

    def folder_test(test_path):
        image_files = ('.png', '.jpg', '.jpeg', '.gif')
        for file in test_path.rglob('*'):
            if file.suffix.lower() in image_files:
                img_info = ImageInfo(file)
                print(img_info.image_path, 'date taken:', img_info.date, img_info.time)

    test_folder_1 = Path('C:/Users/KENNETH/Desktop/Test Folder/Image files')
    test_folder_2 = Path('C:/Users/KENNETH/Pictures')
    folder_test(test_folder_1)

    test_file_1 = 'C:/Users/KENNETH/Pictures/VIVO_1901/Camera/IMG_20210322_012541.JPG'  # timestamp
    test_file_2 = 'C:/Users/KENNETH/Pictures/OPPO_a37f/Maureen/Camera/C360_2017-04-01-18-57-18-788.jpg'  # exif key
    test_file_3 = 'C:/Users/KENNETH/Pictures/OPPO_a37f/Maureen/Camera/IMG_20170408_145205.jpg'  # no metadata
    test_file_4 = 'C:/Users/KENNETH/Desktop/Test Folder/Image files/jpg files/picture 24.jpg'  # no datetime info
    individual_test(test_file_4)
