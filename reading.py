import os
import re
import shutil
import time
import requests
import base64
import subprocess
import urllib.parse
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from urllib.parse import quote
from bs4 import BeautifulSoup
#ironicly using spotify api 
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')

filename = "Apple Music - Play History Daily Tracks.csv"

file_dir = os.path.join(downloads_dir, filename)

delete_this = os.path.join(downloads_dir, 'AppleMusicStats')

if not os.path.isfile(file_dir):
    print(f"{filename} was not found.")
    input(f"please extract {filename} to your download and re-run the code please :) \n press enter to exit")

df = pd.read_csv(file_dir, parse_dates=['Date Played'])

pbar = tqdm(total=len(df), desc='Reading CSV', dynamic_ncols=True, position=0, leave=True)

os.system('cls' if os.name == 'nt' else 'clear')

df = df[df['Media type'] != 'VIDEO']

for i, row in df.iterrows():
    pbar.update(1)
    track_description = row['Track Description']
    if isinstance(track_description, str):
        artist = track_description.split(' - ')[0]
        if ' & ' in artist:
            main_artist = artist.split(' & ')[0]
        else:
            main_artist = artist
        df.at[i, 'Artist'] = main_artist
    else:
        df.at[i, 'Artist'] = None
    df.at[i, 'Play Duration Minutes'] = row['Play Duration Milliseconds'] / 60000

pbar.close()

grouped_artist = df.groupby('Artist')['Play Duration Minutes'].sum()
grouped_artist = grouped_artist.apply(lambda x: round(x/60, 1))
top_50_artists = grouped_artist.sort_values(ascending=False).head(50)

grouped_track = df.groupby('Track Description')['Play Duration Minutes'].sum()
grouped_track = grouped_track.apply(lambda x: round(x/60, 1))
top_50_tracks = grouped_track.sort_values(ascending=False).head(50)

streams = len(df)
minutes_streamed = df['Play Duration Minutes'].sum()
hours_streamed = round(minutes_streamed / 60, 1)
max_songs = df['Track Description'].nunique()
different_artists = df['Artist'].nunique()
print(f"\nTotal streams: {streams:,}")
print(f"Total minutes streamed: {round(minutes_streamed, 2):,}")
print(f"Total hours streamed: {hours_streamed:,}")
print(f"Total days streamed: {round(hours_streamed / 24, 1):,}")
print(f"Different tracks: {max_songs:,}")
print(f"Different artists: {different_artists:,}")

print("\nTop 10 Most Streamed Artists:")
print("-" * 30)
for i, (artist, time) in enumerate(top_50_artists.items(), start=1):
    if i > 10:
        break
    minutes = time * 60
    print(f'{i}. "{artist}" - {time} hours ({minutes:,.2f} minutes)')

print("\nTop 10 Most Streamed Tracks:")
print("-" * 30)
for i, (track, time) in enumerate(top_50_tracks.items(), start=1):
    if i > 10:
        break
    minutes = time * 60
    print(f'{i}. "{track}" - {time} hours ({minutes:,.2f} minutes)')

max_artists = len(df['Artist'].unique())
max_songs = len(df['Track Description'].unique())

if os.path.exists(os.path.expanduser('~/Downloads/AppleMusicStats/')):
    shutil.rmtree(os.path.expanduser('~/Downloads/AppleMusicStats/'))

os.makedirs(os.path.expanduser('~/Downloads/AppleMusicStats/'), exist_ok=True)

customize = input('\nWould you like to customize Stats.txt? (Auto generation includes the top 50 songs and artists) (y/n): ')
if customize.lower() == 'y':
    while True:
        num_artists = int(input(f'\nHow many artists would you like to include? (Max: {max_artists}): '))
        if 0 < num_artists <= max_artists:
            top_artists = grouped_artist.sort_values(ascending=False).head(num_artists)
            break
        else:
            print("Invalid input. Please enter a number between 1 and " + str(max_artists))
    while True:
        num_songs = int(input(f'\nHow many songs would you like to include? (Max: {max_songs}): '))
        if 0 < num_songs <= max_songs:
            top_tracks = grouped_track.sort_values(ascending=False).head(num_songs)
            break
        else:
            print("Invalid input. Please enter a number between 1 and " + str(max_songs))
