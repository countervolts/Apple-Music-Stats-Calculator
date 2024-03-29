import os
import re
import shutil
import time
import platform
from datetime import datetime
import pandas as pd
from tqdm import tqdm

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
    artist = row['Track Description'].split(' - ')[0]
    if ' & ' in artist:
        main_artist = artist.split(' & ')[0]
    else:
        main_artist = artist
    df.at[i, 'Artist'] = main_artist
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
        print("it took soooooooooooo long to write this code u suck pls use it >:(")
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

    # Initialize variables to keep track of the most streamed month
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

        # Check if this month has more streams than the current most streamed month
        if streams > max_streams:
            max_streams = streams
            most_streamed_month = name
            most_streamed_month_data = group

    # Write the most streamed month data to a file
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

def print_directory_contents(path, prefix=""):
    expanded_path = os.path.expanduser(path)
    if os.path.exists(expanded_path):
        num_files = len([f for f in os.listdir(expanded_path) if os.path.isfile(os.path.join(expanded_path, f))])
        num_dirs = len([d for d in os.listdir(expanded_path) if os.path.isdir(os.path.join(expanded_path, d))])
        print(f"\n{'*' * 30}")
        print(f"{prefix}")
        print(f"Number of files: {num_files}")
        print(f"Number of folders: {num_dirs}")
        print(f"{'*' * 30}\n")
        for child in os.listdir(expanded_path):
            child_path = os.path.join(expanded_path, child)
            if os.path.isdir(child_path) and child != 'Monthly':
                print_directory_contents(child_path, prefix=f"{prefix}/{child}")
            elif child == 'Monthly':
                print(f"Skipping contents of {prefix}/{child} (too many folders to display!)")

print("Here are the created files:")
print_directory_contents('~/Downloads/AppleMusicStats', prefix="/AppleMusicStats")

input("Press enter to view your stats :)")

if platform.system() == "Windows":
    os.system("start " + os.path.expanduser('~/Downloads/AppleMusicStats'))
else:
    os.system("xdg-open " + os.path.expanduser('~/Downloads/AppleMusicStats'))
