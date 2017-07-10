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
import pandas as pd
from pandas import DataFrame
from tqdm import tqdm
import geopy

# Own modules
from trackanimation import utils as trk_utils
from trackanimation.utils import TrackException


class DFTrack:

	def __init__(self, df_points=None, columns=None):
		if df_points is None:
			self.df = DataFrame()

		if isinstance(df_points, pd.DataFrame):
			self.df = df_points
		else:
			if columns is None:
				columns = ['CodeRoute', 'Latitude', 'Longitude', 'Altitude', 'Date', 
								'Speed', 'TimeDifference', 'Distance', 'FileName']
			self.df = DataFrame(df_points, columns=columns)


	def export(self, filename='exported_file', export_format='csv'):
		"""
		Export a data frame of DFTrack to JSON or CSV.

		Parameters
		----------
		export_format: string
			Format to export: JSON or CSV
		filename: string
			Name of the exported file
		"""
		if export_format.lower() == 'json':
			self.df.reset_index().to_json(orient='records', path_or_buf=filename+'.json')
		elif export_format.lower() == 'csv':
			self.df.to_csv(path_or_buf=filename+'.csv')
		else:
			raise TrackException('Must specify a valid format to export', "'%s'" % export_format)


	def getTracks(self):
		"""
		Makes a copy of the DFTrack.

		Explanation: 
			http://stackoverflow.com/questions/27673231/why-should-i-make-a-copy-of-a-data-frame-in-pandas

		Returns
		-------
		copy: DFTrack
			The copy of DFTrack.
		"""
		return self.__class__(self.df.copy(), list(self.df))


	def sort(self, column_name):
		"""
		Sorts the data frame by the specified column.

		Parameters
		----------
		column_name: string
			Column name to sort

		Returns
		-------
		sort: DFTrack
			DFTrack sorted
		"""
		if isinstance(column_name, list):
			for column in column_name:
				if column not in self.df:
					raise TrackException('Column name not found', "'%s'" % column)
		else:
			if column_name not in self.df:
				raise TrackException('Column name not found', "'%s'" % column_name)

		return self.__class__(self.df.sort_values(column_name), list(self.df))


	def getTracksByPlace(self, place, timeout=10, only_points=True):
		"""
		Gets the points of the specified place searching in Google's API
		and, if it does not get anything, it tries with OpenStreetMap's API.

		Parameters
		----------
		place: string
			Place to get the points
		timeout: int
			Time, in seconds, to wait for the geocoding service to respond 
			before returning a None value.
		only_points: boolean
			True to retrieve only the points that cross a place. False to
			retrive all the points of the tracks that cross a place.

		Returns
		-------
		place: DFTrack
			A DFTrack with the points of the specified place or 
			None if anything is found.
		"""
		track_place = self.getTracksByPlaceGoogle(place, timeout=timeout, only_points=only_points)
		if track_place is not None:
			return track_place

		track_place = self.getTracksByPlaceOSM(place, timeout=timeout, only_points=only_points)
		if track_place is not None:
			return track_place

		return None


	def getTracksByPlaceGoogle(self, place, timeout=10, only_points=True):
		"""
		Gets the points of the specified place searching in Google's API.

		Parameters
		----------
		place: string
			Place to get the points
		timeout: int
			Time, in seconds, to wait for the geocoding service to respond 
			before returning a None value.
		only_points: boolean
			True to retrieve only the points that cross a place. False to
			retrive all the points of the tracks that cross a place.

		Returns
		-------
		place: DFTrack
			A DFTrack with the points of the specified place or 
			None if anything is found.
		"""
		try:
			geolocator = geopy.GoogleV3()
			location = geolocator.geocode(place, timeout=timeout)
		except geopy.exc.GeopyError as geo_error:
			return None

		southwest_lat = float(location.raw['geometry']['bounds']['southwest']['lat'])
		northeast_lat = float(location.raw['geometry']['bounds']['northeast']['lat'])
		southwest_lng = float(location.raw['geometry']['bounds']['southwest']['lng'])
		northeast_lng = float(location.raw['geometry']['bounds']['northeast']['lng'])

		df_place = self.df[(self.df['Latitude'] < northeast_lat) & (self.df['Longitude'] < northeast_lng) & 
				(self.df['Latitude'] > southwest_lat) & (self.df['Longitude'] > southwest_lng)]

		if only_points:
			return self.__class__(df_place)

		track_list = df_place['CodeRoute'].unique().tolist()
		return self.__class__(self.df[self.df['CodeRoute'].isin(track_list)])


	def getTracksByPlaceOSM(self, place, timeout=10, only_points=True):
		"""
		Gets the points of the specified place searching in OpenStreetMap's API.

		Parameters
		----------
		place: string
			Place to get the points
		timeout: int
			Time, in seconds, to wait for the geocoding service to respond 
			before returning a None value.
		only_points: boolean
			True to retrieve only the points that cross a place. False to
			retrive all the points of the tracks that cross a place.

		Returns
		-------
		place: DFTrack
			A DFTrack with the points of the specified place or 
			None if anything is found.
		"""
		try:
			geolocator = geopy.Nominatim()
			location = geolocator.geocode(place, timeout=timeout)
		except geopy.exc.GeopyError as geo_error:
			return None

		southwest_lat = float(location.raw['boundingbox'][0])
		northeast_lat = float(location.raw['boundingbox'][1])
		southwest_lng = float(location.raw['boundingbox'][2])
		northeast_lng = float(location.raw['boundingbox'][3])

		df_place = self.df[(self.df['Latitude'] < northeast_lat) & (self.df['Longitude'] < northeast_lng) & 
				(self.df['Latitude'] > southwest_lat) & (self.df['Longitude'] > southwest_lng)]

		if only_points:
			return self.__class__(df_place)

		track_list = df_place['CodeRoute'].unique().tolist()
		return self.__class__(self.df[self.df['CodeRoute'].isin(track_list)])


	def getTracksByDate(self, start=None, end=None, periods=None, freq='D'):
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
		if trk_utils.isTimeFormat(start) or trk_utils.isTimeFormat(end):
			raise TrackException('Must specify an appropiate date format', 'Time format found')

		rng = pd.date_range(start=start, end=end, periods=periods, freq=freq)
		
		df_date = self.df.copy()
		df_date['Date'] = pd.to_datetime(df_date['Date'])
		df_date['ShortDate'] = df_date['Date'].apply(lambda date: date.date().strftime('%Y-%m-%d'))
		df_date = df_date[df_date['ShortDate'].apply(lambda date: date in rng)]
		del df_date['ShortDate']

		df_date = df_date.reset_index(drop=True)

		return self.__class__(df_date, list(df_date))


	def getTracksByTime(self, start, end, include_start=True, include_end=True):
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
		if not trk_utils.isTimeFormat(start) or not trk_utils.isTimeFormat(end):
			raise TrackException('Must specify an appropiate time format', trk_utils.TIME_FORMATS)

		df_time = self.df.copy()

		index = pd.DatetimeIndex(df_time['Date'])
		df_time = df_time.iloc[index.indexer_between_time(start_time=start, end_time=end, include_start=include_start, include_end=include_end)]

		df_time = df_time.reset_index(drop=True)

		return self.__class__(df_time, list(df_time))


	def pointVideoNormalize(self):
		df = self.df.copy()

		df_norm = pd.DataFrame()
		group_size = df.groupby('CodeRoute').size()
		max_value = group_size.max()
		name_max_value = group_size.idxmax()

		grouped = df['CodeRoute'].unique()

		for name in tqdm(grouped, desc='Groups'):
			df_slice = df[df['CodeRoute'] == name]
			df_slice = df_slice.reset_index(drop=True)
			div = int(max_value / len(df_slice)) + 1
			df_index = DataFrame(df_slice.index)
			df_slice['VideoFrame'] = df_index.apply(lambda x: x + 1 if name_max_value == name else x * div) 
			df_norm = pd.concat([df_norm, df_slice])

		df_norm = df_norm.reset_index(drop=True)

		return self.__class__(df_norm, list(df_norm))


	def timeVideoNormalize(self, time, framerate=5):
		df = self.df.copy()
		if time == 0:
			df['VideoFrame'] = 0
			df = df.reset_index(drop=True)
			return self.__class__(df, list(df))

		n_fps = time*framerate
		df = df.sort_values('Date')
		df_cum = trk_utils.calculateCumTimeDiff(df)
		grouped = df_cum['CodeRoute'].unique()

		df_norm = pd.DataFrame()
		point_idx = 1

		for name in tqdm(grouped, desc='Groups'):
			df_slice = df_cum[df_cum['CodeRoute'] == name]
			time_diff = float((df_slice[['TimeDifference']].sum() / time) / framerate) # Track duration divided by time and framerate

			df_range = df_slice[df_slice['CumTimeDiff'] == 0]
			df_range = df_range.reset_index(drop=True)
			df_range['VideoFrame'] = 0
			df_norm = pd.concat([df_norm, df_range])

			for i in tqdm(range(1, n_fps+1), desc='Num FPS', leave=False):
				x_start = time_diff*(i-1)
				x_end = time_diff*i

				df_range = df_slice[(df_slice['CumTimeDiff'] > x_start) & (df_slice['CumTimeDiff'] <= x_end)]
				df_range = df_range.reset_index(drop=True)

				if df_range.empty:
					df_start = df_slice[df_slice['CumTimeDiff'] <= x_start].tail(1)
					df_end = df_slice[df_slice['CumTimeDiff'] > x_end].head(1)

					if not df_start.empty and not df_end.empty:
						df_middlePoint = trk_utils.getPointInTheMiddle(df_start, df_end, time_diff, point_idx)
						df_range = DataFrame(df_middlePoint, columns=list(df_cum))

					point_idx = point_idx + 1
				else:
					point_idx = 1

				df_range['VideoFrame'] = i
				df_norm = pd.concat([df_norm, df_range])
		df_norm = df_norm.reset_index(drop=True)

		return self.__class__(df_norm, list(df_norm))


	def setColors(self, column_name, individual_tracks=True):
		if column_name not in self.df:
			raise TrackException('Column name not found', "'%s'" % column_name)

		df = self.df.copy()

		df_colors = pd.DataFrame()

		if individual_tracks:
			grouped = df['CodeRoute'].unique()

			for name in grouped:
				df_slice = df[df['CodeRoute'] == name]
				df_slice = df_slice.reset_index(drop=True)

				min = df_slice[column_name].min()
				max = df_slice[column_name].max()

				df_slice['Color'] = df_slice[column_name].apply(trk_utils.rgb, minimum=min, maximum=max)
				df_colors = pd.concat([df_colors, df_slice])

			df_colors = df_colors.reset_index(drop=True)
			return self.__class__(df_colors, list(df_colors))
		else:
			min = df[column_name].min()
			max = df[column_name].max()

			df['Color'] = df[column_name].apply(trk_utils.rgb, minimum=min, maximum=max) 
			df = df.reset_index(drop=True)

			return self.__class__(df, list(df))
			

	def dropDuplicates(self):
		"""
		Drop points of the same track with the same Latitude and Longitude.
		"""
		return self.__class__(self.df.drop_duplicates(['CodeRoute', 'Latitude', 'Longitude']))


	def toDict(self):
		"""
		Convert de data frame to a dictionary 
		like [{column -> value}, ... , {column -> value}]
		"""
		return self.df.to_dict('records')


	def getBounds(self):
		"""
		Get the bounds of the DFTrack
			
		Returns
		-------
		bounds: gpxpy.GPXBounds
		"""
		min_lat = self.df['Latitude'].min()
		max_lat = self.df['Latitude'].max()
		min_lng = self.df['Longitude'].min()
		max_lng = self.df['Longitude'].max()

		return GPXBounds(min_lat, max_lat, min_lng, max_lng)


	def concat(self, dfTrack):
		"""
		Concatenate DFTrack objects with 'self'

		Parameters
		----------
		dfTrack: DFTrack or list of DFTrack
			The ones that will be joined with 'self'
			
		Returns
		-------
		df_concat: DFTrack
			A DFTrack with the all the DFTrack concatenated
		"""
		if not isinstance(dfTrack, list):
			# If it is not a list of DFTrack, make a list of one element
			dfTrack = [dfTrack]

		df_concat = [self.df]  # First element is 'self'

		# From list of 'dfTrack', create a list of their dataframes
		for df in dfTrack:
			if not isinstance(df, DFTrack):
				raise TrackException("Parameter must be a 'DFTrack' object", '%s found' % type(df))

			df_concat.append(df.df) 

		return self.__class__(pd.concat(df_concat))