else:
    num_artists = 50
    num_songs = 50
    top_artists = top_50_artists
    top_tracks = top_50_tracks

def create_artist_files(data_frame, top_artists_list, max_artists_count):
    create_artists_folder = input("\nWould you like to create the artists folder? (y/n): ")
    if create_artists_folder.lower() == 'y':
        num_top_artists = int(input(f'\nHow many top artists would you like to create files for? (Max: {max_artists_count}): '))

        error_count = 0
        for artist, time in list(top_artists_list.items())[:num_top_artists]:
            safe_artist = artist.encode('ascii', 'ignore').decode()
            safe_artist_filename = re.sub(r'[\\/*?:"<>|]', "", safe_artist)
            artist_df = data_frame[data_frame['Artist'] == safe_artist]
            if artist_df.empty:
                continue
            total_streaming_time = artist_df['Play Duration Minutes'].sum()
            first_time_streamed = artist_df['Date Played'].min().date()
            max_songs = artist_df['Track Description'].nunique()
            top_songs = artist_df.groupby('Track Description')['Play Duration Minutes'].sum().sort_values(ascending=False).head(10)
            safe_songs = {song.encode('ascii', 'ignore').decode(): time for song, time in top_songs.items()}
            if ',' in safe_artist and safe_artist != 'Tyler, The Creator':
                folder = 'MultipleArtists'
            else:
                folder = 'Artists'
            os.makedirs(os.path.expanduser(f'~/Downloads/AppleMusicStats/{folder}'), exist_ok=True)
            try:
                with open(os.path.expanduser(f'~/Downloads/AppleMusicStats/{folder}/{safe_artist_filename}.txt'), 'w', encoding='utf-8') as artist_file:
                    artist_file.write(f"Artist: {safe_artist}\n")
                    artist_file.write(f"Total streaming time: {total_streaming_time:,.2f} minutes\n")
                    artist_file.write(f"First time streamed: {first_time_streamed}\n")
                    artist_file.write(f"Different tracks: {max_songs:,}\n\n")
                    artist_file.write("Top 10 Most Played Songs:\n")
                    for song, time in safe_songs.items():
                        artist_file.write(f'"{song}" - {time:,.2f} minutes\n')
            except UnicodeEncodeError as unicode_error:
                error_count += 1
                with open(os.path.expanduser('~/Downloads/AppleMusicStats/ErrorArtists.txt'), 'a', encoding='utf-8') as error_file:
                    error_file.write(f"Artist: {safe_artist}\n")
                    error_file.write(f"Error: {str(unicode_error)}\n")
                    error_file.write(f"Number of errored artists: {error_count} out of {max_artists_count}\n\n")
            except OSError as os_error:
                print(f"Failed to open file for artist: {safe_artist_filename}")
                print(f"Error: {os_error}")
    else:
        print("\n")
create_artist_files(df, top_artists, max_artists)
                            
