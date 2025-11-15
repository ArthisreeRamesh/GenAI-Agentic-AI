"""
Graph RAG with Neo4j and OpenAI - Complete Implementation
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
import plotly.graph_objs as go

# Load environment variables
load_dotenv()

# Create OpenAI client using API key from file
def _create_openai_client():
    key_file_path = os.path.join(os.path.dirname(__file__), "keys", "openaiapikey.txt")
    try:
        with open(key_file_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
            if not api_key:
                raise ValueError("OpenAI API key file is empty.")
    except Exception as e:
        raise RuntimeError(f"Failed to read OpenAI API key from {key_file_path}: {e}")
    return OpenAI(api_key=api_key)

openai_client = _create_openai_client()

# Helper to safely obtain Neo4j URI
def _get_neo4j_uri():
    uri = os.getenv("NEO4J_URI", "").strip()
    # If URI is missing or does not contain a scheme, fall back to the Aura URI from credentials
    if not uri or "://" not in uri:
        uri = "neo4j+s://9a000976.databases.neo4j.io"
    return uri

# Initialize lists to store data
ontology_list = []
node_creation_cypher_list = []

# Function to identify relationships and nodes
def identify_relationships_and_nodes(file_text):
    
    system_prompt = f"""Assistant is a Named Entity Recognition (NER) expert. The assistant can identify named entities 
    such as a person, place, or thing. The assistant can also identify entity relationships, which describe
    how entities relate to each other (eg: married to, located in, held by). Identify the named entities
    and the entity relationships present in the text by returning comma separated list of tuples
    representing the relationship between two entities in the format (entity, relationship, entity). Only
    generate tuples from the list of entities and the possible entity relationships listed below. Return
    only generated tuples in a comma separated tuple separated by a new line for each tuple.

    Entities:
    - Hotel
    - Location
    - Facilities
    - CustomerType
    - Reviewer

    Relationships:
    - [Hotel],is_located_in,[Location]
    - [Hotel],has_facilities,[Facilities]
    - [Hotel],has_customers,[CustomerType]
    - [Hotel],has_reviewer,[Reviewer]

    Example Output:
    Creek Hotel,is_located_in,Dubai
    Creek Hotel,has_facilities,swimming pool
    Creek Hotel,has_customers,Businessmen
    Creek Hotel,has_customers,senior citizens
    Creek Hotel,has_reviewer,John Doe

    """

    user_prompt = f"""Identify the named entities and entity relationships in the hotel review text above. Return the
    entities and entity relationships in a tuple separated by commas. Return only generated tuples in a
    comma separated tuple separated by a new line for each tuple.

    Text: {file_text}"""

    chat_completions_response = openai_client.chat.completions.create(
        model = os.getenv("GPT_ENGINE"),
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )
    
    ontology_list.append(chat_completions_response.choices[0].message.content)

    print(chat_completions_response.choices[0].message.content)
    return chat_completions_response.choices[0].message.content

# Function to generate Cypher query for node creation
def generate_cypher_for_node_creation(ontology_text):
    cypher_system_prompt = f""" Assistant is an expert in Neo4j Cypher development. Create a cypher query to generate a graph using the data points provided. 
    make sure to only include the cypher query in your response so that I can directly send this cypher query to the Neo4j database API endpoint
    via a POST request. The data is in the format of a comma separated tuple separated by a new line for each tuple.

    """
    
    cypher_user_prompt = f"""Generate a cypher query to create new nodes and their relationships given the data provided. Return only the cypher query. 
    Data is composed of relationships between entities that have been extracted using NER.
    The data is in the format of a comma separated tuple separated by a new line for each tuple.
    
    Example Input: 
    Creek Hotel,is_located_in,Dubai
    Creek Hotel,has_customers,businessmen
    Creek Hotel,has_customers,tourists
    Creek Hotel,has_reviewer,Ryouta Sato
    Creeh Hotel,has_facilities,swimming pool

    Example Output:
    CREATE (ch:Hotel {{name: 'Creek Hotel'}})-[:is_located_in]->(d:Location {{name: 'Dubai'}}),
        (ch)-[:has_customers]->(b:CustomerType {{name: 'businessmen'}}),
        (ch)-[:has_customers]->(t:CustomerType {{name: 'tourists'}}),
        (ch)-[:has_reviewer]->(rs:Reviewer {{name: 'Ryouta Sato'}}),
        (ch)-[:has_facilities]->(sp:Facilities {{name: 'swimming pool'}})
        
    strictly stick to the above output format
    
    use distinct variable names for each node and relationship to avoid conflicts

    the data is: {ontology_text}

    """
    
    cypher_query = openai_client.chat.completions.create(
        model = os.getenv("GPT_ENGINE"),
        messages = [
            {"role": "system", "content": cypher_system_prompt},
            {"role": "user", "content": cypher_user_prompt}
        ],
        temperature=0
    )
    
    node_creation_cypher_list.append(cypher_query.choices[0].message.content)

    print(cypher_query.choices[0].message.content)
    return cypher_query.choices[0].message.content

# Function to strip markdown code blocks from Cypher queries
def strip_markdown_code_blocks(query):
    """
    Remove markdown code block markers (```) from Cypher queries
    """
    if query.startswith('```'):
        # Find the end of the first code block marker
        first_marker_end = query.find('\n', 3)
        if first_marker_end != -1:
            query = query[first_marker_end + 1:]
    
    # Remove trailing code block markers
    if '```' in query:
        query = query.split('```')[0]
    
    return query.strip()

# Function to query Neo4j graph
def query_neo4j_graph(user_query):
    query_with_cypher_system_prompt = f"""Assistant is an expert in Neo4j Cypher development. Only return a cypher query based on the user query
    the cypher graph has the following schema:

    Nodes:
    - Hotel
    - Location
    - Facilities
    - CustomerType
    - Reviewer

    Relationships:
    - [Hotel],is_located_in,[Location]
    - [Hotel],has_facilities,[Facilities]
    - [Hotel],has_customers,[CustomerType]
    - [Hotel],has_reviewer,[Reviewer]

    example of a node created through cypher query:
    {node_creation_cypher_list[0] if node_creation_cypher_list else ""}
    
    Example Input:
    what hotels are reviewed by Ryouta Sato?
    
    Example Output:
    MATCH (h:Hotel)-[:has_reviewer]-(r:Reviewer {{name: 'Ryouta Sato'}})
    RETURN h

    stick strictly to the above output format
    """

    query_with_cypher_user_prompt = f"""Generate a cypher query to answer the user query.
    user_query = {user_query}"""
    
    query_response = openai_client.chat.completions.create(
        model = os.getenv("GPT_ENGINE"),
        messages = [
            {"role": "system", "content": query_with_cypher_system_prompt},
            {"role": "user", "content": query_with_cypher_user_prompt}
        ],
        temperature=0
    )    
    
    cypher_query_for_retrieval = query_response.choices[0].message.content
    
    print(cypher_query_for_retrieval)
    
    return cypher_query_for_retrieval

# Function to execute Neo4j query and return results
def execute_neo4j_query(cypher_query):
    url = _get_neo4j_uri()
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(url, auth=(neo4j_username, neo4j_password))
    
    with driver.session() as session:
        # Run the Cypher query
        result = session.run(cypher_query)
        
        # Extract and return results
        records = [record.data() for record in result]
        print(records)
        return records

# Function to create the knowledge graph in Neo4j
def create_knowledge_graph(hotel_reviews):
    """
    Create a knowledge graph in Neo4j from hotel reviews
    
    Args:
        hotel_reviews: List of hotel review texts
    """
    # Process each hotel review
    for review in hotel_reviews:
        # Identify relationships and nodes
        ontology = identify_relationships_and_nodes(review)
        
        # Generate Cypher query for node creation
        cypher_query = generate_cypher_for_node_creation(ontology)
    
    # Connect to Neo4j and create the graph
    url = _get_neo4j_uri()
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(url, auth=(neo4j_username, neo4j_password))
    
    with driver.session() as session:
        for cypher_query in node_creation_cypher_list:
            # Remove markdown code block markers
            clean_query = strip_markdown_code_blocks(cypher_query)
            try:
                session.run(clean_query)
                print(f"Executed: {clean_query}")
            except Exception as e:
                print(f"Error executing query: {e}")
                print(f"Failed query: {clean_query}")

# Function to perform RAG query
def rag_query(user_query):
    """
    Perform a RAG query using Neo4j and OpenAI
    
    Args:
        user_query: User's natural language query
    
    Returns:
        Answer to the user's query
    """
    # Generate Cypher query from user query
    cypher_query = query_neo4j_graph(user_query)
    
    # Clean the query
    clean_query = strip_markdown_code_blocks(cypher_query)
    
    # Execute the query
    results = execute_neo4j_query(clean_query)
    
    # Format the results for the LLM
    formatted_results = str(results)
    
    # Generate answer using OpenAI
    system_prompt = f"""You are an assistant that answers questions about hotels based on the provided information.
    Use only the information provided to answer the question. If you don't know the answer, say so.
    """
    
    user_prompt = f"""Based on the following information about hotels, answer this question: {user_query}
    
    Information: {formatted_results}
    """
    
    response = openai_client.chat.completions.create(
        model = os.getenv("GPT_ENGINE"),
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

# Sample hotel reviews
sample_hotel_reviews = [
    """The Creek Hotel in Dubai offers comfortable accommodations with amenities like a sofa, TV, and hot-shower bath. 
    It caters to both Businessmen and Tourists. Ryouta Sato, who recently stayed there, found the service excellent.""",
    
    """The Buckingham Hotel in New York City provides a cozy atmosphere with a sofa, TV, and hot-shower bath. 
    Issac Collett, a recent guest, praised the hotel's convenient location.""",
    
    """The Buckingham Hotel, located in London, UK, offers a unique British experience. 
    Akiko Kaneko mentioned the authentic English breakfast in her review.""",
    
    """The Kensington Hotel in Oslo received a positive review from Hsiung Chuang, 
    who appreciated the Scandinavian design elements.""",
    
    """The Deira Hotel in Beijing features 3 restaurants offering various cuisines. 
    Reina Inoue recommended trying the local specialties during her stay."""
]

# Create a Dash app for visualization
def create_visualization_app(neo4j_uri, neo4j_username, neo4j_password):
    """
    Create a Dash app for visualizing the knowledge graph
    """
    app = dash.Dash(__name__)
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(_get_neo4j_uri(), auth=(neo4j_username, neo4j_password))
    
    # Get all nodes and relationships
    with driver.session() as session:
        # Get hotels
        hotels_result = session.run("MATCH (h:Hotel) RETURN h.name as name")
        hotels = [record["name"] for record in hotels_result]
        
        # Get all relationships
        relationships_result = session.run("""
            MATCH (h:Hotel)-[r]->(n)
            RETURN h.name as hotel, type(r) as relation, labels(n)[0] as node_type, n.name as related_entity
        """)
        
        relationships_data = [
            {
                "hotel": record["hotel"],
                "relation": record["relation"],
                "node_type": record["node_type"],
                "related_entity": record["related_entity"]
            }
            for record in relationships_result
        ]
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(relationships_data)
    
    # Create network graph
    def create_network_graph():
        # Create nodes
        nodes = []
        node_colors = {
            "Hotel": "red",
            "Location": "blue",
            "Facilities": "green",
            "CustomerType": "purple",
            "Reviewer": "orange"
        }
        
        # Add hotel nodes
        for hotel in hotels:
            nodes.append({
                "id": hotel,
                "label": hotel,
                "color": node_colors["Hotel"]
            })
        
        # Add other nodes
        for _, row in df.iterrows():
            nodes.append({
                "id": row["related_entity"],
                "label": row["related_entity"],
                "color": node_colors[row["node_type"]]
            })
        
        # Create edges
        edges = []
        for _, row in df.iterrows():
            edges.append({
                "from": row["hotel"],
                "to": row["related_entity"],
                "label": row["relation"]
            })
        
        # Return network data
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    # Create app layout
    app.layout = html.Div([
        html.H1("Hotel Knowledge Graph Visualization"),
        
        html.Div([
            html.H3("Network Graph"),
            dcc.Graph(
                id="network-graph",
                figure={
                    "data": [
                        go.Scatter(
                            x=[1, 2, 3],
                            y=[1, 2, 3],
                            mode="markers",
                            marker={"size": 12}
                        )
                    ],
                    "layout": go.Layout(
                        title="Hotel Knowledge Graph",
                        showlegend=False,
                        hovermode="closest",
                        margin={"b": 40, "l": 40, "r": 40, "t": 40},
                        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                        yaxis={"showgrid": False, "zeroline": False, "showticklabels": False}
                    )
                }
            )
        ]),
        
        html.Div([
            html.H3("Query the Knowledge Graph"),
            dcc.Input(
                id="query-input",
                type="text",
                placeholder="Enter your query...",
                style={"width": "100%"}
            ),
            html.Button("Submit", id="submit-button"),
            html.Div(id="query-result")
        ])
    ])
    
    return app

# Main function to run the complete pipeline
def main():
    # Check if environment variables are set
    required_vars = ["GPT_ENGINE", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return
    
    print("Starting Graph RAG pipeline...")
    
    # Create knowledge graph
    print("\n1. Creating knowledge graph from hotel reviews...")
    create_knowledge_graph(sample_hotel_reviews)
    
    # Test RAG query
    print("\n2. Testing RAG query...")
    test_query = "which hotels are visited by businessmen?"
    answer = rag_query(test_query)
    print(f"\nQuery: {test_query}")
    print(f"Answer: {answer}")
    
    # Create visualization app
    print("\n3. Creating visualization app...")
    app = create_visualization_app(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
    
    # Run the app
    print("\nStarting Dash app for visualization. Open http://127.0.0.1:8050/ in your browser.")
    app.run_server(debug=True)

if __name__ == "__main__":
    main()
