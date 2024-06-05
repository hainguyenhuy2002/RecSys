import random
from llama_index.core.llms import ChatMessage

class RAGPrompt:
    def __init__(self, user_order, references, lst_emojis, social_platform, post_of_author):
        max_length = 0
        for key, value in references.items():
            if len(value) > max_length:
                max_length = len(value)

        self.max_length = max_length
        self.prompt = [
            ChatMessage(
                role="user", content="""
                    You are a professional marketer and your task is to create a post for a social media platform.
                    I will give you my requirement and after I say 'Start!!!', you will start your task.
                    ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Yeah, I can help you with that. What is your requirement?"
            ),
            ChatMessage(
                role="user", content=f"""
                    Create a post for a social media platform with the keywords: {user_order}.
                    - For Twitter, limit your post to 280 characters.
                    - For Telegram, the post must be at least {self.max_length} characters.
                    I will provide you with some examples of posts. Please wait a moment.
                    ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Sure, I can help you with that. Please provide me with the social media platform you want to create a post for, and examples of posts."
            ),
            ChatMessage(
                role="user", content=f"""
                    Create a post for the {social_platform} platform. You should base the content on the examples below but follow the style and format of {post_of_author}.
                    - Post1: {random.choice(list(references.values()))}
                    - Post2: {random.choice(list(references.values()))}
                    - Post3: {random.choice(list(references.values()))}
                    - Post4: {random.choice(list(references.values()))}
                    - Post5: {random.choice(list(references.values()))}
                    ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Great! I have understood your requirement. Do you have any other requirements?"
            ),
            ChatMessage(
                role="user", content=f"""
                    Remember:
                    - Please write a post in the same style and format as: {post_of_author}
                    - Please use only the emojis: {lst_emojis}
                    - Post should only contain content, no additional information.
                    - Limit the number of "\\n" to a maximum of 2.
                    - Be flexible and creative with hashtags.
                    ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Okay, I have understood your requirement. Let's start your task now."
            ),
            ChatMessage(
                role="user", content="Start!!!"
            )
        ]

        