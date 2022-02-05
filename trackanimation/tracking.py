# -*- coding: utf-8 -*-

# Copyright 2017 Juan José Martín Miralles
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Python modules
import glob
import os

# Third party modules
import gpxpy
from gpxpy.gpx import GPXBounds
import pandas
import tqdm
import geopy

# Own modules
from trackanimation import utils as trk_utils
from trackanimation.utils import TrackException


class DFTrack:
    def __init__(self, df_points=None, columns=None):
        if df_points is None:
            self.df = pandas.DataFrame()

        if isinstance(df_points, pandas.DataFrame):
            self.df = df_points
        else:
            if columns is None:
                columns = ['CodeRoute', 'Latitude', 'Longitude', 'Altitude', 'Date',
                           'Speed', 'TimeDifference', 'Distance', 'FileName']
            self.df = pandas.DataFrame(df_points, columns=columns)

    def export(self, filename='exported_file', export_format='csv'):
        """
        Export a data frame of DFTrack to JSON or CSV.
        """
        if export_format.lower() == 'json':
            self.df.reset_index().to_json(orient='records', path_or_buf=filename + '.json')
        elif export_format.lower() == 'csv':
            self.df.to_csv(path_or_buf=filename + '.csv')
        else:
            raise TrackException('Must specify a valid format to export', "'%s'" % export_format)

    def get_copy(self):
        """
        Makes a copy of the DFTrack dataframe
        """
        return self.__class__(self.df.copy(), self.df.columns.values.tolist())

    def sort_columns(self, list_columns):
        try:
            return self.__class__(self.df.sort_values(list_columns), self.df.columns.values.tolist())
        except KeyError as exception:
            raise TrackException(exception)

    def get_tracks_by_place(self, string_location, timeout=10, only_points=True):
        """
        Gets the points of the specified place as a DFTrack.
        Searching in Google's API and defaults to OpenStreetMap's API.

        Returns None if nothing is found.

        only_points: boolean
            Retrieve only the points that cross a place. Otherwise
            retrive all the track's points that cross a place.
        """
        dict_coordinates = self.get_coordinates_from_google(string_location, timeout=timeout, only_points=only_points)
        if dict_coordinates is None:
            return None

        dict_coordinates = self.get_tracks_by_place_osm(string_location, timeout=timeout, only_points=only_points)        
        if dict_coordinates is None:
            return None

        dataframe_tracks = self.calculate_dataframe_tracks(dict_coordinates, only_points)
        
        return dataframe_tracks

    def calculate_dataframe_tracks(self, dict_coordinates, only_points=True):
        """
        dictionary should have lat_sw, lat_ne, lon_sw, lon_ne
        """
        mask_ne_lat = self.df['Latitude'] < dict_coordinates['lat_ne']
        mask_ne_lon = self.df['Longitude'] < dict_coordinates['lon_ne']
        mask_sw_lat = self.df['Latitude'] > dict_coordinates['lat_sw']
        mask_sw_lon = self.df['Longitude'] > dict_coordinates['lon_sw']

        df_place = self.df[mask_ne_lat & mask_ne_lon & mask_sw_lat & mask_sw_lon]

        if only_points:
            return self.__class__(df_place)

        track_list = df_place['CodeRoute'].unique().tolist()
        mask_track_list = self.df['CodeRoute'].isin(track_list)

        return self.__class__(self.df[mask_track_list])

    def get_coordinates_from_google(self, string_location, timeout=10):
        """
        Gets the points of the specified place searching in Google's API.

        Returns None if nothing is found.
        """
        try:
            geolocator = geopy.GoogleV3()
            location = geolocator.geocode(string_location, timeout=timeout)

            southwest_lat = float(location.raw['geometry']['bounds']['southwest']['lat'])
            northeast_lat = float(location.raw['geometry']['bounds']['northeast']['lat'])
            southwest_lon = float(location.raw['geometry']['bounds']['southwest']['lon'])
            northeast_lon = float(location.raw['geometry']['bounds']['northeast']['lon'])

        except geopy.exc.GeopyError:
            return None
        
        dict_coordinates = {
            'lat_sw' : southwest_lat,
            'lat_ne' : northeast_lat,
            'lon_sw' : southwest_lon,
            'lon_ne' : northeast_lon
        }
        
        return dict_coordinates

    def get_tracks_by_place_osm(self, string_location, timeout=10):
        """
        Gets the points of the specified place searching in OpenStreetMap's API.

        Returns None if nothing is found.
        """
        try:
            geolocator = geopy.Nominatim()
            location = geolocator.geocode(string_location, timeout=timeout)

            southwest_lat = float(location.raw['boundingbox'][0])
            northeast_lat = float(location.raw['boundingbox'][1])
            southwest_lon = float(location.raw['boundingbox'][2])
            northeast_lon = float(location.raw['boundingbox'][3])

        except geopy.exc.GeopyError:
            return None

        dict_coordinates = {
            'lat_sw' : southwest_lat,
            'lat_ne' : northeast_lat,
            'lon_sw' : southwest_lon,
            'lon_ne' : northeast_lon
        }
        
        return dict_coordinates

    def get_tracks_by_date(self, start=None, end=None, periods=None, freq='D'):
        """
        Gets the points of the specified date range
        using various combinations of parameters.

        2 of 'start', 'end', or 'periods' must be specified.

        Date format recommended: 'yyyy-mm-dd'

        Parameters
        ----------
        start: date
            Date start period
        end: date
            Date end period
        periods: int
            Number of periods. If None, must specify 'start' and 'end'
        freq: string
            Frequency of the date range

        Returns
        -------
        df_date: DFTrack
            A DFTrack with the points of the specified date range.
        """
        if trk_utils.is_time_format(start) or trk_utils.is_time_format(end):
            raise TrackException('Must specify an appropiate date format', 'Time format found')

        rng = pandas.date_range(start=start, end=end, periods=periods, freq=freq)

        df_date = self.df.copy()
        df_date.loc[:, 'Date'] = pandas.to_datetime(df_date['Date'])

        # I think you can call the .dt attribute directly
        series_short_date = df_date['Date'].apply(lambda date: date.date().strftime('%Y-%m-%d'))
        mask_rng = series_short_date.isin(rng)
        df_date = df_date[mask_rng]

        df_date = df_date.reset_index(drop=True)

        return self.__class__(df_date, df_date.columns.values.tolist())

    def get_tracks_by_time(self, start, end, include_start=True, include_end=True):
        """
        Gets the points between the specified time range.

        Parameters
        ----------
        start: datetime.time
            Time start period
        end: datetime.time
            Time end period
        include_start: boolean
        include_end: boolean

        Returns
        -------
        df_time: DFTrack
            A DFTrack with the points of the specified date and time periods.
        """
        if not trk_utils.is_time_format(start) or not trk_utils.is_time_format(end):
            raise TrackException('Must specify an appropiate time format', trk_utils.TIME_FORMATS)

        df_time = self.df.copy()

        index = pandas.DatetimeIndex(df_time['Date'])
        df_time = df_time.iloc[index.indexer_between_time(
            start_time=start, end_time=end, include_start=include_start, include_end=include_end)]

        df_time = df_time.reset_index(drop=True)

        return self.__class__(df_time, df_time.columns.values.tolist())

    def point_video_normalize(self):
        df = self.df.copy()

        df_norm = pandas.DataFrame()
        group_size = df.groupby('CodeRoute').size()
        max_value = group_size.max()
        name_max_value = group_size.idxmax()

        grouped = df['CodeRoute'].unique()

        for name in tqdm.tqdm(grouped, desc='Groups'):
            df_slice = df[df['CodeRoute'] == name]
            df_slice = df_slice.reset_index(drop=True)
            div = int(max_value / len(df_slice)) + 1
            df_index = pandas.DataFrame(df_slice.index)
            df_slice['VideoFrame'] = df_index.apply(lambda x: x + 1 if name_max_value == name else x * div)
            df_norm = pandas.concat([df_norm, df_slice])

        df_norm = df_norm.reset_index(drop=True)

        return self.__class__(df_norm, df_norm.columns.values.tolist())

    def time_video_normalize(self, time, framerate=5):
        df = self.df.copy()
        if time == 0:
            df['VideoFrame'] = 0
            df = df.reset_index(drop=True)
            return self.__class__(df, list(df))

        n_fps = time * framerate
        df = df.sort_values('Date')
        df_cum = trk_utils.calculate_cum_time_diff(df)
        grouped = df_cum['CodeRoute'].unique()

        df_norm = pandas.DataFrame()
        point_idx = 1

        for name in tqdm.tqdm(grouped, desc='Groups'):
            df_slice = df_cum[df_cum['CodeRoute'] == name]
            time_diff = float(
                (df_slice[['TimeDifference']].sum() / time) / framerate)  # Track duration divided by time and framerate

            df_range = df_slice[df_slice['CumTimeDiff'] == 0]
            df_range = df_range.reset_index(drop=True)
            df_range['VideoFrame'] = 0
            df_norm = pandas.concat([df_norm, df_range])

            for i in tqdm.tqdm(range(1, n_fps + 1), desc='Num FPS', leave=False):
                x_start = time_diff * (i - 1)
                x_end = time_diff * i

                df_range = df_slice[(df_slice['CumTimeDiff'] > x_start) & (df_slice['CumTimeDiff'] <= x_end)]
                df_range = df_range.reset_index(drop=True)

                if df_range.empty:
                    df_start = df_slice[df_slice['CumTimeDiff'] <= x_start].tail(1)
                    df_end = df_slice[df_slice['CumTimeDiff'] > x_end].head(1)

                    if not df_start.empty and not df_end.empty:
                        df_middlePoint = trk_utils.get_point_in_the_middle(df_start, df_end, time_diff, point_idx)
                        df_range = pandas.DataFrame(df_middlePoint, columns=list(df_cum))

                    point_idx = point_idx + 1
                else:
                    point_idx = 1

                df_range['VideoFrame'] = i
                df_norm = pandas.concat([df_norm, df_range])
        df_norm = df_norm.reset_index(drop=True)

        return self.__class__(df_norm, df_norm.columns.values.tolist())

    def set_colors(self, column_name, individual_tracks=True):
        if column_name not in self.df:
            raise TrackException('Column name not found', "'%s'" % column_name)

        df = self.df.copy()

        df_colors = pandas.DataFrame()

        if individual_tracks:
            grouped = df['CodeRoute'].unique()

            for name in grouped:
                df_slice = df[df['CodeRoute'] == name]
                df_slice = df_slice.reset_index(drop=True)

                min = df_slice[column_name].min()
                max = df_slice[column_name].max()

                df_slice['Color'] = df_slice[column_name].apply(trk_utils.calculate_rgb, minimum=min, maximum=max)
                df_colors = pandas.concat([df_colors, df_slice])

            df_colors = df_colors.reset_index(drop=True)
            return self.__class__(df_colors, df_colors.columns.values.tolist())
        else:
            min = df[column_name].min()
            max = df[column_name].max()

            df['Color'] = df[column_name].apply(trk_utils.calculate_rgb, minimum=min, maximum=max)
            df = df.reset_index(drop=True)

            return self.__class__(df, df.columns.values.tolist())

    def drop_duplicates(self):
        """
        Drop points of the same track with the same Latitude and Longitude.
        """
        return self.__class__(self.df.drop_duplicates(['CodeRoute', 'Latitude', 'Longitude']))

    def get_bounds(self):
        """
        Get the bounds of the DFTrack

        Returns
        -------
        bounds: gpxpy.GPXBounds
        """
        min_lat = self.df['Latitude'].min()
        max_lat = self.df['Latitude'].max()
        min_lon = self.df['Longitude'].min()
        max_lon = self.df['Longitude'].max()

        return GPXBounds(min_lat, max_lat, min_lon, max_lon)

    def concat_dfts(self, df_track):
        """
        Concatenate DFTrack objects with 'self'

        Parameters
        ----------
        df_track: DFTrack or list of DFTrack
            The ones that will be joined with 'self'

        Returns
        -------
        df_concat: DFTrack
            A DFTrack with the all the DFTrack concatenated
        """
        if not isinstance(df_track, list):
            # If it is not a list of DFTrack, make a list of one element
            df_track = [df_track]

        list_dft = [self.df]  # First element is 'self'

        # From list of 'df_track', create a list of their dataframes
        for df in df_track:
            if not isinstance(df, DFTrack):
                raise TrackException("Parameter must be a 'DFTrack' object", '%s found' % type(df))

            list_dft.append(df.df)

        return self.__class__(pandas.concat(list_dft, sort=True))


