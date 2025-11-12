from langchain_core.prompts import PromptTemplate

question_prompt = PromptTemplate(
    input_variables=["summary"],
    template="""
        Generate exactly 3 coding questions based on the video summary.

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
        - Determine difficulty based on code complexity and concepts

        Summary:
        {summary}
        """
)
