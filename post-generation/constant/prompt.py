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
                    Now, I will give you my requirement and after I say 'Start!!!', you will start your task.
                    ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Yeah, I can help you with that. What is your requirement?"
            ),
            ChatMessage(
                role="user", content=f"""
                    create a post for a social media platform, with the keywords: {user_order}.;
                    You must write a post suitable for a social media platform.
                    - If I want to create a post for Twitter, please limit your post to maximum 280 characters.
                    - If I want to create a post for Telegram, MUST write a post with the length at least {self.max_length} characters.
                    I will provide you with some examples of posts. Please wait a moment.
                    ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Sure, I can help you with that. Please provide me with the social media platform you want to create a post for, and examples of posts."
            ),
            ChatMessage(
                role="user", content=f"""
                    Create a post for {social_platform} platform. 
                    Here are some examples of posts:
                        - Post1 content: {random.choice(list(references.values()))}
                        - Post2 content: {random.choice(list(references.values()))}
                        - Post3 content: {random.choice(list(references.values()))}
                        - Post4 content: {random.choice(list(references.values()))}
                        - Post5 content: {random.choice(list(references.values()))}
                    ----------------------------------------------------------------------------------------------

                    MUST write a post in the same style as the following list of post: {post_of_author}
                    Please use emojis that belong to the following lít emojis: {lst_emojis}. Do not use any other emojis.
                    Your post should only contain content without any unnecessary information such as "Author", 
                    "Note", "Introduction", "Conclusion", or any other end markers.
                    ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Great! I have understood your requirement. Do you have any other requirements?"
            ),
            ChatMessage(
                role="user", content="""
                    Remember that:
                        - Your post should only contain content, no additional information or introduction or conclusion.
                        - Limit the number of "\\n" in your post to a maximum of 2. Use line breaks only when you want to write a new part of your post.
                        - I found that your post usually contains hashtag at the end of the post, please flexible and creative to add it in your post.
                        ----------------------------------------------------------------------------------------------
                """
            ),
            ChatMessage(
                role="system", content="Okay, I have understood your requirement. Let's start your task now."
            ),
            ChatMessage(
                role="user", content="Start!!!"
            ),
        ]

    # def prompt_v2(self, first_reponse):
    #     prompt_v2 = [
    #         ChatMessage(
    #             role="user", content=f"""
    #                 I have received the first response from you.
    #                 Here is the post that you have created: {first_reponse}
    #                 Please remove any unnecessary information, only keep the content of the post and give me the final version of the post.
    #                 ----------------------------------------------------------------------------------------------
    #                 MUST write a post with the length at least {self.max_length} characters, Please create again, MORE CREATIVE, MORE FLEXIBLE.
    #             """),
    #     ]

    #     return prompt_v2