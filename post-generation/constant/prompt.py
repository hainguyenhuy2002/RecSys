from llama_index.core.llms import ChatMessage

class RAGPrompt:
     def __init__(self, user_order, references, social_platform):
        self.prompt = [
            ChatMessage(
                role="user", content="""
                    You are a professional marketer and your task is to create a post for a social media platform.
                    Now, I will give you my requirement and after I say 'Start!!!', you will start your task.
                """
            ),
            ChatMessage(
                role="system", content="Yeah, I can help you with that. What is your requirement?"
            ),
            ChatMessage(
                role="user", content=f"""
                    I want to create a post for a social media platform with the keywords: {user_order}.;
                    You must write a post suitable for a social media platform.
                    - If I want to create a post for Twitter, please limit your post to maximum 280 characters.
                    - If I want to create a post for Telegram or Discord, consider your post with longer content and more detailed information.
                    I will provide you with some examples of posts. Please wait a moment.
                """
            ),
            ChatMessage(
                role="system", content="Sure, I can help you with that. Please provide me with the social media platform you want to create a post for, and examples of posts."
            ),
            ChatMessage(
                role="user", content=f"""
                    I want to create a post for {social_platform}. 
                    Here are some examples of posts:
                        - Post1 content: {references[f'post {0}']}
                        - Post2 content: {references[f'post {1}']}
                        - Post3 content: {references[f'post {2}']}
                        - Post4 content: {references[f'post {3}']}
                        - Post5 content: {references[f'post {4}']}
                    Please write a post in the same style and layout as the above posts. 
                    Your post should only contain content without any unnecessary information such as "Author", 
                    "Note", "Introduction", "Conclusion", or any other end marker
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
                """
            ),
            ChatMessage(
                role="system", content="Okay, I have understood your requirement. Let's start your task now."
            ),
            ChatMessage(
                role="user", content="Start!!!"
            ),
        ]

class NormalPrompt:
    def __init__(self, user_order):
        self.prompt = f"""   
            Please execute the following user order
            User order: 

                Please write me a twitter post with keywords: {user_order}
                Write your answer in the commentary form:"answer": \n"your answer"
                Note: your answer should have 3 main parts: title, main content, ending part
                
            Start!"""