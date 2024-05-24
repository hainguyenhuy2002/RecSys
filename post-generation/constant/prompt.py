import random
from llama_index.core.llms import ChatMessage

class RAGPrompt:
     def __init__(self, user_order, references, lst_emojis, social_platform):
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
                    - If I want to create a post for Telegram or Discord, consider your post with longer content and more detailed information.
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
                        - Post1 content: {references[f'post {random.randint(1, len(references))}']}
                        - Post2 content: {references[f'post {random.randint(1, len(references))}']}
                        - Post3 content: {references[f'post {random.randint(1, len(references))}']}
                        - Post4 content: {references[f'post {random.randint(1, len(references))}']}
                        - Post5 content: {references[f'post {random.randint(1, len(references))}']}
                    Please write a post in the same style and layout as the above posts. 
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

# After get the first response of llm, prompt again to improve the quality of the post 
class NormalPrompt:
    def __init__(self, first_reponse, social_platform):
        self.prompt = [
            ChatMessage(
                role="user", content=f"""
                    I have received the first response from you.
                    Here is the post that you have created: {first_reponse}
                    Please remove any unnecessary information, only keep the content of the post and give me the final version of the post.
                    ----------------------------------------------------------------------------------------------
                """),
        ]