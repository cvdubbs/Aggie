
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

## Teasting new build out for creating transcripts
channel_handle = config.kols_list[4]  # Example channel handle
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

# try:
#     # Get transcript
#     transcript = YouTubeTranscriptApi.get_transcript(video_id)
#     return {
#         'video_id': video_id,
#         'title': video_title,
#         'date': video_date,
#         'transcript': transcript
#     }


import pytube
import speech_recognition as sr
import os
from pydub import AudioSegment
import tempfile

def download_youtube_audio(video_url, output_path="audio.mp3"):
    """Download audio from a YouTube video."""
    try:
        # Create a YouTube object
        yt = pytube.YouTube(video_url)
        
        # Get the audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        # Download the audio file
        print(f"Downloading audio from: {yt.title}")
        audio_file = audio_stream.download(output_path=os.path.dirname(output_path), 
                                          filename=os.path.basename(output_path))
        
        print(f"Audio downloaded to: {audio_file}")
        return audio_file
    
    except Exception as e:
        print(f"Error downloading YouTube audio: {e}")
        return None

def transcribe_audio(audio_file_path):
    """Transcribe the downloaded audio file."""
    try:
        # Create a temporary WAV file (speech_recognition requires WAV format)
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_wav.close()
        
        # Convert MP3 to WAV
        print("Converting audio to WAV format...")
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(temp_wav.name, format="wav")
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Transcribe audio in chunks
        print("Transcribing audio (this may take some time)...")
        
        with sr.AudioFile(temp_wav.name) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)
            
            # For longer videos, we'll process in chunks
            # Typical YouTube videos can be very long, so we process in chunks
            full_transcript = ""
            chunk_duration = 30  # seconds
            audio_duration = len(audio) / 1000  # Convert milliseconds to seconds
            
            for i in range(0, int(audio_duration) + 1, chunk_duration):
                print(f"Transcribing chunk {i//chunk_duration + 1}...")
                chunk_audio = recognizer.record(source, duration=min(chunk_duration, audio_duration - i))
                try:
                    chunk_text = recognizer.recognize_google(chunk_audio)
                    full_transcript += chunk_text + " "
                except sr.UnknownValueError:
                    full_transcript += "[Unintelligible] "
                except Exception as e:
                    print(f"Error in chunk {i//chunk_duration + 1}: {e}")
                    full_transcript += "[Error] "
        
        # Clean up temporary file
        os.unlink(temp_wav.name)
        
        return full_transcript.strip()
    
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def save_transcript(transcript, output_file="transcript.txt"):
    """Save the transcript to a file."""
    try:
        with open(output_file, "w") as f:
            f.write(transcript)
        print(f"Transcript saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False

def generate_youtube_transcript(video_url, output_file="transcript.txt"):
    """Generate a transcript for a YouTube video."""
    # 1. Download the audio
    audio_file = download_youtube_audio(video_url)
    if not audio_file:
        return False
    
    # 2. Transcribe the audio
    transcript = transcribe_audio(audio_file)
    if not transcript:
        return False
    
    # 3. Save the transcript
    success = save_transcript(transcript, output_file)
    
    # 4. Optionally clean up the audio file
    try:
        os.remove(audio_file)
    except:
        pass
    
    return success
