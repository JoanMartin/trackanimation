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
import io
import subprocess
try:
	# Python 3
	from itertools import zip_longest
except ImportError:
	# Python 2
	from itertools import izip_longest as zip_longest

# Third party modules
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # Attention: include the .use('agg') before importing pyplot: DISPLAY issues
import mplleaflet
import numpy as np
from PIL import Image
from tqdm import tqdm
import smopy

# Own modules
from trackanimation.tracking import DFTrack
from trackanimation.utils import TrackException


class AnimationTrack:

	def __init__(self, df_points, dpi=100, bg_map=True, map_transparency=0.5):
		if not isinstance(df_points, list):
			df_points = [df_points]

		self.fig, self.axarr = plt.subplots(len(df_points), 1, facecolor='0.05', dpi=dpi)
		if not isinstance(self.axarr, np.ndarray):
			self.axarr = [self.axarr]

		self.map = []
		self.track_df = DFTrack()
		for i in range(len(df_points)):
			df = df_points[i].getTracks()	
			df.df['Axes'] = i
			self.track_df = self.track_df.concat(df)

			trk_bounds = df.getBounds()
			min_lat = trk_bounds.min_latitude
			max_lat = trk_bounds.max_latitude
			min_lng = trk_bounds.min_longitude
			max_lng = trk_bounds.max_longitude
			if bg_map:
				self.map.append(smopy.Map((min_lat, min_lng, max_lat, max_lng)))
				self.axarr[i].imshow(self.map[i].img, aspect='auto', alpha=map_transparency)
			else:
				self.axarr[i].set_ylim([min_lat, max_lat])
				self.axarr[i].set_xlim([min_lng, max_lng])

			self.axarr[i].set_facecolor('0.05')
			self.axarr[i].tick_params(color='0.05', labelcolor='0.05')
			for spine in self.axarr[i].spines.values():
				spine.set_edgecolor('white')

		self.fig.tight_layout()
		plt.subplots_adjust(wspace=0.1, hspace=0.1)

		if 'VideoFrame' in self.track_df.df:
			self.track_df = self.track_df.sort(['VideoFrame', 'Axes', 'CodeRoute'])
		else:
			self.track_df = self.track_df.sort(['Axes', 'Date'])

		self.track_df.df = self.track_df.df.reset_index(drop=True)


	def computePoints(self, track_df=None, linewidth=0.5):
		track_points = {}

		if track_df is None:
			points = self.track_df.toDict()
		else:
			points = track_df.toDict()

		for point, next_point in zip_longest(tqdm(points, desc='Computing points'), points[1:], fillvalue=None):
			track_code = str(point['CodeRoute']) + "_" + str(point['Axes'])

			# Check if the track is in the data structure
			if track_code in track_points:
				position = track_points[track_code]

				if len(position['lat']) > 1 and len(position['lng']) > 1:
					del position['lat'][0]
					del position['lng'][0]
					
				# Remove plotted line
				# for axarr in self.axarr:
				# 	for c in axarr.get_lines():
				# 		if c.get_gid() == track_code:
				# 			c.remove()
			else:
				position = {}
				position['lat'] = []
				position['lng'] = []

			lat = point['Latitude']
			lng = point['Longitude']
			if self.map:
				lng, lat = self.map[int(point['Axes'])].to_pixels(lat, lng)

			position['lat'].append(lat)
			position['lng'].append(lng)
			track_points[track_code] = position

			if 'Color' in point:
				self.axarr[int(point['Axes'])].plot(position['lng'], position['lat'], color=point['Color'], lw=linewidth, alpha=1)
			else:
				self.axarr[int(point['Axes'])].plot(position['lng'], position['lat'], color='deepskyblue', lw=linewidth, alpha=1)

			yield point, next_point


	def computeTracks(self, linewidth=0.5):
		df = self.track_df.getTracks().df

		df['track_code'] = df['CodeRoute'].map(str) + '_' + df['Axes'].map(str)
		grouped = df['track_code'].unique()

		for name in tqdm(grouped, desc='Groups'):
			df_slice = df[df['track_code'] == name]

			lat = df_slice['Latitude'].values
			lng = df_slice['Longitude'].values
			if self.map:
				lng, lat = self.map[int(df_slice['Axes'].unique())].to_pixels(lat, lng)

			self.axarr[int(df_slice['Axes'].unique())].plot(lng, lat, color='deepskyblue', lw=linewidth, alpha=1)


	def makeVideo(self, linewidth=0.5, output_file='video', framerate=5):
		cmdstring = ('ffmpeg',
			'-y',
			'-loglevel', 'quiet',
			'-framerate', str(framerate),
			'-f', 'image2pipe',
			'-i', 'pipe:',
			'-r', '25',
			'-s','1280x960',
			'-pix_fmt','yuv420p',
			output_file + '.mp4'
		)

		pipe = subprocess.Popen(cmdstring, stdin=subprocess.PIPE)

		for axarr in self.axarr:
			axarr.lines = []

		for point, next_point in self.computePoints(linewidth=linewidth):
			if self.isNewFrame(point, next_point):
				buffer = io.BytesIO()
				canvas = plt.get_current_fig_manager().canvas
				canvas.draw()
				pil_image = Image.frombytes('RGB', canvas.get_width_height(), canvas.tostring_rgb())
				pil_image.save(buffer, 'PNG')
				buffer.seek(0)
				pipe.stdin.write(buffer.read())

		pipe.stdin.close()


	def makeMap(self, linewidth=2.5, output_file='map'):
		for axarr in self.axarr:
			axarr.lines = []

		if self.map:
			raise TrackException('Map background found in the figure', 'Remove it to create an interactive HTML map.')

		if 'Color' in self.track_df.df:
			for point, next_point in self.computePoints(linewidth=linewidth):
				pass
		else:
			self.computeTracks(linewidth=linewidth)

		mplleaflet.save_html(fig=self.fig, tiles='esri_aerial',	 fileobj=output_file + '.html')#, close_mpl=False) # Creating html map


	def makeImage(self, linewidth=0.5, output_file='image', framerate=5, save_fig_at=None):
		for axarr in self.axarr:
			axarr.lines = []

		frame = 1
		if save_fig_at is not None or 'Color' in self.track_df.df:
			if not isinstance(save_fig_at, list):
				# If it is not a list, make a list of one element
				save_fig_at = [save_fig_at]

			for point, next_point in self.computePoints(linewidth=linewidth):
				if self.isNewFrame(point, next_point):
					second = frame / framerate
					if second in save_fig_at:
						plt.savefig(output_file + '_' + str(second) + '.png', facecolor=self.fig.get_facecolor())
					frame = frame + 1
		else:
			self.computeTracks(linewidth=linewidth)

		plt.savefig(output_file + '.png', facecolor=self.fig.get_facecolor())



	def isNewFrame(self, point, next_point):
		if next_point is not None:
			if 'VideoFrame' in point:
				new_frame = point['VideoFrame'] != next_point['VideoFrame']
			else:
				new_frame = point['Date'] != next_point['Date']		
		else:
			new_frame = False

		return new_frame