with open(os.path.expanduser('~/Downloads/AppleMusicStats/Stats.txt'), 'w') as f:
    f.write(f"Total streams: {streams:,}\n")
    f.write(f"Total minutes streamed: {round(minutes_streamed, 2):,}\n")
    f.write(f"Total hours streamed: {hours_streamed:,}\n")
    f.write(f"Total days streamed: {round(hours_streamed / 24, 1):,}\n")
    f.write(f"Different tracks: {max_songs:,}\n")
    f.write(f"Different artists: {different_artists:,}\n\n")
    f.write(f"Top {num_artists} Most Streamed Artists:\n")
    f.write("-" * 30 + "\n")
    for artist, time in list(top_artists.items())[:num_artists]:
        safe_artist = artist.encode('ascii', 'ignore').decode()
        artist_df = df[df['Artist'] == safe_artist]
        if artist_df.empty:
            continue
        minutes = time * 60
        first_listened = artist_df['Date Played'].min().date()
        first_song = artist_df['Track Description'].iloc[0]
        most_streamed_song = artist_df.groupby('Track Description')['Play Duration Minutes'].sum().idxmax()
        most_streamed_song_time = artist_df.groupby('Track Description')['Play Duration Minutes'].sum().max()
        most_streamed_song_time_hours = round(most_streamed_song_time / 60, 1)
        try:
            f.write(f'"{safe_artist}"\n')
            f.write(f'   -> first listened on: {first_listened}\n')
            f.write(f'   -> first song streamed: {first_song}\n')
            f.write(f'   -> total listening time: {time} hours ({minutes:,.2f} minutes)\n')
            f.write(f'   -> most streamed song: {most_streamed_song} - {most_streamed_song_time_hours} hours ({most_streamed_song_time:,.2f} minutes)\n\n')
        except UnicodeEncodeError as e:
            with open(os.path.expanduser('~/Downloads/AppleMusicStats/ErrorArtists.txt'), 'a') as error_file:
                error_file.write(f"Artist: {safe_artist}\n")
                error_file.write(f"Error: {str(e)}\n\n")

    f.write(f"\nTop {num_songs} Most Streamed Tracks:\n")
    f.write("-" * 30 + "\n")
    for track, time in list(top_tracks.items())[:num_songs]:
        safe_track = track.encode('ascii', 'ignore').decode()
        minutes = time * 60
        first_listened = df[df['Track Description'] == safe_track]['Date Played'].min().date()
        try:
            f.write(f'"{safe_track}"\n')
            f.write(f'   -> listened for {time} hours ({minutes:,.2f} minutes)\n')
            f.write(f'   -> first listened on {first_listened}\n\n')
        except UnicodeEncodeError as e:
            with open(os.path.expanduser('~/Downloads/AppleMusicStats/ErrorSongs.txt'), 'a') as error_file:
                error_file.write(f"Song: {safe_track}\n")
                error_file.write(f"Error: {str(e)}\n\n")

def write_monthly_stats(df):
    monthly_dir = os.path.expanduser('~/Downloads/AppleMusicStats/Monthly')
    os.makedirs(monthly_dir, exist_ok=True)

    df['Date Played'] = pd.to_datetime(df['Date Played'], format='%Y%m%d')
    df['Month'] = df['Date Played'].dt.month_name()
    df['Month Number'] = df['Date Played'].dt.month
    grouped = df.groupby(['Month Number', 'Month'], sort=True)

    max_streams = 0
    most_streamed_month = None
    most_streamed_month_data = None

    for (month_number, name), group in grouped:
        month_dir = os.path.join(monthly_dir, f'{month_number:02d}_{name}')
        os.makedirs(month_dir, exist_ok=True)

        streams = len(group)
        minutes_streamed = group['Play Duration Minutes'].sum()
        hours_streamed = round(minutes_streamed / 60, 1)
        max_songs = group['Track Description'].nunique()
        different_artists = group['Artist'].nunique()

        daily_grouped = group.groupby(group['Date Played'].dt.to_period('D'))
        most_streamed_day = daily_grouped.size().idxmax()
        total_streams_most_streamed_day = daily_grouped.size().max()

        most_streamed_day_data = group[group['Date Played'].dt.to_period('D') == most_streamed_day]
        minutes_streamed_most_streamed_day = most_streamed_day_data['Play Duration Minutes'].sum()
        hours_streamed_most_streamed_day = round(minutes_streamed_most_streamed_day / 60, 1)

        most_streamed_song = group['Track Description'].value_counts().idxmax()
        most_streamed_artist = group['Artist'].value_counts().idxmax()

        file_path = os.path.join(month_dir, f'{name}Stats.txt')
        with open(file_path, 'w') as f:
            f.write(f"Total streams: {streams:,}\n")
            f.write(f"Total minutes streamed: {minutes_streamed:,.2f}\n")
            f.write(f"Total hours streamed: {hours_streamed:,.2f}\n")
            f.write(f"Different tracks: {max_songs:,}\n")
            f.write(f"Different artists: {different_artists:,}\n\n")
            f.write("----------------Monthly Stats----------------\n")
            f.write(f"Most streamed day: {most_streamed_day.strftime('%Y-%m-%d')}\n")
            f.write(f"Total streams on most streamed day: {total_streams_most_streamed_day:,}\n")
            f.write(f"Total minutes streamed on most streamed day: {minutes_streamed_most_streamed_day:,.2f}\n")
            f.write(f"Total hours streamed on most streamed day: {hours_streamed_most_streamed_day:,.2f}\n")
            f.write(f"Most streamed artist: {most_streamed_artist}\n")
            f.write(f"Most streamed song: {most_streamed_song}\n")

        if streams > max_streams:
            max_streams = streams
            most_streamed_month = name
            most_streamed_month_data = group

    most_streamed_song = most_streamed_month_data['Track Description'].value_counts().idxmax()
    most_streamed_artist = most_streamed_month_data['Artist'].value_counts().idxmax()
    minutes_streamed = most_streamed_month_data['Play Duration Minutes'].sum()
    hours_streamed = round(minutes_streamed / 60, 1)

    summary_file_path = os.path.join(monthly_dir, 'Summary.txt')
    with open(summary_file_path, 'w') as f:
        f.write(f"Most streamed month: {most_streamed_month}\n")
        f.write(f"Total streams in most streamed month: {max_streams:,}\n")
        f.write(f"Total minutes streamed in most streamed month: {minutes_streamed:,.2f}\n")
        f.write(f"Total hours streamed in most streamed month: {hours_streamed:,.2f}\n")
        f.write(f"Most streamed artist in most streamed month: {most_streamed_artist}\n")
        f.write(f"Most streamed song in most streamed month: {most_streamed_song}\n")

