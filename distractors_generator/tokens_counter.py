from typing import List

import tiktoken


def encoding_getter(encoding_type: str) -> tiktoken.Encoding:
    """
    Get the encoding object for a given encoding type.

    Args:
        encoding_type (str): The encoding type, which can be an encoding string or a model name.

    Returns:
        tiktoken.Encoding: The encoding object based on the provided encoding type.
    """
    if "k_base" in encoding_type:
        return tiktoken.get_encoding(encoding_type)
    else:
        return tiktoken.encoding_for_model(encoding_type)


def tokenizer(string: str, encoding_type: str) -> List[int]:
    """
    Tokenize a text string using the specified encoding.

    Args:
        string (str): The input text string to tokenize.
        encoding_type (str): The encoding type to use for tokenization.

    Returns:
        List[str]: A list of tokens extracted from the input text using the specified encoding.
    """
    encoding = encoding_getter(encoding_type)
    tokens = encoding.encode(string)
    return tokens


def token_counter(string: str, encoding_type: str) -> int:
    """
    Count the number of tokens in a text string using the specified encoding.

    Args:
        string (str): The input text string to count tokens in.
        encoding_type (str): The encoding type to use for token counting.

    Returns:
        int: The total number of tokens in the input text using the specified encoding.
    """
    num_tokens = len(tokenizer(string, encoding_type))
    return num_tokens
