import json
import random
import time
from json import JSONDecodeError
from typing import Dict, List, Optional, Tuple

import openai
from openai.error import RateLimitError, ServiceUnavailableError
from thefuzz import fuzz

from distractors_generator.constants import (DISTRACTORS_PROMPT_TEMPLATE,
                                             DUPLICATES_THRESHOLD, MODEL_NAME)
from distractors_generator.tokens_counter import token_counter


class DistractorGenerator:
    def __init__(self, model: str = MODEL_NAME):
        self._system_prompt = DISTRACTORS_PROMPT_TEMPLATE
        self._model = model

    @property
    def tokens_count(self) -> int:
        """
        Get the number of tokens in the system prompt.

        Returns:
            int: number of tokens
        """
        return token_counter(self._system_prompt, self._model)

    def _is_duplicate(self, a: str, b: str, threshold: int = DUPLICATES_THRESHOLD) -> bool:
        """
        Check if two strings are duplicates.

        Args:
            a (str): first string
            b (str): second string
            threshold (int, optional): threshold for thefuzz partial ratio. Defaults to DUPLICATES_THRESHOLD.

        Returns:
            bool: True if strings are duplicates, False otherwise
        """
        return fuzz.partial_ratio(a, b) > threshold

    def _drop_duplicates(
        self, distractors: List[str], threshold: int = DUPLICATES_THRESHOLD
    ) -> Tuple[List[str], List[str]]:
        """
        Remove (almost) duplicates from distractors list.

        Example: ["example", "example as", "feature"] -> ["feature"], ["example", "example as"]

        Args:
            distractors (List[str]): list of distractors
            threshold (int, optional): threshold for thefuzz partial ratio. Defaults to DUPLICATES_THRESHOLD.

        Returns:
            1. List[str]: list of unique distractors
            2. List[str]: list of found duplicates
        """
        duplicates, unique = [], []
        for i, distractor in enumerate(distractors):
            for j, distractor2 in enumerate(distractors):
                if i != j and self._is_duplicate(distractor, distractor2, threshold):
                    duplicates.append(distractor2)
                    break
            else:
                unique.append(distractor)

        return unique, duplicates

    def _safe_generate(
        self,
        message_history: List[Dict[str, str]],
        temperature: float = 0.8,
        num_trials: int = 3,
    ) -> Optional[Dict]:
        """
        Safely generate and parse response from OpenAI API.

        Args:
            message_history (List[Dict[str, str]]): message history
            temperature (float, optional): temperature for OpenAI API. Defaults to 0.8.
            num_trials (int, optional): number of unsuccessful trials. Defaults to 3.

        Returns:
            Optional[Dict]: Parsed OpenAI API response (None if unsuccessful trials > num_trials)
        """
        for _ in range(num_trials):
            try:
                response = openai.ChatCompletion.create(
                    model=self._model,
                    messages=message_history,
                    temperature=temperature,
                )["choices"][0]["message"]["content"]
                return self._parse_output_json(response)

            except JSONDecodeError:
                continue

            except (RateLimitError, ServiceUnavailableError) as e:
                wait_time = e.headers.get("Retry-After", 20)
                time.sleep(wait_time)
                continue

        return None

    def _parse_output_json(self, response: str) -> Dict:
        """
        Parse response from OpenAI API.

        Args:
            response (str): response from OpenAI API

        Returns:
            Dict: parsed response
        """
        try:
            return json.loads(response)
        except JSONDecodeError:
            return json.loads(response[response.find("{") : response.find("}") + 1])

    def _parse_distractors_dict(self, distractors_dict: Dict) -> List[str]:
        """
        Convert distractors dict to list of distractors.

        Example: {"1": "cat", "2": "dog"} -> ["cat", "dog"]

        Args:
            distractors_dict (Dict): distractors dict
        """
        return [v for k, v in distractors_dict.items() if k.isdigit()]

    def _generate_unique_distractors_batch(
        self,
        message_history: List[Dict[str, str]],
        distractors: List[str],
        expected_count: int,
        num_trials: int = 1,
        temperature: float = 1.2,
    ) -> List[str]:
        """
        Try to generate unique distractors for deduplication.

        Args:
            message_history (List[Dict[str, str]]): prompt for OpenAI API
            distractors (List[str]): list of distractors
            expected_count (int): expected number of distractors
            num_trials (int, optional): number of generation trials. Defaults to 1.
            temperature (float, optional): temperature for OpenAI API. Defaults to 1.2.

        Returns:
            List[str]: list of unique distractors
        """
        # Quick check if we have enough distractors
        if len(distractors) >= expected_count:
            return distractors

        # We can't generate any new distractors if we have no trials
        if num_trials == 0:
            return distractors

        for _ in range(num_trials):
            # Infer model and get response
            distractors_dict = self._safe_generate(message_history, temperature=temperature)

            # Check if we have response
            if distractors_dict is None:
                continue

            # Parse response to list of distractors
            distractors_new = self._parse_distractors_dict(distractors_dict)

            # Check if we have new unique distractors
            for new_dis in distractors_new:
                is_duplicate = any([self._is_duplicate(new_dis, dis) for dis in distractors])
                if not is_duplicate:
                    distractors.append(new_dis)

            if len(distractors) >= expected_count:
                break

        return distractors

    def generate(
        self,
        word: str,
        translation: str,
        source_language: str = "en",
        target_language: str = "ru",
        count: int = 3,
        deduplicate_num_trials: int = 1,
        deduplicate_temperature: float = 1.2,
    ) -> List[str]:
        """
        Generate a list of distractors for a given word and its translation
        Args:
            word (str): The word in source language.
            translation (str): The translation of the word in target language.
            source_language (str, optional): The source language (default is "en").
            target_language (str, optional): The target language (default is "ru").
            count (int, optional): The number of distractors to generate (default is 3).
            deduplicate_num_trials (int, optional): The number of trials to deduplicate distractors
                (default is 1).
            deduplicate_temperature (float, optional): The temperature for deduplication trials
                (default is 1.2)
        Returns:
            List[str]: A list of generated distractors for the word.
        """
        # Create input dict
        input_dict = {
            "word": word,
            "translation": translation,
            "source_language": source_language,
            "target_language": target_language,
            "num_distractors": count,
        }

        # Dump input dict to json string
        input_json = json.dumps(input_dict)

        # Add input json to self._prompt
        message_history = [
            {"role": "user", "content": self._system_prompt},
            {
                "role": "assistant",
                "content": "Ready to generate distractors. Waiting for input...",
            },
            {"role": "user", "content": input_json},
        ]

        # Infer model and get response
        distractors_dict = self._safe_generate(message_history)

        # Parse response to list of distractors
        distractors = self._parse_distractors_dict(distractors_dict)

        # Remove translation from distractors list (if it exists)
        distractors = [dis for dis in distractors if dis != translation]

        # Remove duplicates from distractors list
        distractors, duplicates = self._drop_duplicates(distractors)

        # If we have duplicates, we need to generate new distractors
        distractors = self._generate_unique_distractors_batch(
            message_history=message_history,
            distractors=distractors,
            expected_count=count,
            num_trials=deduplicate_num_trials,
            temperature=deduplicate_temperature,
        )

        # If we still don't have enough distractors, just sample from duplicates
        if len(distractors) < count:
            distractors += random.sample(duplicates, count - len(distractors))

        return distractors
