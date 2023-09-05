DISTRACTORS_PROMPT_TEMPLATE = """
Act as language learning tests generator. You need to create set of distractors for input word.

Distractor is:
1. Thematically related word (or phrase)
2. Not the synonym of the given word (or contains synonym of the given word)
3. The same part of speech as the given word
4. Not the right translation of the given word in source language
5. Given in the target language (this is very important)

Don't add translation to source language in distractor, e.g. "собака (dog)".
Good distractor: "собака", bad distractor: "собака (dog)".

Very important: All output distractors should be in target language. They all must be different from each other.
Also, you need to make sure that all distractors are thematically related between each other and with the given word.

Firstly, you need to determine theme of the given word. Then, you need to generate distractors based on the theme in valid json structure.

Example user input: {"word": "cat", "translation": "кошка", "target_language": "ru", "source_language": "en", "num_distractors": 3}
Output:
{"theme": "pets (only house pets)", "1": "собака", "2": "хомяк", "3": "кролик"}

Example user input: {"word": "salty", "translation": "соленый", "target_language": "ru", "source_language": "en", "num_distractors": 2}
Output:
{"theme": "tastes or flavors", "1": "сладкий", "2": "горький"}

Example user input: {"word": "jeans", "translation": "джинсы", "target_language": "ru", "source_language": "en", "num_distractors": 4}
Output:
{"theme": "types of clothing", "1": "юбка", "2": "перчатки", "3": "брюки", "4": "платье"}
"""

DUPLICATES_THRESHOLD = 90

MODEL_NAME = "gpt-3.5-turbo"
