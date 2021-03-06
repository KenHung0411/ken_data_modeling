import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    # open song file  
    df = pd.read_json(filepath, lines=True) # read data frame from json file

    # insert song record
    song_data = df[['song_id', 'title', 'artist_id', 'year' ,'duration']]
    song_data_insert = tuple(map(tuple, song_data.values))
    for row in song_data_insert:
        cur.execute(song_table_insert, row)
        
    
    # insert artist record
    artist_data = df[['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude']]
    artist_data_insert = tuple(map(tuple, artist_data.values))
    for row in artist_data_insert:
        cur.execute(artist_table_insert, row)
        
    

def process_log_file(cur, filepath):
    # open log file
    df = pd.read_json(filepath, lines=True) # read data frame from json file
    # filter by NextSong action
    df = df[df['page'] == 'NextSong']

    # convert timestamp column to datetime
    time_df = df.loc[ : ,['ts']]
    time_df['ts'] = pd.to_datetime(time_df['ts'], unit='ms')

    time_df['start_time'] = time_df.loc[ : , 'ts']
    time_df['year'] = time_df.loc[ : ,'ts'].dt.year
    time_df['month'] = time_df.loc[ : ,'ts'].dt.month
    time_df['week'] = time_df.loc[ : ,'ts'].dt.week
    time_df['weekday'] = time_df.loc[ : ,'ts'].dt.weekday
    time_df['day'] = time_df.loc[ : ,'ts'].dt.day
    time_df['hour'] = time_df.loc[ : ,'ts'].dt.hour
    time_df = time_df.loc[ : ,['start_time', 'year', 'month', 'week', 'weekday', 'day', 'hour']]
        
    # insert time data records
    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, tuple(row))
        

    # load user table
    user_df = df.loc[:, ("userId", "firstName", "lastName", "gender" , "level")] 

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)
        
    
    # insert songplay records
    for index, row in df.iterrows():
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None
        # insert songplay record
        # No idea what is it for "songplay_id for song play"
        songplay_data = (index, row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)
        


def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()