class ReadTrack:

	def __init__(self, directory_or_file):
		self.directory_or_file = directory_or_file
		self.points_list = []


	def readGPXFile(self, filename):
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

						timeDifference = point.time_difference(prev_point)
						if timeDifference is None:
							timeDifference = 0

						distance = point.distance_3d(prev_point)
						if not distance:
							distance = point.distance_2d(prev_point)
						if distance is None:
							distance = 0

						self.points_list.append([code_route, point.latitude, point.longitude, point.elevation, 
							point.time, speed, timeDifference, distance, gpx.name])

						prev_point = point
				except Exception as e:
					raise TrackException('GPX file "' + filename + '" malformed', e)
		except FileNotFoundError as e:
			raise TrackException('GPX file "' + filename + '" not found', e)


	def readGPX(self, files_to_read=None):
		if self.directory_or_file.lower().endswith(('.gpx')):
			self.readGPXFile(self.directory_or_file)
		else:
			n_file_read = 1
			for file in tqdm(glob.glob(self.directory_or_file + "*.gpx"), desc='Reading files'):
				try:
					self.readGPXFile(file)
				except TrackException as e:
					pass

				if files_to_read == n_file_read:
					break
				n_file_read += 1

		return DFTrack(self.points_list)


	def readCSV(self):
		try:
			return DFTrack(pd.read_csv(self.directory_or_file, sep=',', header=0, index_col=0))
		except FileNotFoundError as e:
			raise TrackException('CSV file not found', e)