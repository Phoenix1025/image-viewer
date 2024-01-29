import datetime
import webbrowser

import folium
import pyexiv2
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

from configs import data_folder, logger


class ImageInfo:
    def __init__(self, image_path):
        self.image_path = image_path

    def _read_exif_metadata(self):
        try:
            with open(self.image_path, 'rb') as f:
                with pyexiv2.ImageData(f.read()) as image_info:
                    return image_info.read_exif()
        except Exception as e:
            logger.error(f"Error reading EXIF metadata for {self.image_path}: {e}")
            return {}

    @property
    def metadata(self):
        return self._read_exif_metadata()

    @property
    def device_model(self):
        return self.metadata.get('Exif.Image.Model')

    @property
    def device_make(self):
        return self.metadata.get('Exif.Image.Make')

    @property
    def date(self):
        datetime_info = self.get_datetime_info()
        return self._parse_datetime_info(datetime_info).strftime('%B %d, %Y') if datetime_info else None

    @property
    def time(self):
        datetime_info = self.get_datetime_info()
        return self._parse_datetime_info(datetime_info).strftime('%I:%M %p') if datetime_info else None

    def _parse_datetime_info(self, datetime_info):
        # parse from format like this: '1616347542050'
        if all(char.isdigit() for char in datetime_info):
            date_and_time = int(datetime_info) / 1000
            return datetime.datetime.fromtimestamp(date_and_time)

        # parse from format like this: 'Dec 8, 2018 8:14:03 AM'
        if any(char.isalpha() for char in datetime_info):
            return datetime.datetime.strptime(datetime_info, '%b %d, %Y %H:%M:%S %p')
        else:
            # parse from format like this: '2017:04:01 18:57:18'
            return datetime.datetime.strptime(datetime_info, '%Y:%m:%d %H:%M:%S')

    def get_datetime_info(self):
        exif_datetime_keys = ('Exif.Image.DateTime', 'Exif.Photo.DateTimeOriginal')
        datetime_info = [self.metadata.get(key) for key in exif_datetime_keys if self.metadata.get(key)]

        datetime_info = datetime_info[0] if datetime_info else None
        if datetime_info is None:
            if self.metadata:
                logger.error(f'No DateTime info extracted from {self.image_path}.')
            else:
                logger.error(f'No metadata available for {self.image_path}.')

        return datetime_info

    @property
    def coordinates(self):
        latitude_info = self.metadata.get('Exif.GPSInfo.GPSLatitude')
        longitude_info = self.metadata.get('Exif.GPSInfo.GPSLongitude')

        if latitude_info and longitude_info:
            latitude = sum((value / 60**i) for i, value in enumerate(map(eval, latitude_info.split())))
            longitude = sum((value / 60**i) for i, value in enumerate(map(eval, longitude_info.split())))

            return round(latitude, 6), round(longitude, 6)

    @property
    def address(self):
        if self.coordinates:
            latitude, longitude = self.coordinates
            geolocator = Nominatim(user_agent="image_locator")
            try:
                location = geolocator.reverse((latitude, longitude), language='en')
                return location.address
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                logger.error(f"Error during geocoding for {self.image_path}: {e}")
            except Exception as e:
                logger.error(f"Error during geocoding for {self.image_path}: {e}")
        return None

    def view_location_on_map(self):
        latitude, longitude = self.coordinates

        map_location = folium.Map(location=[latitude, longitude], zoom_start=15)
        folium.Marker([latitude, longitude], popup='Image Location').add_to(map_location)
        map_file = data_folder / 'location.html'
        map_location.save(map_file)
        webbrowser.open(map_file)


if __name__ == '__main__':
    from pathlib import Path

    def individual_test(test_path):
        img_info = ImageInfo(test_path)
        print(img_info.metadata)
        print()
        print(img_info.image_path)
        print(f'date: {img_info.date}')
        print(f'time: {img_info.time}')
        print(f'coordinates: {img_info.coordinates}')
        print(f'device make: {img_info.device_make}')
        print(f'device model: {img_info.device_model}')

    def folder_test(test_path):
        image_files = ('.png', '.jpg', '.jpeg', '.gif')
        for file in test_path.rglob('*'):
            if file.suffix.lower() in image_files:
                img_info = ImageInfo(file)
                print(img_info.image_path, 'date taken:', img_info.date, img_info.time)

    test_folder_1 = Path('C:/Users/KENNETH/Desktop/Test Folder/Image files')
    test_folder_2 = Path('C:/Users/KENNETH/Pictures')
    # folder_test(test_folder_1)

    test_file_1 = 'C:/Users/KENNETH/Pictures/VIVO_1901/Camera/IMG_20210322_012541.JPG'  # timestamp
    test_file_2 = 'C:/Users/KENNETH/Pictures/OPPO_a37f/Maureen/Camera/C360_2017-04-01-18-57-18-788.jpg'  # exif key
    test_file_3 = 'C:/Users/KENNETH/Pictures/OPPO_a37f/Maureen/Camera/IMG_20170408_145205.jpg'  # no metadata
    test_file_4 = 'C:/Users/KENNETH/Desktop/Test Folder/Image files/jpg files/picture 24.jpg'  # no datetime info
    test_file_5 = 'C:/Users/KENNETH/Desktop/Test Folder/Image files/jpg files/1544228043189.jpg'  # 'Dec 8, 2018 8:14:03 AM'
    # individual_test(test_file_5)
