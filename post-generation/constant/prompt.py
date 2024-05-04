
class RAGPrompt:
     def __init__(self, user_order, references):
        self.prompt = f"""
            - Please write me a twitter post with user's given keywords, using the writting style and the icons of these following tweets:
                - tweet1 with the context: {references['tweet 0']}
                - tweet2 with the context: {references['tweet 1']}
                - tweet3 with the context: {references['tweet 2']}
                - tweet4 with teh context: {references['tweet 3']}
                - tweet5 with the  context: {references['tweet 4']}


            - User's given: Please write me a twitter post with keywords: {user_order}
            Write your answer in the commentary form:
            "answer": \n
            "your twitter post answer"
            Note: your answer should have 3 main parts: title, main content, ending part with hashtags like these 5 above tweets
            Start!
        """
        

class NormalPrompt:
    def __init__(self, user_order):
        self.prompt = f"""
            - Please execute the following user order
            - User order: Please write me a twitter post with keywords: {user_order}
            Write your answer in the commentary form:
            "answer": \n
            "your answer"
            Note: your answer should have 3 main parts: title, main content, ending part
            Start!
        """
