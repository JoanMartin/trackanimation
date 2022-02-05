import pandas
import tqdm

try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest

def calculate_lat_lon(lat_given, lon_given, iter_axis):
    lat = lat_given
    lon = lon_given

    # if map:
    #     lon, lat = map[int(iter_axis)].to_pixels(lat, lon)

    return lat, lon

def calculate_dict_position(dict_points_track, dict_point):

    track_code = str(dict_point['CodeRoute']) + "_" + str(dict_point['Axes'])
    lat, lon = calculate_lat_lon(
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

        # plot_line(self.list_axes, int(point['Axes']), dict_position['lat'], dict_position['lon'], 
        #         color = point.get('Color', 'deepskyblue'), lw = lw, alpha=1)

        yield point, next_point

def plot_points_track(dft, lw=0.5):
    df = dft.copy()

    # process dataframe
    df.loc[:, 'track_code'] = df['CodeRoute'].map(str) + '_' + df['Axes'].map(str)
    groups_track_codes = df.groupby('track_code')

    for track_code, track_code_df in tqdm.tqdm(groups_track_codes, desc='Track codes'):

        lat, lon = calculate_lat_lon(
            track_code_df['Latitude'].values, track_code_df['Longitude'].values, track_code_df['Axes'].unique())

        # plot_line(self.list_axes, int(track_code_df['Axes'].unique()), lat, lon, 
        #     color = 'deepskyblue', lw = lw, alpha=1)
    
