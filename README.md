# Anki-Spelling-Generator
Given an image of words, generates audio example sentences and Anki cards.

This code is toy code / demonstration, and requires some setup.

- Setup a python environment.
- Install `openai` and `requests`.
- Update `api_key` in the code with your OpenAI API Key
- Update the file path in the code to a path to your image with the spelling words you want to have turned into Anki Flashcards
- It doesn't hurt to debug, otherwise you might get an error and not know :D And then it generates sentences for the error message split into words :D
- Update the output path for Audio files / Anki Export file


When the script is complete copy the mp3 files into your Anki media folder. On Windows: `C:\Users\{username}\AppData\Roaming\Anki2\{anki_username}\collection.media`.
Import the `001_anki_deck.txt` file into an existing or new Anki deck.
