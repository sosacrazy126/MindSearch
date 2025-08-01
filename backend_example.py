import json

import requests

# Define the backend URL
url = "http://localhost:8005/solve"
headers = {"Content-Type": "application/json"}


# Function to send a query to the backend and get the response
def get_response(query):
    # Prepare the input data
    data = {"inputs": query}

    # Send the request to the backend
    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=20, stream=True)

    # Process the streaming response
    for chunk in response.iter_lines(chunk_size=8192, decode_unicode=False, delimiter=b"\n"):
        if chunk:
            decoded = chunk.decode("utf-8")
            if decoded == "\r":
                continue
            if decoded[:6] == "data: ":
                decoded = decoded[6:]
            elif decoded.startswith(": ping - "):
                continue
            response_data = json.loads(decoded)
            logger.debug(f"Raw response: {response_data}")

            agent_return = response_data.get("response", {})
            node_name = response_data.get("current_node", "unknown")

            # Handle different response formats
            if isinstance(agent_return, dict):
                content = agent_return.get("content", "")
                formatted = agent_return.get("formatted", {})
                print(f"Node: {node_name}")
                print(f"Content: {content}")
                if formatted and isinstance(formatted, dict):
                    ref2url = formatted.get("ref2url", {})
                    if ref2url:
                        print(f"References: {ref2url}")
                print("---")


# Example usage
if __name__ == "__main__":
    query = """Compare the current economic performance of the United States and China in 2024.
    I need information about:
    1. GDP growth rates for both countries
    2. Current inflation rates
    3. Unemployment statistics
    4. Recent trade relationship developments
    5. Stock market performance (S&P 500 vs Shanghai Composite)
    Please provide recent data and analysis of how these factors interact."""
    get_response(query)
