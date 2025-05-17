from dotenv import load_dotenv
import os
import json
import pandas as pd
import shutil
import tempfile
import time
import requests
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import pytube
import speech_recognition as sr
from pydub import AudioSegment
import yt_dlp  # More robust alternative to pytube
from datetime import datetime  # Added import for current date check

# Load environment variables from .env file
load_dotenv()

# Get the API key
api_key = os.getenv('youtube_key_aggie')

def clear_new_video_transcripts(source_dir="./New_Video_Transcripts", destination_dir="./Video_Transcripts"):
    """Move files from the source directory to the destination directory."""
    # Create destination directory if it doesn't exist
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        print(f"Created destination directory: {destination_dir}")
    
    # Create source directory if it doesn't exist
    if not os.path.exists(source_dir):
        os.makedirs(source_dir)
        print(f"Created source directory: {source_dir}")

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


def get_latest_video_data(api_key, channel_handle):
    """Get the latest video data from a channel."""
    # Create YouTube service object
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    try:
        # First, get the channel ID from the handle
        request = youtube.search().list(
            part='snippet',
            q=channel_handle,
            type='channel'
        )
        response = request.execute()
        
        if not response.get('items'):
            print(f"No channel found for handle: {channel_handle}")
            return None
        
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
        
        if not response.get('items'):
            print(f"No videos found for channel: {channel_handle}")
            return None
        
        # Extract video ID and details
        video_id = response['items'][0]['id']['videoId']
        video_title = response['items'][0]['snippet']['title']
        video_date = pd.to_datetime(response['items'][0]['snippet']['publishedAt']).strftime('%Y_%m_%d')
        publish_date_raw = response['items'][0]['snippet']['publishedAt']
        
        return {
            'video_id': video_id,
            'title': video_title,
            'date': video_date,
            'channel_id': channel_id,
            'video_url': f"https://www.youtube.com/watch?v={video_id}",
            'publish_date_raw': publish_date_raw
        }
    except Exception as e:
        print(f"Error fetching video data for {channel_handle}: {str(e)}")
        return None


