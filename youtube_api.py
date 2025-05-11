
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API key
api_key = os.getenv('youtube_key_aggie')

import json
import pandas as pd
import shutil
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

import config

def clear_new_video_transcripts(source_dir = "./New_Video_Transcripts", destination_dir = "./Video_Transcripts"):
    # Create destination directory if it doesn't exist
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        print(f"Created destination directory: {destination_dir}")

    # Get list of all files in source directory
    try:
        files = os.listdir(source_dir)
        
        # Count for summary
        moved_count = 0
        
        # Move each file
        for file in files:
            source_path = os.path.join(source_dir, file)
            
            # Skip directories
            if os.path.isfile(source_path):
                destination_path = os.path.join(destination_dir, file)
                
                # Move the file
                shutil.move(source_path, destination_path)
                print(f"Moved: {file}")
                moved_count += 1
        
        # Print summary
        if moved_count > 0:
            print(f"\nSuccessfully moved {moved_count} files from {source_dir} to {destination_dir}")
        else:
            print(f"\nNo files found in {source_dir}")
            
    except FileNotFoundError:
        print(f"Error: Source directory '{source_dir}' not found")
    except PermissionError:
        print(f"Error: Permission denied when accessing files")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def get_latest_video_and_transcript(api_key, channel_handle):
    # Create YouTube service object
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # First, get the channel ID from the handle
    request = youtube.search().list(
        part='snippet',
        q=channel_handle,
        type='channel'
    )
    response = request.execute()
    
    # Extract channel ID
    channel_id = response['items'][0]['id']['channelId']
    
    # Get the latest video from the channel
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        order='date',
        maxResults=1,
        type='video'
    )
    response = request.execute()
    
    # Extract video ID and details
    video_id = response['items'][0]['id']['videoId']
    video_title = response['items'][0]['snippet']['title']
    video_date = pd.to_datetime(response['items'][0]['snippet']['publishedAt']).strftime('%Y_%m_%d')
    
    try:
        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return {
            'video_id': video_id,
            'title': video_title,
            'date': video_date,
            'transcript': transcript
        }
    except Exception as e:
        return {
            'video_id': video_id,
            'title': video_title,
            'error': f'Could not fetch transcript: {str(e)}'
        }


def get_save_video_transcript(channel_handle, api_key):
    file_channel_name = channel_handle[1:]
    result = get_latest_video_and_transcript(api_key, channel_handle)
    transcript_string = ""
    if 'transcript' in result:
        for i in range(0, len(result['transcript'])):
            transcript_string += (" " + result['transcript'][i]['text']) 

        save_dict = {
            'channel': file_channel_name,
            'date': result['date'],
            'transcript': transcript_string
        }

        with open(f"./New_Video_Transcripts/{file_channel_name}_{result['date']}.json", 'w') as file:
            json.dump(save_dict, file, indent=4)
        
        with open(f"./Video_Transcripts/{file_channel_name}_{result['date']}.json", 'w') as file:
            json.dump(save_dict, file, indent=4)


clear_new_video_transcripts()
# Usage
for channel in config.kols_list:
    get_save_video_transcript(channel, api_key)
