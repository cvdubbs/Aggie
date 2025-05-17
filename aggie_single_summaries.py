import json
import os
import pandas as pd
import ast
from openai import OpenAI
from datetime import datetime

from dotenv import load_dotenv
import os

import utils

# Load environment variables from .env file
load_dotenv()

# Get the API key
os.environ['OPENAI_API_KEY'] = os.getenv('openai_gpt_key_aggie')

client = OpenAI()


def get_data(all_transactipts):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a data aggregator and crypto expert providing market insights."},
            {
                "role": "user",
                "content": f"Please write a short summary of this crypto video. At the top of the message use a header and show the channel and date. Start the message with a unique emoji that will show in discord. Keep the number of characters below 2000 please.: {all_transactipts}"
            }
        ]
    )
    return completion.choices[0].message.content
 

aggie_list = list()
folder_path = './New_Video_Transcripts'
for filename in os.listdir(folder_path):
    if filename.endswith('.json'):  # Only process .json files
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r') as file:
                loaded_dict = file.read()
                response = get_data(loaded_dict)
                utils.send_discord_message(response, os.getenv("discord_webhook_url_single"))
        except Exception as e:
            print(f"Unexpected error with {filename}: {e}")


