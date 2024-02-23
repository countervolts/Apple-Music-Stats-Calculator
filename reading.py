import os
import pandas as pd
from tqdm import tqdm

current_dir = os.path.dirname(os.path.realpath(__file__))

os.system('cls' if os.name == 'nt' else 'clear')

while True:
    contents = os.listdir(current_dir)
    print(f'Current directory: {current_dir}')
    
    csv_files = [item for item in contents if item.endswith('.csv')]
    if csv_files:
        csv_files.sort(key=lambda x: os.path.getsize(os.path.join(current_dir, x)), reverse=True)
        for i, item in enumerate(csv_files, start=1):
            size = os.path.getsize(os.path.join(current_dir, item))
            size_mb = size / (1024 * 1024)
            size_kb = size / 1024
            if size_mb < 1:
                print(f'{i}. {item} - {size_kb:.2f} KB')
            else:
                print(f'{i}. {item} - {size_mb:.2f} MB')
        prompt = 'Pick a CSV: '
    else:
        for i, item in enumerate(contents, start=1):
            print(f'{i}. {item}')
        prompt = 'Enter the number of the item to select: '

    choice = input(prompt)

    try:
        choice = int(choice)
        file_dir = os.path.join(current_dir, csv_files[choice-1] if csv_files else contents[choice-1])
        
        if os.path.isdir(file_dir):
            current_dir = file_dir
            os.system('cls' if os.name == 'nt' else 'clear')  # clear the command line
            continue
        else:
            break
    except (ValueError, IndexError):
        print('Invalid choice, please try again.')

os.system('cls' if os.name == 'nt' else 'clear')

df = pd.read_csv(file_dir, parse_dates=['Date Played'])

pbar = tqdm(total=len(df), desc='Reading CSV', dynamic_ncols=True, position=0, leave=True)

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

df['Artists'] = df['Track Description'].apply(lambda x: x.split(' - ')[0].split(' & '))
all_artists = df.explode('Artists')

grouped_artist = all_artists.groupby('Artists')['Play Duration Minutes'].sum()
grouped_artist = grouped_artist.apply(lambda x: round(x/60, 1))
top_50_artists = grouped_artist.sort_values(ascending=False).head(50)

grouped_track = df.groupby('Track Description')['Play Duration Minutes'].sum()
grouped_track = grouped_track.apply(lambda x: round(x/60, 1))
top_50_tracks = grouped_track.sort_values(ascending=False).head(50)

streams = len(df)
minutes_streamed = df['Play Duration Minutes'].sum()
hours_streamed = round(minutes_streamed / 60, 1)
different_tracks = df['Track Description'].nunique()
different_artists = df['Artist'].nunique()

print(f"\nTotal streams: {streams:,}")
print(f"Total minutes streamed: {round(minutes_streamed, 2):,}")
print(f"Total hours streamed: {hours_streamed:,}")
print(f"Different tracks: {different_tracks:,}")
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

if os.path.exists('Stats.txt'):
    update = input('\nWould you like to update Stats.txt? \n\n(It will contain total streams, total minutes streamed, total hours streamed, number of different tracks, number of different artists, and the top 50 most streamed artists and tracks with their respective hours and minutes listened, and the first time each artist/track was listened to.) (y/n): ')
    if update.lower() != 'y':
        exit()

with open('Stats.txt', 'w') as f:
    f.write(f"Total streams: {streams:,}\n")
    f.write(f"Total minutes streamed: {round(minutes_streamed, 2):,}\n")
    f.write(f"Total hours streamed: {hours_streamed:,}\n")
    f.write(f"Different tracks: {different_tracks:,}\n")
    f.write(f"Different artists: {different_artists:,}\n\n")
    f.write("Top 50 Most Streamed Artists:\n")
    f.write("-" * 30 + "\n")
    for artist, time in top_50_artists.items():
        artist_df = df[df['Artist'] == artist]
        if artist_df.empty:
            continue
        minutes = time * 60
        first_listened = artist_df['Date Played'].min().date()
        first_song = artist_df['Track Description'].iloc[0]
        most_streamed_song = artist_df.groupby('Track Description')['Play Duration Minutes'].sum().idxmax()
        most_streamed_song_time = artist_df.groupby('Track Description')['Play Duration Minutes'].sum().max()
        most_streamed_song_time_hours = round(most_streamed_song_time / 60, 1)
        f.write(f'"{artist}" listened for {time} hours ({minutes:,.2f} minutes)\n')
        f.write(f'   -> first listened on: {first_listened}\n')
        f.write(f'   -> first song streamed: {first_song}\n')
        f.write(f'   -> total listening time: {time} hours ({minutes:,.2f} minutes)\n')
        f.write(f'   -> most streamed song: {most_streamed_song} - {most_streamed_song_time_hours} hours ({most_streamed_song_time:,.2f} minutes)\n\n')
    f.write("\nTop 50 Most Streamed Tracks:\n")
    f.write("-" * 30 + "\n")
    for track, time in top_50_tracks.items():
        minutes = time * 60
        first_listened = df[df['Track Description'] == track]['Date Played'].min().date()
        f.write(f'"{track}" listened for {time} hours ({minutes:,.2f} minutes), first listened on {first_listened}\n')
