#!/usr/bin/env python3
"""
Research Analysis Tool
Analyze collected research data from MindSearch sessions
"""

import json
import os
from pathlib import Path
from datetime import datetime

class ResearchAnalyzer:
    def __init__(self, research_dir="research_outputs"):
        self.research_dir = Path(research_dir)
    
    def list_sessions(self):
        """List all available research sessions"""
        sessions = []
        if self.research_dir.exists():
            for session_path in self.research_dir.iterdir():
                if session_path.is_dir():
                    metadata_file = session_path / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        sessions.append({
                            "name": session_path.name,
                            "path": session_path,
                            "metadata": metadata
                        })
        return sorted(sessions, key=lambda x: x["metadata"].get("start_time", ""))
    
    def analyze_session(self, session_name):
        """Analyze a specific research session"""
        session_path = self.research_dir / session_name
        if not session_path.exists():
            print(f"❌ Session not found: {session_name}")
            return None
        
        # Load metadata
        metadata_file = session_path / "metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # Load graph evolution
        graph_file = session_path / "graph_evolution.json"
        graph_evolution = []
        if graph_file.exists():
            with open(graph_file) as f:
                graph_evolution = json.load(f)
        
        print(f"📊 Analysis for: {session_name}")
        print("=" * 60)
        print(f"Query: {metadata['query']}")
        print(f"Duration: {metadata.get('start_time', 'Unknown')} to {metadata.get('end_time', 'Unknown')}")
        print(f"Total responses: {metadata['total_responses']}")
        print(f"Unique nodes: {len(metadata['unique_nodes'])}")
        print(f"References: {len(metadata.get('references', {}))}")
        
        if metadata['unique_nodes']:
            print(f"\nNodes created: {', '.join(metadata['unique_nodes'])}")
        
        if metadata.get('references'):
            print(f"\nReferences found:")
            for ref, url in metadata['references'].items():
                print(f"  [{ref}] {url}")
        
        # Graph evolution analysis
        if graph_evolution:
            print(f"\nGraph Evolution ({len(graph_evolution)} states):")
            for i, state in enumerate(graph_evolution):
                nodes = list(state['adjacency_list'].keys())
                print(f"  State {i+1}: {len(nodes)} nodes - {', '.join(nodes)}")
        
        return {
            "metadata": metadata,
            "graph_evolution": graph_evolution,
            "session_path": session_path
        }
    
    def visualize_graph(self, session_name, save_plot=True):
        """Create a text-based visualization of the final graph structure"""
        analysis = self.analyze_session(session_name)
        if not analysis:
            return

        final_graph = analysis["metadata"].get("final_graph", {})
        if not final_graph:
            print("❌ No graph data to visualize")
            return

        print(f"\n📊 Graph Structure for {session_name}:")
        print("=" * 50)

        # Simple text visualization
        for node, connections in final_graph.items():
            print(f"📍 {node}")
            if connections:
                for conn in connections:
                    print(f"  └─→ {conn}")
            else:
                print(f"  └─→ (no connections)")
            print()

        # Save as text file
        if save_plot:
            graph_file = analysis["session_path"] / "graph_structure.txt"
            with open(graph_file, 'w') as f:
                f.write(f"Graph Structure for {session_name}\n")
                f.write("=" * 50 + "\n\n")
                for node, connections in final_graph.items():
                    f.write(f"{node}:\n")
                    if connections:
                        for conn in connections:
                            f.write(f"  -> {conn}\n")
                    else:
                        f.write(f"  -> (no connections)\n")
                    f.write("\n")
            print(f"📊 Graph structure saved: {graph_file}")
    
    def export_for_training(self, session_name, output_file=None):
        """Export session data in a format suitable for training/analysis"""
        analysis = self.analyze_session(session_name)
        if not analysis:
            return
        
        session_path = analysis["session_path"]
        
        # Load raw stream data
        raw_file = session_path / "raw_stream.jsonl"
        raw_responses = []
        if raw_file.exists():
            with open(raw_file) as f:
                for line in f:
                    raw_responses.append(json.loads(line.strip()))
        
        # Create training-friendly format
        training_data = {
            "query": analysis["metadata"]["query"],
            "session_id": session_name,
            "metadata": analysis["metadata"],
            "graph_evolution": analysis["graph_evolution"],
            "response_stream": raw_responses,
            "final_graph": analysis["metadata"].get("final_graph", {}),
            "node_sequence": [state["adjacency_list"] for state in analysis["graph_evolution"]],
            "reasoning_steps": []
        }
        
        # Extract reasoning steps
        current_thought = ""
        for response in raw_responses:
            if 'response' in response and response['response']:
                formatted = response['response'].get('formatted', {})
                if 'thought' in formatted:
                    thought = formatted['thought']
                    if thought and thought != current_thought:
                        training_data["reasoning_steps"].append({
                            "step": len(training_data["reasoning_steps"]) + 1,
                            "thought": thought,
                            "tool_type": formatted.get('tool_type'),
                            "graph_state": formatted.get('adjacency_list', {})
                        })
                        current_thought = thought
        
        # Save training data
        if output_file is None:
            output_file = session_path / "training_data.json"
        
        with open(output_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        print(f"📚 Training data exported: {output_file}")
        print(f"   - {len(training_data['reasoning_steps'])} reasoning steps")
        print(f"   - {len(training_data['response_stream'])} raw responses")
        print(f"   - {len(training_data['graph_evolution'])} graph states")
        
        return training_data

def main():
    analyzer = ResearchAnalyzer()
    
    sessions = analyzer.list_sessions()
    if not sessions:
        print("❌ No research sessions found. Run research_collector.py first!")
        return
    
    print("📊 Available Research Sessions:")
    print("=" * 50)
    for i, session in enumerate(sessions, 1):
        meta = session["metadata"]
        print(f"{i}. {session['name']}")
        print(f"   Query: {meta['query'][:60]}...")
        print(f"   Responses: {meta['total_responses']}, Nodes: {len(meta['unique_nodes'])}")
        print()
    
    choice = input("Enter session number to analyze: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(sessions):
        session = sessions[int(choice) - 1]
        
        print(f"\n🔍 Analyzing: {session['name']}")
        analyzer.analyze_session(session['name'])
        
        # Ask for additional actions
        print("\nAdditional actions:")
        print("1. Show graph structure")
        print("2. Export training data")
        print("3. Both")

        action = input("Choose action (1-3, or Enter to skip): ").strip()

        if action in ['1', '3']:
            analyzer.visualize_graph(session['name'])

        if action in ['2', '3']:
            analyzer.export_for_training(session['name'])

if __name__ == "__main__":
    main()
