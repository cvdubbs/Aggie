
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API key
api_key = os.getenv('youtube_key_aggie')

import json
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

import config

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

        with open(f"./Video_Transcripts/{file_channel_name}_{result['date']}.json", 'w') as file:
            json.dump(save_dict, file, indent=4)

# Usage
for channel in config.kols_list:
    get_save_video_transcript(channel, api_key)
