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
import math
import warnings
import datetime

# Third party modules
import geopy
import geopy.distance
import pandas

TIME_FORMATS = ['%H:%M', '%H%M', '%I:%M%p', '%I%M%p', '%H:%M:%S', '%H%M%S', '%I:%M:%S%p', '%I%M%S%p']

class TrackException(Exception):
    """
    Generic exception for TrackAnimation
    """

    def __init__(self, msg, original_exception):
        super(TrackException, self).__init__(msg + (": %s" % original_exception))
        self.original_exception = original_exception

def get_bearing(dataframe_start, dataframe_end):
    """
    Calculates the bearing between two points.

    Parameters
    ----------
    dataframe_start: geopy.Point
    dataframe_end: geopy.Point

    Returns
    -------
    point: int
        Bearing in degrees between the start and end points.
    """
    start_lat = math.radians(dataframe_start.latitude)
    start_lng = math.radians(dataframe_start.longitude)
    end_lat = math.radians(dataframe_end.latitude)
    end_lng = math.radians(dataframe_end.longitude)

    d_lng = end_lng - start_lng
    if abs(d_lng) > math.pi:
        if d_lng > 0.0:
            d_lng = -(2.0 * math.pi - d_lng)
        else:
            d_lng = (2.0 * math.pi + d_lng)

    tan_start = math.tan(start_lat / 2.0 + math.pi / 4.0)
    tan_end = math.tan(end_lat / 2.0 + math.pi / 4.0)
    d_phi = math.log(tan_end / tan_start)
    bearing = (math.degrees(math.atan2(d_lng, d_phi)) + 360.0) % 360.0

    return bearing

def get_coordinates(dataframe_start, dataframe_end, distance_meters):
    """
    Calculates the new coordinates between two points depending
    of the specified distance and the calculated bearing.

    Parameters
    ----------
    dataframe_start: geopy.Point
    dataframe_end: geopy.Point
    distance_meters: float

    Returns
    -------
    point: geopy.Point
        A new point between the start and the end points.
    """
    bearing = get_bearing(dataframe_start, dataframe_end)

    distance_km = distance_meters / 1000
    d = geopy.distance.VincentyDistance(kilometers=distance_km)
    destination = d.destination(point=dataframe_start, bearing=bearing)

    return geopy.Point(destination.latitude, destination.longitude)

def get_point_in_the_middle(dataframe_start, dataframe_end, time_diff, point_idx):
    """
    Calculates a new point between two points depending of the
    time difference between them and the point index.

    Parameters
    ----------
    time_diff: float
    point_idx: int
        Point index between the start and the end points

    Returns
    -------
    point: list
        A new point between the start and the end points.
    """
    time_proportion = (time_diff * point_idx) / dataframe_end['TimeDifference'].item()

    distance_proportion = dataframe_end['Distance'].item() * time_proportion
    time_diff_proportion = dataframe_end['TimeDifference'].item() * time_proportion
    speed = distance_proportion / time_diff_proportion
    distance = time_diff * speed
    cum_time_diff = int(dataframe_start['CumTimeDiff'].item() + time_diff_proportion)
    # date = datetime.datetime.strptime(dataframe_start['Date'].item(), '%Y-%m-%d %H:%M:%S') + datetime.datetime.timedelta(seconds=int(
    # time_diff_proportion))
    date = pandas.to_datetime(
        dataframe_start['Date'].astype(str), 
        format='%Y-%m-%d %H:%M:%S') + datetime.datetime.timedelta(seconds=int(time_diff_proportion)
        )
    altitude = (dataframe_end['Altitude'].item() + dataframe_start['Altitude'].item()) / 2
    name = dataframe_start['CodeRoute'].item()

    geo_start = geopy.Point(dataframe_start['Latitude'].item(), dataframe_start['Longitude'].item())
    geo_end = geopy.Point(dataframe_end['Latitude'].item(), dataframe_end['Longitude'].item())
    middle_point = get_coordinates(geo_start, geo_end, distance_proportion)

    df_middle_point = ([[name, middle_point.latitude, middle_point.longitude, altitude,
                         date, speed, int(time_diff), distance, None, cum_time_diff]])

    return df_middle_point


def calculate_rgb(value, minimum, maximum):
    """
    Calculates an rgb color of a value depending on
    the minimum and maximum values.

    Returns tuple
    """
    value = float(value)
    minimum = float(minimum)
    maximum = float(maximum)

    if minimum == maximum:
        ratio = 0
    else:
        ratio = 2 * (value - minimum) / (maximum - minimum)

    b = int(max(0, 255 * (1 - ratio)))
    r = int(max(0, 255 * (ratio - 1)))
    g = 255 - b - r

    return r / 255.0, g / 255.0, b / 255.0

def calculate_cum_time_diff(df):
    """
    Calculates the cumulative of the time difference
    between points for each track of 'dfTrack'.
    """
    df = df.copy()

    df_cum = pandas.DataFrame()
    grouped = df['CodeRoute'].unique()

    for name in grouped:
        df_slice = df[df['CodeRoute'] == name]
        df_slice = df_slice.reset_index(drop=True)
        df_slice['CumTimeDiff'] = df_slice['TimeDifference'].cumsum()
        df_cum = pandas.concat([df_cum, df_slice])

    df_cum = df_cum.reset_index(drop=True)

    return df_cum

def is_time_format(time):
    """
    Check if 'time' variable has the format of one
    of the 'time_formats'
    """
    if time is None:
        return False

    for time_format in TIME_FORMATS:
        try:
            datetime.datetime.strptime(time, time_format)
            return True
        except ValueError:
            pass

    return False
