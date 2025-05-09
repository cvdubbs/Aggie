import os
import requests
import time
from requests.exceptions import Timeout, ConnectionError, RequestException
import pandas as pd
from dotenv import load_dotenv
load_dotenv()


def send_discord_message(message_to_send, max_retries=3, timeout=10):
    """
    Send a message to a Discord channel using a webhook with proper error handling and timeout.
    
    Args:
        message_to_send (str): The message to send.
        image_url (str, optional): URL of an image to include in the embed.
        max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
        timeout (int, optional): Request timeout in seconds. Defaults to 10.
        
    Returns:
        bool: True if message was sent successfully, False otherwise.
    """
    # Define the webhook URL
    try:
        webhook_url = os.getenv("discord_webhook_url")
    except (AttributeError, KeyError):
        print("Error: Discord webhook URL not found in config")
        return False
    
    # Prepare the message payload
    data = {
        "content": message_to_send
    }

    # Attempt to send the message with retries
    for attempt in range(max_retries):
        try:
            # Send the request with timeout
            response = requests.post(webhook_url, json=data, timeout=timeout)
            
            # Check response status
            if response.status_code == 204:
                print("Message sent successfully!")
                return True
            elif response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 5))
                print(f"Rate limited. Waiting {retry_after} seconds before retry...")
                time.sleep(retry_after)
            else:
                print(f"Failed to send message: Status code {response.status_code}")
                # If it's a client error (4xx) that's not rate limiting, don't retry
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    print(f"Client error: {response.text}")
                    return False
                    
                # Wait before retry for server errors
                wait_time = (attempt + 1) * 2
                print(f"Server error. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
        except Timeout:
            print(f"Request timed out (attempt {attempt+1}/{max_retries})")
            if attempt == max_retries - 1:
                return False
                
        except ConnectionError as e:
            print(f"Connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep((attempt + 1) * 2)
            
        except RequestException as e:
            print(f"Request exception (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep((attempt + 1) * 2)
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return False
    
    print("Max retries exceeded. Failed to send Discord message.")
    return False

