#!/usr/bin/env python3
"""
Research File Collector for MindSearch
Saves all streaming output as it gets collected for analysis
"""

import json
import requests
import time
from datetime import datetime
import os
from pathlib import Path

class ResearchCollector:
    def __init__(self, base_url="http://localhost:8005", output_dir="research_outputs"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def collect_research(self, query, session_name=None):
        """
        Collect all streaming output from a research query
        """
        if session_name is None:
            session_name = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create session directory
        session_dir = self.output_dir / session_name
        session_dir.mkdir(exist_ok=True)
        
        print(f"🔬 Starting research collection: {session_name}")
        print(f"📁 Output directory: {session_dir}")
        print(f"❓ Query: {query}")
        print("=" * 80)
        
        # Files to save different aspects
        raw_stream_file = session_dir / "raw_stream.jsonl"
        formatted_output_file = session_dir / "formatted_output.txt"
        graph_evolution_file = session_dir / "graph_evolution.json"
        metadata_file = session_dir / "metadata.json"
        
        # Metadata
        metadata = {
            "session_name": session_name,
            "query": query,
            "start_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_responses": 0,
            "unique_nodes": [],
            "final_graph": {},
            "references": {}
        }
        
        # Collections
        all_responses = []
        graph_states = []
        current_thought = ""
        
        try:
            # Make the streaming request
            response = requests.post(
                f"{self.base_url}/solve",
                json={"inputs": query},
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            print("🌊 Streaming started...")
            
            with open(raw_stream_file, 'w') as raw_file, \
                 open(formatted_output_file, 'w') as formatted_file:
                
                # Write headers
                formatted_file.write(f"Research Session: {session_name}\n")
                formatted_file.write(f"Query: {query}\n")
                formatted_file.write(f"Started: {metadata['start_time']}\n")
                formatted_file.write("=" * 80 + "\n\n")
                
                for line in response.iter_lines():
                    if line:
                        try:
                            # Parse the streaming response
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data: '):
                                json_str = line_str[6:]  # Remove 'data: ' prefix
                                if json_str.strip() == '[DONE]':
                                    break
                                
                                data = json.loads(json_str)
                                all_responses.append(data)
                                metadata["total_responses"] += 1
                                
                                # Save raw response
                                raw_file.write(json.dumps(data) + "\n")
                                raw_file.flush()
                                
                                # Extract useful info
                                if 'response' in data and data['response']:
                                    resp = data['response']
                                    formatted_data = resp.get('formatted', {})
                                    
                                    # Track graph evolution
                                    if 'adjacency_list' in formatted_data:
                                        adj_list = formatted_data['adjacency_list']
                                        if adj_list and adj_list != metadata.get("final_graph"):
                                            metadata["final_graph"] = adj_list
                                            metadata["unique_nodes"].update(adj_list.keys())
                                            graph_states.append({
                                                "timestamp": datetime.now().isoformat(),
                                                "response_count": metadata["total_responses"],
                                                "adjacency_list": adj_list
                                            })
                                    
                                    # Track references
                                    if 'ref2url' in formatted_data:
                                        ref2url = formatted_data['ref2url']
                                        if ref2url:
                                            metadata["references"].update(ref2url)
                                    
                                    # Build thought stream
                                    if 'thought' in formatted_data:
                                        new_thought = formatted_data['thought']
                                        if new_thought and new_thought != current_thought:
                                            current_thought = new_thought
                                            
                                            # Write formatted output
                                            formatted_file.write(f"[{metadata['total_responses']:04d}] ")
                                            if 'tool_type' in formatted_data and formatted_data['tool_type']:
                                                formatted_file.write(f"[{formatted_data['tool_type']}] ")
                                            formatted_file.write(f"{new_thought}\n")
                                            formatted_file.flush()
                                            
                                            # Print progress
                                            if metadata["total_responses"] % 50 == 0:
                                                print(f"📊 Collected {metadata['total_responses']} responses...")
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON decode error: {e}")
                            continue
                        except Exception as e:
                            print(f"⚠️  Processing error: {e}")
                            continue
            
            # Finalize metadata
            metadata["end_time"] = datetime.now().isoformat()
            metadata["unique_nodes"] = list(metadata["unique_nodes"])
            
            # Save graph evolution
            with open(graph_evolution_file, 'w') as graph_file:
                json.dump(graph_states, graph_file, indent=2)
            
            # Save metadata
            with open(metadata_file, 'w') as meta_file:
                json.dump(metadata, meta_file, indent=2)
            
            print("\n" + "=" * 80)
            print(f"✅ Research collection complete!")
            print(f"📊 Total responses: {metadata['total_responses']}")
            print(f"🔗 Unique nodes: {len(metadata['unique_nodes'])}")
            print(f"📚 References found: {len(metadata['references'])}")
            print(f"📁 Files saved in: {session_dir}")
            
            return {
                "session_dir": str(session_dir),
                "metadata": metadata,
                "files": {
                    "raw_stream": str(raw_stream_file),
                    "formatted_output": str(formatted_output_file),
                    "graph_evolution": str(graph_evolution_file),
                    "metadata": str(metadata_file)
                }
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

def main():
    """Example usage"""
    collector = ResearchCollector()
    
    # Example research queries
    queries = [
        "What are the latest developments in AI agent architectures and multi-agent systems in 2024?",
        "Compare the performance and capabilities of different vector databases for RAG applications",
        "What are the current challenges and solutions in agentic workflow orchestration?"
    ]
    
    print("🔬 Research Collector Ready!")
    print("Available example queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    choice = input("\nEnter query number (1-3) or type your own query: ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(queries):
        query = queries[int(choice) - 1]
    else:
        query = choice
    
    if query:
        result = collector.collect_research(query)
        if result:
            print(f"\n🎉 Research saved! Check: {result['session_dir']}")
        else:
            print("\n❌ Research collection failed")

if __name__ == "__main__":
    main()