def try_get_transcript_via_api(video_id):
    """Attempt to get the transcript via YouTube Transcript API with multiple retries."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Try multiple languages if needed
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
            except:
                # Try to get any available transcript, regardless of language
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list[0].fetch()
            
            # Convert transcript to text
            transcript_string = ""
            for item in transcript:
                transcript_string += (" " + item['text'])
            return transcript_string
        except Exception as e:
            print(f"API Transcript fetch attempt {attempt+1} failed: {str(e)}")
            time.sleep(1)  # Brief pause before retry
    
    return None


def download_youtube_audio_yt_dlp(video_url, temp_dir=None):
    """Download audio from a YouTube video using yt-dlp (more robust than pytube)."""
    try:
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        
        output_path = os.path.join(temp_dir, "audio.mp3")
        
        # yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False
        }
        
        print(f"Downloading audio from: {video_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # yt-dlp adds extension automatically
        final_path = output_path + ".mp3"
        if not os.path.exists(final_path):
            final_path = output_path
        
        print(f"Audio downloaded to: {final_path}")
        return final_path
    
    except Exception as e:
        print(f"Error downloading YouTube audio with yt-dlp: {e}")
        return None


def download_youtube_audio_pytube(video_url, temp_dir=None):
    """Download audio using pytube (fallback method)."""
    try:
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        
        output_path = os.path.join(temp_dir, "audio.mp3")
        
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
        print(f"Error downloading YouTube audio with pytube: {e}")
        return None


def download_youtube_audio(video_url, temp_dir=None):
    """Try multiple methods to download audio."""
    # Try yt-dlp first (more reliable)
    audio_file = download_youtube_audio_yt_dlp(video_url, temp_dir)
    
    # If that fails, try pytube
    if audio_file is None:
        audio_file = download_youtube_audio_pytube(video_url, temp_dir)
    
    return audio_file


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
            full_transcript = ""
            chunk_duration = 30  # seconds
            audio_duration = len(audio) / 1000  # Convert milliseconds to seconds
            total_chunks = int(audio_duration/chunk_duration) + 1
            
            for i in range(0, int(audio_duration) + 1, chunk_duration):
                chunk_num = i//chunk_duration + 1
                print(f"Transcribing chunk {chunk_num}/{total_chunks}...")
                chunk_audio = recognizer.record(source, duration=min(chunk_duration, audio_duration - i))
                try:
                    # Try using Google's speech recognition API
                    chunk_text = recognizer.recognize_google(chunk_audio)
                    full_transcript += chunk_text + " "
                except sr.UnknownValueError:
                    full_transcript += "[Unintelligible] "
                except sr.RequestError:
                    # If Google API fails, try an alternative service
                    try:
                        print("Google API failed, trying alternative...")
                        chunk_text = recognizer.recognize_sphinx(chunk_audio)
                        full_transcript += chunk_text + " "
                    except:
                        full_transcript += "[Recognition Error] "
                except Exception as e:
                    print(f"Error in chunk {chunk_num}: {e}")
                    full_transcript += "[Error] "
        
        # Clean up temporary file
        try:
            os.unlink(temp_wav.name)
        except:
            pass
        
        return full_transcript.strip()
    
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None


def get_transcript_via_audio(video_url):
    """Get transcript by downloading and transcribing the audio."""
    try:
        # Create a temporary directory for the audio file
        temp_dir = tempfile.mkdtemp()
        
        # Download the audio
        audio_file = download_youtube_audio(video_url, temp_dir)
        if not audio_file:
            return None
        
        # Transcribe the audio
        transcript = transcribe_audio(audio_file)
        
        # Clean up the audio file and temp directory
        try:
            os.remove(audio_file)
            os.rmdir(temp_dir)
        except:
            pass
        
        return transcript
    
    except Exception as e:
        print(f"Error in audio transcription process: {e}")
        return None


def is_current_month_year(date_str):
    """Check if the date string is from the current month and year.
    
    Args:
        date_str: Date string in format 'YYYY_MM_DD' or ISO format
        
    Returns:
        Boolean indicating if the date is from current month and year
    """
    try:
        # If the date is in ISO format (from the API), convert it to datetime
        if 'T' in date_str:
            video_date = pd.to_datetime(date_str)
        else:
            # Otherwise, it's in our YYYY_MM_DD format
            video_date = pd.to_datetime(date_str.replace('_', '-'))
        
        # Get current date
        current_date = datetime.now()
        
        # Check if video is from current month and year
        return (video_date.year == current_date.year and 
                video_date.month == current_date.month)
    
    except Exception as e:
        print(f"Error checking date: {e}")
        return False  # Default to False if there's an error


def get_save_video_transcript(channel_handle, api_key):
    """Get and save transcript for the latest video from a channel."""
    try:
        # Remove @ from channel handle for file naming
        file_channel_name = channel_handle.replace('@', '')
        
        # Get latest video data
        print(f"\nProcessing channel: {channel_handle}")
        video_data = get_latest_video_data(api_key, channel_handle)
        
        if video_data is None:
            print(f"Could not get video data for {channel_handle}. Skipping.")
            return
            
        print(f"Found video: {video_data['title']} (ID: {video_data['video_id']})")
        
        # Check if the video is from the current month and year
        if not is_current_month_year(video_data['publish_date_raw']):
            print(f"Skipping {channel_handle}: Latest video is not from the current month and year.")
            print(f"Video date: {video_data['date']}, Current date: {datetime.now().strftime('%Y-%m-%d')}")
            return
        
        # Method 1: Try to get transcript via YouTube API
        print("Attempting to get transcript via YouTube API...")
        transcript_string = try_get_transcript_via_api(video_data['video_id'])
        transcript_method = "api"
        
        # If API method fails, use audio transcription
        if transcript_string is None:
            print("API method failed. Falling back to audio transcription...")
            transcript_string = get_transcript_via_audio(video_data['video_url'])
            transcript_method = "audio_transcription"
            
            if transcript_string is None:
                print("Audio transcription also failed. Saving video info without transcript.")
                transcript_string = "[Transcript unavailable]"
                transcript_method = "failed"
        
        # Ensure directories exist
        for directory in ["./New_Video_Transcripts", "./Video_Transcripts"]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Save the transcript
        save_dict = {
            'channel': file_channel_name,
            'date': video_data['date'],
            'title': video_data['title'],
            'video_id': video_data['video_id'],
            'video_url': video_data['video_url'],
            'transcript': transcript_string,
            'transcript_method': transcript_method
        }

        # Save to both directories
        output_file = f"{file_channel_name}_{video_data['date']}.json"
        
        with open(f"./New_Video_Transcripts/{output_file}", 'w', encoding='utf-8') as file:
            json.dump(save_dict, file, indent=4, ensure_ascii=False)
        
        with open(f"./Video_Transcripts/{output_file}", 'w', encoding='utf-8') as file:
            json.dump(save_dict, file, indent=4, ensure_ascii=False)
            
        print(f"Successfully saved to {output_file} (method: {transcript_method})")
        
    except Exception as e:
        print(f"Error processing {channel_handle}: {str(e)}")


def process_channels(channels_list):
    """Process a list of channel handles."""
    # Clear previous transcripts
    clear_new_video_transcripts()
    
    # Process each channel
    for channel in channels_list:
        get_save_video_transcript(channel, api_key)
        print("-" * 50)


def check_ffmpeg():
    """Check if ffmpeg is installed and working."""
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        print("WARNING: ffmpeg not found. Audio conversion may fail.")
        print("Please install ffmpeg using: brew install ffmpeg (Mac) or apt-get install ffmpeg (Linux)")
        return False


if __name__ == "__main__":
    # Check for ffmpeg
    check_ffmpeg()
    
    # Print current date for reference
    current_date = datetime.now()
    print(f"Current date: {current_date.strftime('%Y-%m-%d')}")
    print(f"Only processing videos from {current_date.strftime('%B %Y')}")
    print("-" * 50)
    
    try:
        # Import channel list from config
        import config
        channels_list = config.kols_list
    except ImportError:
        # If config module not found, can specify channels here
        channels_list = ['@example1', '@example2']
        
        # Or get from user input
        use_input = input("Config not found. Would you like to enter channel handles manually? (y/n): ")
        if use_input.lower() == 'y':
            channels_input = input("Enter channel handles separated by commas (e.g., @example1,@example2): ")
            channels_list = [handle.strip() for handle in channels_input.split(',')]
    
    # Process all channels
    process_channels(channels_list)
    print("\nAll channels processed!")