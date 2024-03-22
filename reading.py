import os
import re
import time
import pandas as pd
from tqdm import tqdm
downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')

filename = "Apple Music - Play History Daily Tracks.csv"

file_dir = os.path.join(downloads_dir, filename)

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

        os.makedirs(os.path.expanduser('~/Downloads/AppleMusicStats/Artists'), exist_ok=True)
        os.makedirs(os.path.expanduser('~/Downloads/AppleMusicStats/Artists/MultipleArtists'), exist_ok=True)

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
            try:
                with open(os.path.expanduser(f'~/Downloads/AppleMusicStats/Artists/{safe_artist_filename}.txt'), 'w', encoding='utf-8') as artist_file:
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
        print(":( it took soooooooooooo long to write this code :3")
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

print(f"\nAppleMusicStats successfully written to {os.path.expanduser('~/Downloads/AppleMusicStats')}")

TOTAL_FILES = 0
for dirpath, dirnames, filenames in os.walk(os.path.expanduser('~/Downloads/AppleMusicStats')):
    print(f'\n{dirpath}')
    LINE_COUNT = 0
    for filename in filenames:
        TOTAL_FILES += 1
        if LINE_COUNT < 15:
            print(f'├── {filename}')
            LINE_COUNT += 1
    if LINE_COUNT >= 15:
        print(f"... and {len(filenames) - 15 if len(filenames) > 15 else 0} more files in this directory.")

print(f"\nTotal files: {TOTAL_FILES}")

input("\nPress enter to view your stats :)")

os.system("start " + os.path.expanduser('~/Downloads/AppleMusicStats'))
