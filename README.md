# YouTube KOL Content Analysis

This project automatically fetches the latest videos from specified YouTube crypto influencers (KOLs), extracts their transcripts, and analyzes the content to identify recommended cryptocurrencies using GPT-4.

## Features

- Fetches latest videos from configured YouTube channels
- Extracts video transcripts automatically
- Processes transcripts using GPT-4 to identify cryptocurrency recommendations
- Generates consolidated CSV reports with findings
- Handles multiple channels in batch processing

## Prerequisites

- Python 3.x
- YouTube Data API key
- OpenAI API key

## Required Python Packages

```bash
pip install python-dotenv
pip install google-api-python-client
pip install youtube-transcript-api
pip install pandas
pip install openai
```

## Project Structure

```
├── config.py                # KOL channel configuration
├── youtube_api.py           # YouTube data fetching logic
├── chatgpt_api.py          # GPT-4 analysis implementation
├── main.py                 # Main execution script
├── Video_Transcripts/      # Storage for video transcripts
└── Aggie_Outputs/         # Output directory for analysis results
```

## Configuration

1. Create a `.env` file in the project root with your API keys:
```
youtube_key_aggie=YOUR_YOUTUBE_API_KEY
openai_gpt_key_aggie=YOUR_OPENAI_API_KEY
```

2. Install pip packages:
'''
pip install -r requirements.txt
'''

3. Configure YouTube channels in `config.py`:
```python
kols_list = [
    '@ChannelHandle1',
    '@ChannelHandle2',
    # Add more channels as needed
]
```

## Usage

Run the entire pipeline:
```bash
python main.py
```

This will:
1. Fetch the latest video from each configured channel
2. Extract and save video transcripts
3. Analyze transcripts for cryptocurrency recommendations
4. Generate a consolidated CSV report

## Output

The script generates two types of outputs:

1. Individual JSON files for each video transcript in `Video_Transcripts/`
2. Consolidated CSV reports in `Aggie_Outputs/` with the format:
   - KOL (channel name)
   - Date
   - Recommended Coins

## Error Handling

- The script includes robust error handling for API failures
- Transcripts that can't be fetched are logged with error messages
- Failed processes don't stop the entire pipeline

## Notes

- API rate limits apply for both YouTube and OpenAI services
- Some YouTube videos may not have available transcripts
- The analysis accuracy depends on GPT-4's interpretation of the content
