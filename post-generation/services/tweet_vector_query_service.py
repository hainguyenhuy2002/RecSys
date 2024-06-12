from llama_index.core.vector_stores import VectorStoreQuery

def tweet_vector_query(EmbedModel, vector_store, input, top_simi): 
    query_mode = "default"
    query_embedding = EmbedModel.get_query_embedding(input)

    vector_store_query = VectorStoreQuery(
    query_str=query_embedding, similarity_top_k=top_simi, mode=query_mode
    )

    query_result = vector_store.query(vector_store_query)
    tweet_simi =dict()

    for i in range(0, top_simi):
        tweet_simi[f'post {i+1}'] = query_result.nodes[i].get_content()
    return tweet_simi