write_monthly_stats(df)

os.makedirs(os.path.expanduser('~/Downloads/AppleMusicStats/StatsSimplified'), exist_ok=True)

def write_top_artists_func(top_artists_param, num_artists_param):
    with open(os.path.expanduser('~/Downloads/AppleMusicStats/StatsSimplified/TopArtists.txt'), 'w', encoding='utf-8') as f_param:
        f_param.write("Top Artists:\n")
        for i_param, (artist_param, time_param) in enumerate(sorted(top_artists_param.items(), key=lambda x: x[1], reverse=True)[:num_artists_param], start=1):
            minutes_param = time_param * 60
            safe_artist_param = artist_param.encode('ascii', 'ignore').decode()
            try:
                f_param.write(f"{i_param}. {safe_artist_param} - {time_param} hours ({minutes_param:,.2f} minutes)\n")
            except UnicodeEncodeError as e_param:
                with open(os.path.expanduser('~/Downloads/AppleMusicStats/ErrorArtists.txt'), 'a', encoding='utf-8') as error_file_param:
                    error_file_param.write(f"Artist: {safe_artist_param}\n")
                    error_file_param.write(f"Error: {str(e_param)}\n\n")

write_top_artists_func(top_artists, num_artists)

with open(os.path.expanduser('~/Downloads/AppleMusicStats/StatsSimplified/TopSongs.txt'), 'w', encoding='utf-8') as f_param:
    f_param.write("Top Songs:\n")
    for i_param, (song_param, time_param) in enumerate(list(top_tracks.items())[:num_songs], start=1):
        minutes_param = time_param * 60
        safe_song_param = song_param.encode('ascii', 'ignore').decode()
        try:
            f_param.write(f"{i_param}. {safe_song_param} - {time_param} hours ({minutes_param:,.2f} minutes)\n")
        except UnicodeEncodeError as e_param:
            with open(os.path.expanduser('~/Downloads/AppleMusicStats/ErrorSongs.txt'), 'a', encoding='utf-8') as error_file_param:
                error_file_param.write(f"Song: {safe_song_param}\n")
                error_file_param.write(f"Error: {str(e_param)}\n\n")

with open(os.path.expanduser('~/Downloads/AppleMusicStats/StatsSimplified/StatsSimplified.txt'), 'w', encoding='utf-8') as f:
    f.write(f"Total streams: {streams:,}\n")
    f.write(f"Total minutes streamed: {round(minutes_streamed, 2):,}\n")
    f.write(f"Total hours streamed: {hours_streamed:,}\n")
    f.write(f"Total days streamed: {round(hours_streamed / 24, 1):,}\n")
    f.write(f"Different tracks: {max_songs:,}\n")
    f.write(f"Different artists: {different_artists:,}\n\n")

print('\033[91m' + 'from now on, the code will create a website for you to view your stats on,')
print('this will include a website with your top 10 artists and songs, along with general stats')
print('this will be written to a folder in your downloads folder called AppleMusicStats')
print('if you are just running the source code, it wont work, you need to run the executable')
print('otherwise, your stats can be found at ~/Downloads/AppleMusicStats' + '\033[0m' )
user_input = input('Press enter if you would like to continue with website creation, or type "n" to just open the folder with all your stats: ').lower()

