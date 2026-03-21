from langchain.prompts.prompt import PromptTemplate


def create_slot_extraction_prompt(
    key_description_list: list,
) -> PromptTemplate:
    keys = ", ".join([key for key, _ in key_description_list])
    descriptions = "\n    ".join(
        [f"{key}: {description}" for key, description in key_description_list]
    )

    prompt_template = (
        SLOT_EXTRACTION_HEAD_TEMPLATE + " " + keys + ".\n\n"
        "The experiment name entities are defined below:\n"
        "{{\n    "
        + descriptions
        + "\n}}\n\n"  # Double braces {{ }} to escape in format string
        + SLOT_EXTRACTION_TAIL_TEMPLATE
    )

    return PromptTemplate(
        input_variables=[
            "history",
            "input",
            "slots",
            "check",
            "current_datetime",
            "is_from_image",
        ],
        template=prompt_template,
    )


SLOT_EXTRACTION_HEAD_TEMPLATE = """
You are an AI assistant, reading the transcript of a conversation between an AI and a human.
From the last line of the conversation, extract all proper named entities (here denoted as slots) that match recording an experiment.
Named entities required for recording the experiment result include
""".strip()

SLOT_EXTRACTION_TAIL_TEMPLATE = """
Important: Do not infer or auto-generate time values. Only update experiment_time or any time-related fields if explicitly mentioned by the user or clearly visible in the image.\n\n
If there is no match for each slot, assume null (e.g., user is simply saying hello or having a brief conversation).
After Output Slots, you should provide one or more formatting instructions for updates: UPDATE `slot_name` `old_value` `new_value`.

The output should be returned in the following format:
{{
    "slot_name_1": "value_1",
    "slot_name_2": "value_2",
    ...
}}
~~~
UPDATE slot_name old_value new_value
...

EXAMPLE
Conversation history:
Human: "I want to record an experiment."
AI: "Hi, what is the slot_name_1?"
Current Slots: {{"slot_name_1": null, "slot_name_2": null, "slot_name_3": null, "slot_name_4": null, "slot_name_5": null, ...}}
~~~
UPDATE null null null
Last line:
Human: "50.0, and the slot_name_4 is 7.2"
Output Slots: {{"slot_name_1": "50.0", "slot_name_2": null, "slot_name_3": null, "slot_name_4": "7.2", "slot_name_5": null, ...}}
~~~
UPDATE slot_name_1 null 50.0
UPDATE slot_name_4 null 7.2
END OF EXAMPLE

EXAMPLE-1
Conversation history:
Human: "I want to change the value of slot_name_2."
AI: "OK, what value do you want to change for the slot_name_2?"
Current Slots: {{"slot_name_1": null, "slot_name_2": "2.0", "slot_name_3": null, "slot_name_4": null, "slot_name_5": null, ...}}
~~~
UPDATE null null null
Last line:
Human: "1.0"
Output Slots: {{"slot_name_1": null, "slot_name_2": "1.0", "slot_name_3": null, "slot_name_4": null, "slot_name_5": null}}
~~~
UPDATE slot_name_2 2.0 1.0

EXAMPLE-2
Conversation history:
Human: "我想开始一个实验。"
AI: "好的, 请问slot_name_1是多少？"
Current Slots: {{"slot_name_1": null, "slot_name_2": null, "slot_name_3": null, "slot_name_4": null, "slot_name_5": null, ...}}
~~~
UPDATE null null null
Last line:
Human: "28.0"
Output Slots: {{"slot_name_1": "28.0", "slot_name_2": null, "slot_name_3": null, "slot_name_4": null, "slot_name_5": null, ...}}
~~~
UPDATE slot_name_1 null 28.0

EXAMPLE-3
Conversation history:
Human: "asfg3g3ddg3"
AI: "I didn't understand what you meant. What is the slot_name_1?"
Current Slots: {{"slot_name_1": null, "slot_name_2": null, "slot_name_3": null, "slot_name_4": null, "slot_name_5": null, ...}}
~~~
UPDATE null null null
Last line:
Human: "23.6"
Output Slots: {{"slot_name_1": "23.6", "slot_name_2": null, "slot_name_3": null, "slot_name_4": null, "slot_name_5": null}}
~~~
UPDATE slot_name_1 null 23.6

EXAMPLE-4
Conversation history:
Human: "I want to share an image with you"
AI: "Please upload your image and I'll try to extract information from it"
Current Slots: {{"slot_name_1": null, "slot_name_2": null, "slot_name_3": null, "slot_name_4": null, "slot_name_5": null, ...}}
~~~
UPDATE null null null
Last line:
Human: "<Image containing text: 'Experiment results: slot_name_1: 45.2, slot_name_3: 9.8, slot_name_5: positive'>"
Output Slots: {{"slot_name_1": "45.2", "slot_name_2": null, "slot_name_3": "9.8", "slot_name_4": null, "slot_name_5": "positive"}}
~~~
UPDATE slot_name_1 null 45.2
UPDATE slot_name_3 null 9.8
UPDATE slot_name_5 null positive

Output Slots must be in JSON format!
If there is no update, the update info is `UPDATE null null null`!
Don't forget to include ~~~ between the output slots and the update infos.

Begin!
Current datetime: {current_datetime}
Conversation history (for reference only):
{history}
Current Slots:
{slots}
Last line of conversation (for extraction):
Human: {input}{is_from_image}

Output Slots:""".strip()
