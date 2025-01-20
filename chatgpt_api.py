import json
import os
import pandas as pd
import ast
from openai import OpenAI
from datetime import datetime

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API key
os.environ['OPENAI_API_KEY'] = os.getenv('openai_gpt_key_aggie')

client = OpenAI()


def get_dataframe(loaded_dict):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Return ONLY a Python list of recommended coins. No additional text, no markdown formatting, no explanation. Just the list in the format: ['coin1', 'coin2', 'coin3']"},
            {
                "role": "user",
                "content": f"Return only a Python list of the coins recommended to buy in this transcript: {loaded_dict['transcript']}"
            }
        ]
    )

    string_list = completion.choices[0].message.content
    coins_list = ast.literal_eval(string_list)
    # Create DataFrame
    df = pd.DataFrame({
        'KOL': [loaded_dict['channel']] * len(coins_list),
        'Date': [loaded_dict['date']] * len(coins_list),
        'Coin': coins_list
    })
    return df


aggie_list = list()
folder_path = './Video_Transcripts'
for filename in os.listdir(folder_path):
    if filename.endswith('.json'):  # Only process .json files
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r') as file:
                loaded_dict = json.load(file)
                aggie_list.append(get_dataframe(loaded_dict))
        except json.JSONDecodeError as e:
            print(f"Error reading {filename}: {e}")
        except Exception as e:
            print(f"Unexpected error with {filename}: {e}")


current_date = datetime.now().strftime('%Y_%m_%d')

final_df = pd.concat(aggie_list)
final_df.to_csv(f'./Aggie_Outputs/Aggie_Output_{current_date}.csv', index=False)
final_df.to_clipboard()
