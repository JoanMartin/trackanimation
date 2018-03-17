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


# Own modules
import trackanimation
from trackanimation.animation import AnimationTrack

# Simple example
input_directory = "example-routes/"
ibiza_trk = trackanimation.read_track(input_directory)

fig = AnimationTrack(df_points=ibiza_trk, dpi=300, bg_map=True, map_transparency=0.5)
fig.make_video(output_file='simple-example', framerate=60, linewidth=1.0)

# Filtering by place and normalizing
input_directory = "example-routes/"
ibiza_trk = trackanimation.read_track(input_directory)
sant_josep_trk = ibiza_trk.getTracksByPlace('Sant Josep de sa Talaia', only_points=False)
sant_josep_trk = sant_josep_trk.time_video_normalize(time=10, framerate=10)

fig = AnimationTrack(df_points=sant_josep_trk, dpi=300, bg_map=True, map_transparency=0.5)
fig.make_video(output_file='filtering-by-place', framerate=10, linewidth=1.0)

# Coloring tracks by their speed
input_directory = "example-routes/ibiza.csv"
ibiza_trk = trackanimation.read_track(input_directory)
ibiza_trk = ibiza_trk.time_video_normalize(time=10, framerate=10)
ibiza_trk = ibiza_trk.set_colors('Speed', individual_tracks=True)

fig = AnimationTrack(df_points=ibiza_trk, dpi=300, bg_map=True, map_transparency=0.5)
fig.make_video(output_file='coloring-map-by-speed', framerate=10, linewidth=1.0)

# Variable 'bg_map' must be to False in order to create an interactive map
fig = AnimationTrack(df_points=ibiza_trk, dpi=300, bg_map=False, map_transparency=0.5)
fig.make_map(output_file='coloring-map-by-speed')

# Multiple axes
input_directory = "example-routes/"
ibiza_trk = trackanimation.read_track(input_directory)
sant_josep_trk = ibiza_trk.get_tracks_by_place('Sant Josep de sa Talaia', only_points=False)

ibiza_trk = ibiza_trk.set_colors('Speed', individual_tracks=True)
sant_josep_trk = sant_josep_trk.set_colors('Speed', individual_tracks=True)

fig = AnimationTrack(df_points=[ibiza_trk, sant_josep_trk], dpi=300, bg_map=True, map_transparency=0.5)
fig.make_image(output_file='multiple-axes')
