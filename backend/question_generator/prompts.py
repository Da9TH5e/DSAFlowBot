def get_chunk_prompt(chunk, part_num, total_parts, is_last):
    if is_last:
        return f"""
        You are a coding question generator.

        You have now received the FINAL Part ({part_num}/{total_parts}) of the transcript. 
        Use ALL transcript parts to generate exactly **three** coding questions.

        IMPORTANT CONTEXT RULES:
        - The context may come from video metadata (title, description, topic) and NOT a transcript.
        - If the context is written in any human language:
            • FIRST, internally understand and convert it to English
            • THEN generate all questions strictly in clear, simple English
        - Do NOT mention any translation, inference, or assumptions in the output.
        - Do NOT reference the video, speaker, or creator.

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
        
	IMPORTANT CONTEXT NOTICE:
        - The provided content represents PARTIAL CONTEXT of a programming tutorial.
        - This context may come from transcript text OR from metadata
          (topic, language, title, description).
        - Treat it as authoritative and factual.

        This context is being sent in PARTS.
        You are now reading PART {part_num} of {total_parts}.

        Context Part {part_num}:
        {chunk}

        Do NOT generate questions yet. Just store this context in memory for the next parts.
        """
