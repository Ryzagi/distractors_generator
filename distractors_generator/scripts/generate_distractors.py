import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from distractors_generator.generator import DistractorGenerator


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input_path",
        type=Path,
        help="Path to file with pairs of words and its translations",
        required=True,
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=10,
        help="Number of distractors to generate for each word",
    )
    parser.add_argument(
        "-d",
        "--deduplicate_trials",
        type=int,
        default=1,
        help="Max. number of trials to deduplicate distractors",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=Path,
        default="distractors.json",
        help="Path to the output JSON file",
    )
    return parser.parse_args()


def generate_disctactors(
    input_path: Path,
    output_path: Path,
    count: int = 10,
    deduplicate_trials: int = 1,
) -> None:
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize distractor generator
    generator = DistractorGenerator()

    # Log the number of tokens in the prompt
    logger.info(f"Tokens in the prompt: {generator.tokens_count}")

    # Load the CSV file with word translations
    df = pd.read_csv(input_path)
    # Keeping track of time taken to generate distractors
    generation_times = []

    # Create storage for outputs
    outputs = []

    # Iterate over the rows of the CSV file
    for index in tqdm(range(len(df)), desc="Generating Distractors", unit="pair"):
        # Parse the row
        source_language = df.iloc[index]["source_language"]
        target_language = df.iloc[index]["target_language"]
        word = df.iloc[index]["word"]
        translation = df.iloc[index]["translation"]
        start_time = time.time()  # Record the start time
        response = generator.generate(
            word=word,
            translation=translation,
            source_language=source_language,
            target_language=target_language,
            count=count,
            deduplicate_num_trials=deduplicate_trials,
        )
        generation_times.append(time.time() - start_time)

        # Save the output to the JSONL file
        output_item = {
            "word": word,
            "translation": translation,
            "distractors": response,
        }

        # Append the current output to the existing JSONL file
        outputs.append(output_item)

    # Log the average time taken to generate distractors
    generation_times = np.array(generation_times)
    logger.info(
        f"Generation time: {generation_times.mean():.3f} ± {generation_times.std():.3f} sec."
    )

    # Dump to json file
    output_path.write_text(
        json.dumps(outputs, ensure_ascii=False, indent=4), encoding="utf-8"
    )

    logger.info(f"Saved distractors to {output_path}")


def main():
    args = parse_args()
    generate_disctactors(
        input_path=args.input_path,
        output_path=args.output_path,
        count=args.count,
        deduplicate_trials=args.deduplicate_trials,
    )


if __name__ == "__main__":
    main()
