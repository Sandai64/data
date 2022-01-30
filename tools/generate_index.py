#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime
import json

with open('./info_playlists.json', 'r') as playlists_json_file:
  json_playlists = json.load(playlists_json_file)

# Generate endpoint index.md
with open('../v0/index.md', 'w') as endpoint_index_file:
  endpoint_index_file.write('# Endpoints\n\n')
  now = datetime.datetime.now()

  for playlist_item in json_playlists:

    endpoint_index_file.write('- **' + playlist_item['pretty_name'] + '**\n')
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
