#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import glob
import youtube_dl
import json
import csv
import shutil
import datetime
import time

# Running this script is going to take a LONG TIME, as such,
# We'll put a lock file in here just so cron jobs know when not to push this repo
with open('_generator_lock', 'w') as lock_file:
  lock_file.write('.')

# We need to cleanup the entire API endpoint, replacing all files with the current version
shutil.rmtree('../v0/', ignore_errors=True)

with open('./info_playlists.json', 'r') as playlists_json_file:
  json_playlists = json.load(playlists_json_file)

csv_header = [
  "youtube_id",
  "video_title",
  "duration",
  "view_count",
  "uploader_name",
  "uploader_id",
  "channel_url",
  "video_url",
  "description"
]

# We're starting to count time now
script_start_time = time.time()

with youtube_dl.YoutubeDL() as yt_dl:
  
  # Parsed from source JSON
  for index, playlist_item in enumerate(json_playlists):
    start_playlist_item_time = time.time()
    playlist_data = yt_dl.extract_info(playlist_item['url'], download=False)
    
    # We're gonna add the playlist author to the current item in json_playlists
    json_playlists[index]['uploader'] = playlist_data['uploader']

    with open('test.json', 'w') as test:
      test.write(json.dumps(json_playlists))

    simplified_playlist_data = []

    for playlist_video_item in playlist_data['entries']:
      # Create simplified video data dict
      simplified_playlist_data.append({
        "youtube_id": playlist_video_item['id'],
        "video_title": playlist_video_item['title'],
        "duration": playlist_video_item['duration'],
        "view_count": playlist_video_item['view_count'],
        "uploader_name": playlist_video_item['uploader'],
        "uploader_id": playlist_video_item['uploader_id'],
        "channel_url": playlist_video_item['channel_url'],
        "video_url": playlist_video_item['webpage_url'],
        "description": playlist_video_item['description']
      })

    # Serialize simplified playlist data to CSV + JSON
    with open("playlist.csv", 'w') as csv_playlist_file:
      csv_writer = csv.DictWriter(csv_playlist_file, fieldnames=csv_header)
      csv_writer.writeheader()
      csv_writer.writerows(simplified_playlist_data)
    
    with open("playlist.json", 'w') as json_playlist_file:
      json_playlist_file.write(json.dumps(simplified_playlist_data))

    # Generate playlist folders if not present
    if not os.path.exists(str("../v0/" + playlist_item['name'])):
      os.makedirs(str("../v0/" + playlist_item['name']))

    # Generate checksums
    csv_md5 = os.popen("md5sum playlist.csv").read()
    csv_sha = os.popen("sha256sum playlist.csv").read()
    json_md5 = os.popen("md5sum playlist.json").read()
    json_sha = os.popen("sha256sum playlist.json").read()
    
    # Write checksums to respective files
    with open("playlist.csv.md5", "w") as csv_md5_file:
      csv_md5_file.write(csv_md5)
      
    with open("playlist.json.md5", "w") as json_md5_file:
      json_md5_file.write(json_md5)
      
    with open("playlist.csv.sha256", "w") as csv_sha_file:
      csv_sha_file.write(csv_sha)
      
    with open("playlist.json.sha256", "w") as json_sha_file:
      json_sha_file.write(json_sha)

    # Move all playlist files to respective folders
    for playlist_file in glob.iglob('playlist.*'):
      shutil.move(playlist_file, str('../v0/' + playlist_item['name'] + '/'))
    
    # Add computed time took to playlist item
    json_playlists[index]['time_took'] = (time.time() - start_playlist_item_time)

# Generate endpoint index.md
with open('../v0/index.md', 'w') as endpoint_index_file:
  now = datetime.datetime.now()
  total_time_took_seconds = (time.time() - script_start_time)
  total_time_took_formatted = str(datetime.timedelta(seconds=total_time_took_seconds))

  endpoint_index_file.write('# Endpoints\n\n')

  for playlist_item in json_playlists:
    playlist_time_took_formatted = str(datetime.timedelta(seconds=playlist_item['time_took']))

    endpoint_index_file.write('- ' + playlist_item['uploader'] + ' / **' + playlist_item['pretty_name'] + '** / [YouTube link](' + playlist_item['url'] + ')\n')
    endpoint_index_file.write('\tTook ' + playlist_time_took_formatted + '\n')
    endpoint_index_file.write('\t- [CSV file](./' + playlist_item['name'] + '/playlist.csv)\n')
    endpoint_index_file.write('\t\t- [Checksum : SHA256](./' + playlist_item['name'] + '/playlist.csv.sha256)\n')
    endpoint_index_file.write('\t\t- [Checksum : MD5](./' + playlist_item['name'] + '/playlist.csv.md5)\n')
    
    endpoint_index_file.write('\t- [JSON file](./' + playlist_item['name'] + '/playlist.json)\n')
    endpoint_index_file.write('\t\t- [Checksum : SHA256](./' + playlist_item['name'] + '/playlist.json.sha256)\n')
    endpoint_index_file.write('\t\t- [Checksum : MD5](./' + playlist_item['name'] + '/playlist.json.md5)\n\n')
    endpoint_index_file.write('---\n\n')
    
  endpoint_index_file.write("- Auto-generated by : Erwan's automated playlist archiver script\n\n")
  endpoint_index_file.write("- Auto-generated at : ")
  endpoint_index_file.write('**' + now.strftime("%d/%m/%Y %H:%M:%S") + '**\n\n')
  endpoint_index_file.write('- Auto-generated in : ')
  endpoint_index_file.write('**' + total_time_took_formatted + '**\n')

# We can now remove the lock file
os.remove('_generator_lock')
