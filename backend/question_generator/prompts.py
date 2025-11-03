def get_chunk_prompt(chunk, part_num, total_parts, is_last):
    if is_last:
        return f"""
        You are a coding question generator.

        You have now received the FINAL Part ({part_num}/{total_parts}) of the transcript. 
        Use ALL transcript parts to generate exactly **three** coding questions.

        **Output MUST be in CLEAN PLAIN TEXT format** (NO JSON, NO BRACKETS, NO CURLY BRACES):

        Difficulty: <Beginner/Intermediate/Advanced>

        --- Question 1 ---
        Title: Q1
        Description: [Full question description here]
        Input Format: [Describe input format]
        Output Format: [Describe output format] 
        Example Input: [Example input value]
        Example Output: [Example output value]

        --- Question 2 ---
        Title: Q2
        Description: [Full question description here]
        Input Format: [Describe input format]
        Output Format: [Describe output format]
        Example Input: [Example input value]
        Example Output: [Example output value]

        --- Question 3 ---
        Title: Q3
        Description: [Full question description here]
        Input Format: [Describe input format]
        Output Format: [Describe output format]
        Example Input: [Example input value]
        Example Output: [Example output value]

        RULES:
        - NO JSON FORMATTING (no {{ }}, no [ ], no commas)
        - NO code snippets in descriptions
        - NO additional explanations or commentary
        - Use clear section headers with --- separators
        - Each field must be on its own line
        - Only include the 3 questions with the exact format above

        Transcript (Final Part):
        {chunk}
        """
    else:
        return f"""
        You are a coding question generator. 
        This transcript is being sent in PARTS. You are now reading PART {part_num} of {total_parts}.

        Transcript Part {part_num}:
        {chunk}

        Do NOT generate questions yet. Just store this context in memory for the next parts.
        """