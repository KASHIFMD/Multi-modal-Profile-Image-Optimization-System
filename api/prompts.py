

prompts = {
  "gen_alttag": """A single short sentence suitable as image alt text for SEO.""",
  "description": """describe the image in details as if explaining to a visually impaired person""",
  "cat":"""You are a visual reasoning assistant. Carefully analyze the given image and return ONLY a valid JSON object with exactly one field: "cat_match".

Requirements:
- Return a valid JSON object.
- "cat_match": Check if this image matches the given category "{{category_name}}". If it does, return '1', otherwise return '0'.

Important:
- Do not add any comments or explanations.
- Return ONLY the JSON.
- All strings must be wrapped in double quotes.
- Ensure the JSON is well-formed and properly closed.""",
  "vision_json": """You are a visual reasoning assistant. Carefully analyze the given image and return ONLY a valid JSON object with exactly three fields: "alttag", "tags", and "description".

Requirements:
- Return a valid JSON object.
- "alttag": A single short sentence suitable as image alt text for SEO.
- "tags": A comma-separated string containing ONLY 2 to 8 short, relevant keywords. Avoid repetition or abstract concepts.
- "description": The longest and most detailed description of the image, covering layout, objects, colors, style, and context — as if explaining to a visually impaired person.

Important:
- Do not add any comments or explanations.
- Return ONLY the JSON.
- All strings must be wrapped in double quotes.
- Ensure the JSON is well-formed and properly closed."""
,
    "vision_json_cat":"""You are a visual reasoning assistant. Carefully analyze the given image and return ONLY a valid JSON object with exactly Four fields: "cat_match", "alttag", "tags", and "description".

Requirements:
- Return a valid JSON object.
- "cat_match": Check if this image matches the given category "{{category_name}}". If it does, return '1', otherwise return '"0'.
- "alttag": A single short sentence suitable as image alt text for SEO.
- "tags": A comma-separated string containing ONLY 2 to 8 short, relevant keywords. Avoid repetition or abstract concepts.
- "description": The longest and most detailed description of the image, covering layout, objects, colors, style, and context — as if explaining to a visually impaired person.

Important:
- Do not add any comments or explanations.
- Return ONLY the JSON.
- All strings must be wrapped in double quotes.
- Ensure the JSON is well-formed and properly closed.""",
    "full_details_cat": """Analyze the image and return a JSON object with the following structure:
{
  "category_match": "Yes or No — Does this image belong to the category "{{category_name}}""?",
  "contains_human": "Yes or No — Is a person visible in the image?",
  "visible_items": "Comma-separated list of key items seen in the image (e.g., chair, mirror, hair dryer, cosmetics).",
  "text_detected": "List any readable text from signs or posters in the image.",
  "description": "Write a detailed and descriptive paragraph about what is happening in the image, as if explaining it to someone who cannot see it.",
  "isBlurr": "Yes or No — Is the image visibly blurred?",
  "needEnhancement": "Yes or No — Does the image need enhancement to be more clear or useful?",
  "isNude": "Yes or No — Does the image contain nudity?",
  "nudity_score": "Decimal between 0 and 1 — 0.00 means no nudity, 1.00 means complete nudity.",
  "isWaterMarked": "Yes or No — Is there any visible watermark on the image?",
  "isScreenshots": "Yes or No — Does the image appear to be a screenshot of a device screen?",
  "AssociatedBusinessName": "Mention any business name found in the image, if visible.",
  "name": "Write an SEO-friendly title or name for the image.",
  "tags": "Comma-separated list of relevant SEO alt tags for this image.",
  "rel_tags": "Comma-separated list of SEO tags specifically related to the category "{{category_name}}".",
  "rel_description": "Write a detailed and descriptive paragraph about what is happening in the image, as if explaining it to someone who cannot see it, focusing on elements related to a Music Class."
}

Important:
- Do not add any comments or explanations.
- Return ONLY the JSON.
- All strings must be wrapped in double quotes.
- Ensure the JSON is well-formed and properly closed.
""",
    "full_details": """Analyze the image and return a JSON object with the following structure:
{
  "contains_human": "Yes or No — Is a person visible in the image?",
  "visible_items": "Comma-separated list of key items seen in the image (e.g., chair, mirror, hair dryer, cosmetics).",
  "text_detected": "List any readable text from signs or posters in the image.",
  "description": "Write a detailed and descriptive paragraph about what is happening in the image, as if explaining it to someone who cannot see it.",
  "isBlurr": "Yes or No — Is the image visibly blurred?",
  "needEnhancement": "Yes or No — Does the image need enhancement to be more clear or useful?",
  "isNude": "Yes or No — Does the image contain nudity?",
  "nudity_score": "Decimal between 0 and 1 — 0.00 means no nudity, 1.00 means complete nudity.",
  "isWaterMarked": "Yes or No — Is there any visible watermark on the image?",
  "isScreenshots": "Yes or No — Does the image appear to be a screenshot of a device screen?",
  "AssociatedBusinessName": "Mention any business name found in the image, if visible.",
  "name": "Write an SEO-friendly title or name for the image.",
  "tags": "Comma-separated list of relevant SEO alt tags for this image.",
  "rel_description": "Write a detailed and descriptive paragraph about what is happening in the image, as if explaining it to someone who cannot see it, focusing on elements related to a Music Class."
}

Important:
- Do not add any comments or explanations.
- Return ONLY the JSON.
- All strings must be wrapped in double quotes.
- Ensure the JSON is well-formed and properly closed.
"""
}