class ReadTrack:
    def __init__(self, directory_or_file):
        self.directory_or_file = directory_or_file
        self.points_list = []

    def read_gpx_file(self, filename):
        try:
            with open(filename, "r") as f:
                prev_point = None
                head, tail = os.path.split(filename)
                code_route = tail.replace(".gpx", "")
                try:
                    gpx = gpxpy.parse(f)
                    for point in gpx.walk(only_points=True):
                        speed = point.speed_between(prev_point)
                        if speed is None:
                            speed = 0

                        time_difference = point.time_difference(prev_point)
                        if time_difference is None:
                            time_difference = 0

                        distance = point.distance_3d(prev_point)
                        if not distance:
                            distance = point.distance_2d(prev_point)
                        if distance is None:
                            distance = 0

                        self.points_list.append([code_route, point.latitude, point.longitude, point.elevation,
                                                 point.time, speed, time_difference, distance, gpx.name])

                        prev_point = point
                except Exception as e:
                    raise TrackException('GPX file "' + filename + '" malformed', e)
        except FileNotFoundError as e:
            raise TrackException('GPX file "' + filename + '" not found', e)

    def read_gpx(self, files_to_read=None):
        if self.directory_or_file.lower().endswith('.gpx'):
            self.read_gpx_file(self.directory_or_file)
        else:
            n_file_read = 1
            for file in tqdm.tqdm(glob.glob(self.directory_or_file + "*.gpx"), desc='Reading files'):
                try:
                    self.read_gpx_file(file)
                except TrackException as e:
                    pass

                if files_to_read == n_file_read:
                    break
                n_file_read += 1

        return DFTrack(self.points_list)

    def read_csv(self):
        try:
            return DFTrack(pandas.read_csv(self.directory_or_file, sep=',', header=0, index_col=0))
        except FileNotFoundError as e:
            raise TrackException('CSV file not found', e)
