# Anki-Spelling-Generator

Given an image of words, the Anki-Spelling-Generator processes the image to extract spelling words, generates audio example sentences, and creates Anki flashcards for children to practice spelling.

## Setup

1. Set up a Python environment (preferably using virtual environments).
2. Install the required packages with `pip install openai requests`.
3. Ensure your OpenAI API Key is set in the `OPENAI_API_KEY` environment variable.

## Usage

Run the script using the command line with the following named parameters:

- `--image`: The file path to the image containing the words.
- `--output`: The directory path where you want the audio files and Anki deck to be saved.

Example command:

```bash
python3 anki_spelling_generator.py --image "path_to_image.jpg" --output "path_to_output_directory"
```

## Integration with Anki
After running the script:

1. Copy the generated mp3 files into your Anki media folder.
On Windows, this is typically located at: C:\Users\{username}\AppData\Roaming\Anki2\{anki_username}\collection.media.
2. Import the {epoch_time}_anki_deck.txt file into an existing or new Anki deck, where {epoch_time} is the timestamp of when the script was run.