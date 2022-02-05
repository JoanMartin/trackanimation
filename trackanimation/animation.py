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
import numpy
import PIL
import tqdm
import smopy

# Own modules
from trackanimation.tracking import DFTrack
from trackanimation.utils import TrackException

def plot_line(list_axes, iterable, lat, lon, **kwargs):
    list_axes[iterable].plot(lon, lat, **kwargs)

    return

class AnimationTrack:
    def __init__(self, list_dfts, dpi=100, bg_map=True, aspect='equal', map_transparency=0.5):
        if not isinstance(list_dfts, list):
            list_dfts = [list_dfts]

        self.fig, self.list_axes = plt.subplots(len(list_dfts), 1, facecolor='0.05', dpi=dpi)
        if not isinstance(self.list_axes, numpy.ndarray):
            self.list_axes = [self.list_axes]

        self.map = []
        self.dft = DFTrack()
        for i, dfts in enumerate(list_dfts):
            df = dfts.get_copy()
            df.df['Axes'] = i
            self.dft = self.dft.concat_dfts(df)

            trk_bounds = df.get_bounds()
            min_lat = trk_bounds.min_latitude
            max_lat = trk_bounds.max_latitude
            min_lon = trk_bounds.min_longitude
            max_lon = trk_bounds.max_longitude
            if bg_map:
                self.map.append(smopy.Map((min_lat, min_lon, max_lat, max_lon)))
                self.list_axes[i].imshow(self.map[i].img, aspect=aspect, alpha=map_transparency)
            else:
                self.list_axes[i].set_ylim([min_lat, max_lat])
                self.list_axes[i].set_xlim([min_lon, max_lon])

            self.list_axes[i].set_facecolor('0.05')
            self.list_axes[i].tick_params(color='0.05', labelcolor='0.05')
            for spine in self.list_axes[i].spines.values():
                spine.set_edgecolor('white')

        self.fig.tight_layout()
        plt.subplots_adjust(wspace=0.1, hspace=0.1)

        if 'VideoFrame' in self.dft.df:
            self.dft = self.dft.sort_columns(['VideoFrame', 'Axes', 'CodeRoute'])
        else:
            self.dft = self.dft.sort_columns(['Axes', 'Date'])

        self.dft.df = self.dft.df.reset_index(drop=True)

    def calculate_lat_lon(self, lat_given, lon_given, iter_axis):
        lat = lat_given
        lon = lon_given

        if self.map:
            lon, lat = self.map[int(iter_axis)].to_pixels(lat, lon)

        return lat, lon

    def calculate_dict_position(self, dict_points_track, dict_point):

        track_code = str(dict_point['CodeRoute']) + "_" + str(dict_point['Axes'])
        lat, lon = self.calculate_lat_lon(
            dict_point['Latitude'], dict_point['Longitude'], dict_point['Axes'])

        dict_position = dict_points_track.get(track_code, {'lat': [], 'lon': []}) # default

        if len(dict_position['lat']) > 1 and len(dict_position['lon']) > 1:
            del dict_position['lat'][0]
            del dict_position['lon'][0]

            # Remove plotted line
            # for axarr in self.list_axes:
            # 	for c in axarr.get_lines():
            # 		if c.get_gid() == track_code:
            # 			c.remove()

        dict_position['lat'].append(lat)
        dict_position['lon'].append(lon)

        return dict_position, track_code

    def generate_points(self, dft=None, lw=0.5):
        dict_points_track = {}

        if dft is None:
            list_dict_points = self.dft.to_dict('records')
        else:
            list_dict_points = dft.to_dict('records')

        iter_unpack = zip_longest(tqdm.tqdm(list_dict_points, desc='Computing points'), list_dict_points[1:], fillvalue=None)
        for point, next_point in iter_unpack:

            dict_position, track_code = self.calculate_dict_position(dict_points_track, point)
            dict_points_track[track_code] = dict_position

            plot_line(self.list_axes, int(point['Axes']), dict_position['lat'], dict_position['lon'], 
                    color = point.get('Color', 'deepskyblue'), lw = lw, alpha=1)

            yield point, next_point

    def plot_points_track(self, lw=0.5):
        df = self.dft.get_copy().df

        # process dataframe
        df.loc[:, 'track_code'] = df['CodeRoute'].map(str) + '_' + df['Axes'].map(str)
        groups_track_codes = df.groupby('track_code')

        for track_code, track_code_df in tqdm.tqdm(groups_track_codes, desc='Track codes'):

            lat, lon = self.calculate_lat_lon(
                track_code_df['Latitude'].values, track_code_df['Longitude'].values, track_code_df['Axes'].unique())

            plot_line(self.list_axes, int(track_code_df['Axes'].unique()), lat, lon, 
                color = 'deepskyblue', lw = lw, alpha=1)

    def make_video(self, lw=0.5, output_file='video', framerate=5):
        cmdstring = ('ffmpeg',
                     '-y',
                     '-loglevel', 'quiet',
                     '-framerate', str(framerate),
                     '-f', 'image2pipe',
                     '-i', 'pipe:',
                     '-r', '25',
                     '-s', '1280x960',
                     '-pix_fmt', 'yuv420p',
                     output_file + '.mp4'
                     )

        pipe = subprocess.Popen(cmdstring, stdin=subprocess.PIPE)

        for axarr in self.list_axes:
            axarr.lines = []

        for point, next_point in self.generate_points(lw=lw):
            if self.check_frame_new(point, next_point):
                buffer = io.BytesIO()
                canvas = plt.get_current_fig_manager().canvas
                canvas.draw()
                pil_image = PIL.Imagefrombytes('RGB', canvas.get_width_height(), canvas.tostring_rgb())
                pil_image.save(buffer, 'PNG')
                buffer.seek(0)
                pipe.stdin.write(buffer.read())

        pipe.stdin.close()

    def make_map(self, lw=2.5, output_file='map'):
        for axarr in self.list_axes:
            axarr.lines = []

        if self.map:
            raise TrackException('Map background found in the figure', 'Remove it to create an interactive HTML map.')

        if 'Color' in self.dft.df:
            for point, next_point in self.generate_points(lw=lw):
                pass
        else:
            self.plot_points_track(lw=lw)

        mplleaflet.save_html(fig=self.fig, tiles='esri_aerial',
                             fileobj=output_file + '.html')  # , close_mpl=False) # Creating html map

    def make_image(self, lw=0.5, output_file='image', framerate=5, save_fig_at=None):
        for axarr in self.list_axes:
            axarr.lines = []

        frame = 1
        if save_fig_at is not None or 'Color' in self.dft.df:
            if not isinstance(save_fig_at, list):
                save_fig_at = [save_fig_at]

            for point, next_point in self.generate_points(lw=lw):
                if self.check_frame_new(point, next_point):
                    second = frame / framerate
                    if second in save_fig_at:
                        plt.savefig(output_file + '_' + str(second) + '.png', facecolor=self.fig.get_facecolor())
                    frame = frame + 1
        else:
            self.plot_points_track(lw=lw)

        plt.savefig(output_file + '.png', facecolor=self.fig.get_facecolor())

    def check_frame_new(self, point, next_point):
        if next_point is not None:
            if 'VideoFrame' in point:
                return point['VideoFrame'] != next_point['VideoFrame']
            return point['Date'] != next_point['Date']

        return False
