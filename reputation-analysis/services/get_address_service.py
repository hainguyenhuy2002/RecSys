from pymongo import MongoClient
import json
import os



if __name__ == '__main__':
    link = os.getenv('MONGODB_ENTITY_CONNECTION_URL')
    print(link)
    client = MongoClient(link)  # Update the connection string as per # Select the database
    db = client["knowledge_graph"]  # Replace "your_database_name" with your actual database name
    collection = db["wallets"]
        
    query = {"balanceChangeLogs":{"$exists":"True"}, "chainId":"0x1", "balanceInUSD":{"$lte":50000}, "balanceInUSD":{"$gte":10}}
    query = {"address":"0x6f98f8293073b8017422d3afa8b35a34f4ebd375"}
    result = collection.find(query,{'address':1})
    address_lst = []
    for document in result:
        address_lst.append(document['address'])


    client.close()

    with open('../data/eth_address.json', 'w') as json_file:
        json.dump(address_lst, json_file,indent=4)
    