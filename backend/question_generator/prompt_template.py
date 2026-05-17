from langchain_core.prompts import PromptTemplate

question_prompt = PromptTemplate(
    input_variables=["summary"],
    template="""
        Generate exactly 3 coding questions based on the provided context.

        IMPORTANT CONTEXT RULES:
        - The context may come from video metadata (title, description, topic) and NOT a transcript.
        - If the context is written in any human language:
            • FIRST, internally understand and convert it to English
            • THEN generate all questions strictly in clear, simple English
        - Do NOT mention any translation, inference, or assumptions in the output.
        - Do NOT reference a video, speaker, instructor, or creator.

        QUESTION QUALITY RULES (VERY IMPORTANT):
        - Each question must be PLATFORM-AGNOSTIC.
        - Do NOT include execution notices, environment warnings, or UI instructions.
        - Do NOT describe implementation details (e.g., variable names, file handles) as input.
        - Input Format must describe WHAT is provided, not HOW it is implemented.
        - Output Format must describe ONLY the expected result.
        - Avoid mentioning specific functions unless they are core to the problem concept.
        - Questions must be clear, concise, and standard for programming practice.

        **Output MUST be in CLEAN PLAIN TEXT format** (NO JSON, NO BRACKETS, NO CURLY BRACES):

        Difficulty: <Beginner/Intermediate/Advanced>

        --- Question 1 ---
        Title: Q1
        Description: [Clear problem statement only]
        Input Format: [Describe conceptual input]
        Output Format: [Describe expected output]
        Example Input: [Concrete example input]
        Example Output: [Concrete example output]

        --- Question 2 ---
        Title: Q2
        Description: [Clear problem statement only]
        Input Format: [Describe conceptual input]
        Output Format: [Describe expected output]
        Example Input: [Concrete example input]
        Example Output: [Concrete example output]

        --- Question 3 ---
        Title: Q3
        Description: [Clear problem statement only]
        Input Format: [Describe conceptual input]
        Output Format: [Describe expected output]
        Example Input: [Concrete example input]
        Example Output: [Concrete example output]

        RULES:
        - NO JSON FORMATTING (no {{ }}, no [ ], no commas)
        - NO code snippets in descriptions
        - NO platform-specific instructions
        - NO meta commentary
        - Each field must be on its own line
        - Use exact section headers with --- separators
        - Only include the 3 questions with the exact format above
        - Determine difficulty based on algorithmic and conceptual complexity
        - Prefer standard textbook-style problem statements

        Context:
        {summary}
        """
)
