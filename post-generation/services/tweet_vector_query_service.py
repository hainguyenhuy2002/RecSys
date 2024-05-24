from llama_index.core.vector_stores import VectorStoreQuery
import emoji

def tweet_vector_query(EmbedModel, vector_store, input, top_simi): 
    query_embedding = EmbedModel.get_query_embedding(input)
    query_mode = "default"
    vector_store_query = VectorStoreQuery(
    query_embedding=query_embedding, similarity_top_k=top_simi, mode=query_mode
    )

    query_result = vector_store.query(vector_store_query)
    tweet_simi =dict()
    j = 1
    for i in range(0, top_simi):
        # Filter the query result which have the length of content < 350
        if len(query_result.nodes[i].get_content()) < 350:
            tweet_simi[f'post {j}'] = query_result.nodes[i].get_content()
            j += 1
    
    lst_emojis = []
    for key, value in tweet_simi.items():
        values = emoji.emoji_list(value)
        for i in values:
            lst_emojis.append(i.get('emoji'))

    return tweet_simi, lst_emojis