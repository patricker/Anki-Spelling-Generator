import openai
import requests
import base64
import argparse
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def encode_image_to_base64(image_path):
    """
    Encodes an image to a base64 string.

    Args:
    image_path (str): The file path of the image to encode.
    
    Returns:
    str: The base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_spelling_words_from_image(image_path, api_key):
    """
    Takes a local image path, encodes it to base64, sends it to GPT-4 Vision model,
    and extracts spelling words.
    
    Args:
    image_path (str): The local path of the image to process.
    api_key (str): Your OpenAI API key.
    
    Returns:
    dict: The JSON response from the API.
    """
    base64_image = encode_image_to_base64(image_path)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "This image contains a large list of spelling words. Please extract them for me in a line delimited list. Only include the spelling words, nothing else. Do not include text outside of the spelling word list."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                ]
            }
        ],
        "max_tokens": 2000
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content'].split()

def generate_example_sentences(words, api_key):
    """
    Takes a list of spelling words and generates example sentences for each, in bulk.
    
    Args:
    words (list): A list of words to generate sentences for.
    api_key (str): Your OpenAI API key.
    
    Returns:
    dict: A dictionary where each key is a spelling word and the value is an example sentence.
    """
    sentences = {}
    client = openai.OpenAI(api_key=api_key)

    # Construct the prompt with all the words and instructions for the expected output format.
    prompt = ("Write a child-friendly sentence for each spelling word provided. " 
              "The sentences should be simple and silly. " 
              "Use each word in a separate sentence and do not spell out the words. " 
              "Words must be used exactly as provided. You cannot use 's or 're contractions, you cannot use 'fastest' or 'faster' for 'fast', etc."
              "Format your response as 'word|example sentence', one response per line.")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "\n".join(words)}
        ],
        max_tokens=4000,
    )

    # Process the response and extract sentences
    # Assuming the model's response is well-formatted according to our instruction
    for line in response.choices[0].message.content.strip().split('\n'):
        word, sentence = line.split('|')
        sentences[word.strip()] = sentence.strip()

    return sentences

def convert_text_to_speech_task(api_key, sentence, word, file_prefix, output_directory):
    """
    A task that converts a single sentence to speech and saves it as an MP3 file.
    """
    client = openai.OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=f'"{word}"... {sentence}... "{word}".', # Since this is spelling practice, repeate the word before and after the sentence.
    )
    audio_file_path = output_directory / f"{file_prefix}_{word}.mp3"
    with open(audio_file_path, "wb") as audio_file:
        audio_file.write(response.content)
    return word, audio_file_path

def convert_text_to_speech(sentences, api_key, file_prefix, output_directory):
    """
    Takes a dictionary of words and example sentences, and generates an MP3 file for each sentence in parallel.
    
    Args:
    sentences (dict): A dictionary where each key is a spelling word and the value is an example sentence.
    api_key (str): Your OpenAI API key.
    file_prefix (str): A prefix string for the audio files.
    output_directory (Path): The directory to save the generated MP3 files.
    
    Returns:
    dict: A dictionary where each key is a spelling word and the value is the path to the audio file.
    """
    audio_files = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Prepare the list of tasks
        future_to_word = {executor.submit(convert_text_to_speech_task, api_key, sentence, word, file_prefix, output_directory): word for word, sentence in sentences.items()}
        
        for future in as_completed(future_to_word):
            word = future_to_word[future]
            try:
                _, audio_file_path = future.result()
                audio_files[word] = audio_file_path
            except Exception as e:
                print(f"An error occurred while processing {word}: {e}")

    return audio_files

def create_anki_deck(audio_files, output_file):
    """
    Creates an Anki Deck import file with flashcards for each spelling word.

    Args:
    audio_files (dict): A dictionary where each key is a spelling word and the value is the path to the audio file.
    output_file (Path): The path to the output file that will be imported into Anki.

    Returns:
    Path: The path to the created Anki Deck import file.
    """
    with open(output_file, 'w', encoding='utf-8') as file:
        # Write the headers required by Anki
        file.write("#separator:tab\n")
        file.write("#html:true\n")
        file.write("#notetype column:1\n")
        
        for word, audio_path in audio_files.items():
            # Each line will have the format:
            # "Basic (type in the answer) [sound:audio_file_name.mp3] word"
            line = f"Basic (type in the answer)\t[sound:{audio_path.name}]\t{word}\n"
            file.write(line)
    
    return output_file


def main(image_file_path, output_directory):
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    # Use the current epoch time as a string for file_prefix
    file_prefix = str(int(time.time()))

    spelling_words = extract_spelling_words_from_image(image_file_path, api_key)
    example_sentences = generate_example_sentences(spelling_words, api_key)
    audio_files = convert_text_to_speech(example_sentences, api_key, file_prefix, Path(output_directory))

    output_file = Path(output_directory) / f"{file_prefix}_anki_deck.txt"
    anki_deck_file = create_anki_deck(audio_files, output_file)

    print(f"Anki Deck file created at: {anki_deck_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Anki deck from image")
    parser.add_argument("--image", dest="image_file_path", required=True,
                        help="The file path of the image to process")
    parser.add_argument("--output", dest="output_directory", required=True,
                        help="The directory to save the generated audio files and Anki deck")
    args = parser.parse_args()

    main(args.image_file_path, args.output_directory)