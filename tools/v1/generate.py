#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import yt_dlp
import json
import csv
import shutil
import datetime
import time

# Affect globals
script_version = "2.0"
endpoint_version = "1.0"

with open('./metadata.json', 'r') as fp_metadata:
  metadata = json.load(fp_metadata)

csv_header = [
  "youtube_id",
  "video_title",
  "duration",
  "view_count",
  "uploader_name",
  "uploader_id",
  "channel_url",
  "video_url",
]

yt_dlp_params = {
  'ignoreerrors': True,
  'ignore_no_formats_error': True,
  'skip_download': True,
}

def prepare_endpoint():
  # Lock file needed as the script takes several hours to fetch data
  with open('_.lock', 'w') as lock_file:
    lock_file.write('.')

  # Cleanup the API endpoint
  shutil.rmtree('../../v1/', ignore_errors=True)

prepare_endpoint()

# Start global timer
global_timer = time.time()

with yt_dlp.YoutubeDL(yt_dlp_params) as yt_dlp_handler:

  # Parsed from source JSON
  for index, playlist_item in enumerate(metadata):    
    print(':: Downloading playlist', playlist_item['name'])

    # Start item timer
    playlist_timer = time.time()

    # Download full playlist data
    playlist_data = yt_dlp_handler.extract_info(playlist_item['url'], download=False)

    # Add the playlist author to the temporary metadata
    metadata[index]['uploader'] = playlist_data['uploader']

    clean_playlist_data = []

    for playlist_video_item in playlist_data['entries']:
      # Ignore unavailable videos
        
      if playlist_video_item is None:
        # Loop over
        continue
      
      # Remove playlist bloat
      clean_playlist_data.append({
        "youtube_id": playlist_video_item['id'],
        "video_title": playlist_video_item['title'],
        "duration": playlist_video_item['duration'],
        "view_count": playlist_video_item['view_count'],
        "uploader_name": playlist_video_item['uploader'],
        "uploader_id": playlist_video_item['uploader_id'],
        "channel_url": playlist_video_item['channel_url'],
        "video_url": playlist_video_item['webpage_url'],
      })

    # Serialize simplified playlist data to CSV
    with open("playlist.csv", 'w') as fp_csv_playlist:
      csv_writer = csv.DictWriter(fp_csv_playlist, fieldnames=csv_header)
      csv_writer.writeheader()
      csv_writer.writerows(clean_playlist_data)

    # Generate playlist folders if not present
    if not os.path.exists("../../v1/" + str(playlist_item['name'])):
      os.makedirs("../../v1/" + str(playlist_item['name']))

    # Generate checksums
    csv_md5 = os.popen("md5sum playlist.csv").read()
    
    # Write checksums to respective files
    with open("playlist.csv.md5", "w") as csv_md5_file:
      csv_md5_file.write(csv_md5)

    # Move all playlist files to respective folders
    for playlist_file in glob.iglob('playlist.*'):
      shutil.move(playlist_file, str('../../v1/' + playlist_item['name'] + '/'))
    
    # Add computed time took to playlist item
    metadata[index]['time_took'] = (time.time() - playlist_timer)

total_time_took_seconds = (time.time() - global_timer)
total_time_took = str(datetime.timedelta(seconds=total_time_took_seconds)).split('.')[0] # Remove microseconds
split_time = total_time_took.split(':')
total_time_took_formatted = str(split_time[0] + 'h, ' + split_time[1] + ' mins.')

endpoint_index_contents = f"""
> Endpoints
> Script version : { script_version }
> Endpoint version : { endpoint_version }

---
"""

for playlist_item in metadata:
  playlist_time_took = str(datetime.timedelta(seconds=playlist_item['time_took'])).split('.')[0] # Omit microseconds
  split_time = str(playlist_time_took).split(':')
  playlist_time_took_formatted = str(split_time[0] + ' h, ' + split_time[1] + ' mins.')

  endpoint_index_contents += f"""
{ playlist_item['uploader'] } / **{ playlist_item['pretty_name'] }** - [link]({ playlist_item['url'] })
  Took { playlist_time_took_formatted }
  - [CSV file]({ './' + playlist_item['name'] + '/playlist.csv' })
    - [MD5]({'./' + playlist_item['name'] + '/playlist.csv.md5'})

---
"""

endpoint_index_contents += f"""
- Auto-generated at : { datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") }

- Total time took : { total_time_took_formatted }
"""


with open('../../v1/index.md', 'w') as fp_endpoint_index:
  fp_endpoint_index.write(endpoint_index_contents)

# We can now remove the lock file
os.remove('_.lock')