if user_input.lower() == 'n':
    stats_folder = os.path.expanduser('~/Downloads/AppleMusicStats')
    subprocess.run(['open', stats_folder])
else:
    print("\nNow writing website code...")
    print("please wait")

    client_id = 'Spotify_API_Is_Free'
    client_secret = 'Spotify_API_Is_Free'

    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def write_spotify_ids(filename, type, ids_filename):
        filename = os.path.expanduser(filename)
        ids_filename = os.path.expanduser(ids_filename)

        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        top_ten = lines[1:11]
        names = [line.split('. ')[1].split(' - ')[0] if type == 'artist' else line.split('. ')[1].split(' - ')[1] for line in top_ten]
        artists = [line.split('. ')[1].split(' - ')[0] for line in top_ten] if type == 'track' else None

        ids = []
        for i, name in enumerate(names):
            query = f'artist:{artists[i]} track:{name}' if type == 'track' else name
            results = sp.search(q=query, type=type, limit=1)
            id = results['tracks']['items'][0]['id'] if type == 'track' else results['artists']['items'][0]['id']
            ids.append(id)

            if type == 'track':
                album = sp.album(results['tracks']['items'][0]['album']['id'])
                image_url = album['images'][0]['url']
            else:
                artist = sp.artist(id)
                image_url = artist['images'][0]['url']

            response = requests.get(image_url)

            safe_name = quote(name, safe='')
            image_filename = os.path.expanduser(f'~/Downloads/AppleMusicStats/Images/{type}s/{safe_name}.jpg')
            os.makedirs(os.path.dirname(image_filename), exist_ok=True)
            with open(image_filename, 'wb') as f:
                f.write(response.content)

        with open(ids_filename, 'w', encoding='utf-8') as f:
            for id in ids:
                f.write(id + '\n')

        return ids

    print("\nCollecting Spotify ID's... :)")

    write_spotify_ids('~/Downloads/AppleMusicStats/StatsSimplified/TopArtists.txt', 'artist',  '~/Downloads/AppleMusicStats/StatsSimplified/TopArtistIDs.txt')
    write_spotify_ids('~/Downloads/AppleMusicStats/StatsSimplified/TopSongs.txt', 'track',     '~/Downloads/AppleMusicStats/StatsSimplified/TopSongIDs.txt')

    print("Collected Spotify ID's... :)\n")

    def upload_to_github(filename, repo, path, token):
        with open(filename, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')

        url = f'https://api.github.com/repos/{repo}/contents/{path}'
        headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
        data = {
            'message': 'ur cute',
            'content': content
        }

        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()

    def upload_to_github(file_path, repo, path_in_repo, github_pat):
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')

        url = f'https://api.github.com/repos/{repo}/contents/{path_in_repo}'
        headers = {'Authorization': f'token {github_pat}'}
        data = {
            'message': f'ur cute :3',
            'content': content
        }
        response = requests.put(url, headers=headers, json=data)

    print('Calling you cute... :3\n')

    def generate_html_content():
        styles_file = 'website/styles.css'
        html_file = 'website/index.html'
        website_folder = 'website'

        if not os.path.exists(website_folder):
            os.makedirs(website_folder)

        print('Checking for necessary files...')

        if not os.path.exists(styles_file):
            print('File not found.. :(')
            url = 'https://raw.githubusercontent.com/countervolts/Apple-Music-Stats-Calculator/main/website/styles.css'
            r = requests.get(url)
            with open(styles_file, 'w') as f:
                f.write(r.text)

        if not os.path.exists(html_file):
            print('File not found.. :(')
            url = 'https://raw.githubusercontent.com/countervolts/Apple-Music-Stats-Calculator/main/website/index.html'
            r = requests.get(url)
            with open(html_file, 'w') as f:
                f.write(r.text)
        print('Files downloaded successfully... :D')

        print('Files located successfully... :D\n')

        github_pat = 'why'

        username = input("Enter your username (up to 16 characters): ")[:16]

        if "/" in username:
            print("you cant have / in ur username cause it will break repo")
            return

        repo = 'countervolts/59problems'
        url = f'https://api.github.com/repos/{repo}/contents/spotify/users/{username}'
        headers = {'Authorization': f'token {github_pat}'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print("already in use re-run code please")
            return
        elif response.status_code != 404:
            print("github or network error")
            return

        base_path = os.path.expanduser('~/Downloads/AppleMusicStats/StatsSimplified')
        artist_file = os.path.join(base_path, 'TopArtists.txt')
        song_file = os.path.join(base_path, 'TopSongs.txt')
        stats_file = os.path.join(base_path, 'StatsSimplified.txt')

        with open(stats_file, 'r') as f:
            stats = f.readlines()

        print('\nDeciding where to put everything... :)')

        stats_html = f"""
        <div class="box">
            <p class="left-text">{username}</p>
            <p class="right-text">{stats[0]}<br>
            {stats[1]}<br>
            {stats[2]}<br>
            {stats[3]}<br>
            {stats[4]}<br>
            {stats[5]}</p>
        </div>
        """
        print('Decided where to put stuff... :)\n')
        print('Writing website code...')

        artists_html = '<div class="box box-left">\n'
        with open(artist_file, 'r') as f:
            artists = f.readlines()[1:11]
            for artist in artists:
                full_name, streams = artist.split(' - ', 1)
                _, name = full_name.split('. ', 1)
                name_without_spaces = name.replace(' ', '')
                artists_html += f"""
                <div class="section">
                    <img src="/applemusic/users/{username}/images/artists/{name_without_spaces}.jpg" alt="{name}">
                    <p>{name}</p>
                    <p>{streams}</p>
                </div>
                """
        artists_html += '</div>\n'

        songs_html = '<div class="box box-right">\n'
        with open(song_file, 'r') as f:
                songs = f.readlines()[1:11]
                for song in songs:
                    _, full_name = song.split('. ', 1)
                    artist_name, song_name, streams = full_name.split(' - ', 2)
                    song_name = re.sub(r' \(feat.*', '', song_name)
                    song_name_without_spaces = song_name.replace(' ', '').replace('/', '').replace('!', '').replace('(',    '').replace(')', '')
                    hours_played = streams.split(' ')[0]
                    songs_html += f"""
                    <div class="section">
                        <img src="/applemusic/users/{username}/images/songs/{song_name_without_spaces}.jpg" alt="{song_name}">
                        <p>{song_name}</p>
                        <p>{hours_played} hours</p>
                    </div>
                    """
        songs_html += '</div>\n'

        styles_file = 'website/styles.css'
        html_file = 'website/index.html'
        website_folder = 'website'

        with open(styles_file, 'r') as f:
            styles = f.read()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
            {styles}
            </style>
        </head>
        <body>
        {stats_html}
        {artists_html}
        {songs_html}
        </body>
        </html>
        """

        print('Wrote all code with no issues... :D')

        soup = BeautifulSoup(html_content, 'html.parser')
        pretty_html = soup.prettify()

        with open('output.html', 'w') as f:
            f.write(pretty_html)

        with open(html_file, 'w') as f:
            f.write(html_content)

        print('Code made pretty... :D')
        github_pat = 'why'
        repo = 'countervolts/59problems'
        upload_to_github('website/index.html', repo, f'applemusic/users/{username}/index.html', github_pat)

        image_dirs = {
            'artists': os.path.expanduser('~/Downloads/AppleMusicStats/Images/artists'),
            'songs': os.path.expanduser('~/Downloads/AppleMusicStats/Images/tracks')
        }

        for image_type, image_dir in image_dirs.items():
            for image_file in os.listdir(image_dir):
                full_path = os.path.join(image_dir, image_file)
                if os.path.isfile(full_path):
                    decoded_image_file = urllib.parse.unquote(image_file)
                    image_file_without_special_chars = re.sub(r'feat*', '', decoded_image_file)
                    image_file_without_special_chars = image_file_without_special_chars.replace(' ', '').replace('/', '').replace('!',  '').replace('(', '').replace(')', '')
                    image_path = f'applemusic/users/{username}/images/{image_type}/{image_file_without_special_chars}'
                    upload_to_github(full_path, repo, image_path, github_pat)

        print(f'your website is located at https://59problems.me/applemusic/users/{username}')

        print('\nWrote code to GitHub repo with no issues!!! :)\n')
    generate_html_content()

    print(f"Stats where also written to {os.path.expanduser('~/Downloads/AppleMusicStats')}")

    input("\nPress Enter to view you stats :)")

    os.system("start " + os.path.expanduser('~/Downloads/AppleMusicStats'))
