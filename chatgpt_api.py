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
                "content": f"Return 2 distinct messages. The first message is an Early Detection or the coin with the most overlap from the scripts provided. Provide the coin, the infulencers that mentioned it, the sentiment around it from the scripts, and a noteable quote about it. Ignore major coins like Bitcoin, Solana, Etherium. For the second message provide a narrative trend - what ever is mentioned with the most postivite sentiment from the scripts wither it be AI, gaming, utility, rwa or another category of crypto.: {all_transactipts}"
            }
        ]
    )

    return completion.choices[0].message.content
 

aggie_list = list()
transcript_str = ""
folder_path = './New_Video_Transcripts'
for filename in os.listdir(folder_path):
    if filename.endswith('.json'):  # Only process .json files
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r') as file:
                loaded_dict = file.read()
                transcript_str += loaded_dict
        except Exception as e:
            print(f"Unexpected error with {filename}: {e}")

response = get_data(transcript_str)

utils.send_discord_message(response)
