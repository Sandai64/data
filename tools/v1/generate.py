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
separator_character = '='

print(f":: Erwan's Playlist Archiver Script")
print(f":: Script version   : { script_version }")
print(f":: Endpoint version : { script_version }")

(term_cols, term_lines) = os.get_terminal_size()


class YTDLP_Logger:
  def debug(self, msg):
    if msg.startswith('[download]'):
      clean_msg = msg.strip().replace('\n', '').replace('\r', '')
      whitespace_remaining = '.'*((term_cols-len(clean_msg))-4)
      print(f"\r:: { clean_msg } {whitespace_remaining}\r", end='')

  def info(self, msg):
    pass

  def warning(self, msg):
    pass

with open('./metadata.json', 'r') as fp_metadata:
  print(f":: Loading metadata.json...")
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
  'logger': YTDLP_Logger(),
}

# Lock file needed as the script takes several hours to fetch data
print(f":: Writing lock file...")
with open('_.lock', 'w') as lock_file:
  lock_file.write('.')

# Cleanup the API endpoint
print(f":: Cleaning up API endoint...")
shutil.rmtree('../../v1/', ignore_errors=True)

# Start global timer
print(f":: Starting global timer...")
global_timer = time.time()

print(f":: Starting yt_dlp...")
with yt_dlp.YoutubeDL(yt_dlp_params) as yt_dlp_handler:

  # Parsed from source JSON
  for index, playlist_item in enumerate(metadata):
    print(f"{separator_character*term_cols}")
    print(f":: Downloading playlist : { playlist_item['name'] }")

    # Start item timer
    print(f":: { playlist_item['name'] } : Starting timer")
    playlist_timer = time.time()

    # Download full playlist data
    print(f":: { playlist_item['name'] } : Extracting info...")
    playlist_data = yt_dlp_handler.extract_info(playlist_item['url'], download=False)

    # Add the playlist author to the temporary metadata
    print(f"\n:: { playlist_item['name'] } : Adding uploader metadata")
    metadata[index]['uploader'] = playlist_data['uploader']

    clean_playlist_data = []
    print(f":: { playlist_item['name'] } : Starting bulk video metadata processing...")
    print(f":: { playlist_item['name'] } : This will take a while...")

    playlist_video_count = len(playlist_data['entries'])

    for video_index, video_item in enumerate(playlist_data['entries']):
      process_message = f":: { playlist_item['name'] } : Processing video... [{ video_index+1 }/{ playlist_video_count }]"
      remaining_space = (term_cols-len(process_message))-1
      print(f"\r{ process_message } { '.'*remaining_space }", end='', flush=True)

      # Ignore unavailable videos
      if video_item is None:
        # Loop over
        continue

      # Checks for missing keys in video - ignore video if one is missing
      should_ignore_video = False

      for key in ['id', 'title', 'duration', 'view_count', 'uploader', 'uploader_id', 'channel_url', 'webpage_url']:

        if not key in video_item.keys():
          should_ignore_video = True

      if should_ignore_video:
        continue

      # Remove playlist bloat
      clean_playlist_data.append({
        "youtube_id": video_item['id'],
        "video_title": video_item['title'],
        "duration": video_item['duration'],
        "view_count": video_item['view_count'],
        "uploader_name": video_item['uploader'],
        "uploader_id": video_item['uploader_id'],
        "channel_url": video_item['channel_url'],
        "video_url": video_item['webpage_url'],
      })

    print(f"\n:: { playlist_item['name'] } : Processing finished. Serializing data...")

    # Serialize simplified playlist data to CSV
    with open("playlist.csv", 'w') as fp_csv_playlist:
      csv_writer = csv.DictWriter(fp_csv_playlist, fieldnames=csv_header)
      csv_writer.writeheader()
      csv_writer.writerows(clean_playlist_data)

    print(f":: { playlist_item['name'] } : Generating folder structure...")


    # Generate playlist folders if not present
    if not os.path.exists("../../v1/" + str(playlist_item['name'])):
      os.makedirs("../../v1/" + str(playlist_item['name']))

    print(f":: { playlist_item['name'] } : Generating checksums...")

    # Generate checksums
    csv_md5 = os.popen("md5sum playlist.csv").read()

    # Write checksums to respective files
    with open("playlist.csv.md5", "w") as csv_md5_file:
      csv_md5_file.write(csv_md5)

    print(f":: { playlist_item['name'] } : Moving playlist files...")

    # Move all playlist files to respective folders
    for playlist_file in glob.iglob('playlist.*'):
      shutil.move(playlist_file, str('../../v1/' + playlist_item['name'] + '/'))

    print(f":: { playlist_item['name'] } : Stopping timer")

    # Add computed time took to playlist item
    metadata[index]['time_took'] = (time.time() - playlist_timer)

print(f"{separator_character*term_cols}")
print(f":: Global data processing finished !")
print(f":: Generating index file...")

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
print(f":: Removing lock file...")
os.remove('_.lock')
print(f"{separator_character*term_cols}")
print(f"\n:: Job done.")