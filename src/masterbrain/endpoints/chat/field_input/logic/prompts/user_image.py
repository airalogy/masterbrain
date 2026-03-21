from typing import List

VLLM_PROMPT_EXP_HEAD = """
You are an AI assistant, providing all named entities and their corresponding values that match the experiment in the image.

Named entities include
""".strip()


def get_default_vllm_prompt_exp(key_description_list: list) -> str:
    """
    Generate a prompt for vision models to extract experiment data from images.

    Args:
        key_description_list: List of tuples containing (key, description) pairs

    Returns:
        A formatted prompt string
    """
    keys = ", ".join([key for key, _ in key_description_list])

    descriptions = "\n    ".join(
        [f"{key}: {description}" for key, description in key_description_list]
    )

    prompt = (
        VLLM_PROMPT_EXP_HEAD
        + " "
        + keys
        + ".\n\n"
        + "The experiment entities are defined below:\n"
        + "{\n    "
        + descriptions
        + "\n}\n\n"
        + "Extract only values that are clearly visible in the image. Do not include fields with null values in your output."
        + "\n\nThe output should be returned in the following JSON format:\n{\n    "
        + '"entity_name": "value"'
        + "\n}\n\n"
        + "Where 'entity_name' is the name of an entity you found in the image, and 'value' is its value. Include only entities with actual values."
        + "\nImportant: Do not infer or auto-generate time values. Only include experiment_time or other time-related fields if they are explicitly visible in the image."
    )
    return prompt


def create_image_extraction_system_prompt(key_description_list: List[tuple]) -> str:
    """
    Creates a system prompt specifically for image extraction to be used with multimodal models.

    Args:
        key_description_list: List of tuples containing (key, description) pairs

    Returns:
        A system prompt string
    """
    keys = ", ".join([key for key, _ in key_description_list])
    descriptions = "\n- ".join(
        [f"{key}: {description}" for key, description in key_description_list]
    )

    prompt = f"""You are an AI assistant specialized in extracting experiment data from images.
Your task is to identify and extract values for the following named entities:
{keys}

Details about these entities:
- {descriptions}

For any image provided:
1. Carefully analyze its content
2. Extract ONLY values that are clearly visible in the image
3. Return ONLY the entities you found with their values - omit any entities not present
4. If you're uncertain about a value, do not include it

Return your results in a concise JSON format including ONLY entities that have values:
{{
  "entity_name1": "value1",
  "entity_name2": "value2"
}}

Important: 
- Do not infer or auto-generate time values
- Only include experiment_time or other time-related fields if explicitly visible
- Only include fields with actual values - do not include null values
- Prioritize accuracy over completeness
"""
    return prompt


def clean_image_recognition_results(results: str) -> str:
    """
    Cleans and formats the image recognition results to be more concise.

    Args:
        results: Raw recognition results string, typically in JSON format

    Returns:
        Cleaned JSON string with only non-null values
    """
    try:
        import json

        # Try to parse as JSON
        data = json.loads(results)
        # Filter out null values
        cleaned_data = {
            k: v
            for k, v in data.items()
            if v and isinstance(v, str) and v.lower() != "null"
        }
        # Return formatted JSON with only valid values
        return json.dumps(cleaned_data, indent=2)
    except json.JSONDecodeError:
        # If not valid JSON, just return the original string
        return results
