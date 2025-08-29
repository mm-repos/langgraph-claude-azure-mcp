#!/usr/bin/env python3
"""Dynamic LangGraph visualization that automatically extracts and displays graph structure."""

print("Step 1: Starting module execution")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("Step 2: Basic imports complete")

import asyncio
from typing import Dict, List, Tuple, Set, Optional
import json

print("Step 3: Standard library imports complete")

from azure_search_mcp.chain import AzureSearchChain

print("Step 4: AzureSearchChain import complete")

# Try to import grandalf for advanced layouts
try:
    from grandalf.graphs import Vertex, Edge, Graph
    from grandalf.layouts import SugiyamaLayout
    from grandalf.routing import route_with_lines
    GRANDALF_AVAILABLE = True
except ImportError:
    GRANDALF_AVAILABLE = False


class GraphVisualizer:
    """Dynamic graph visualizer for LangGraph structures with enhanced layout algorithms."""
    
    def __init__(self, chain: AzureSearchChain):
        self.chain = chain
        self.graph_repr = chain.graph.get_graph()
        self.nodes = self.graph_repr.nodes
        self.edges = self.graph_repr.edges
        self.grandalf_graph = None
        self.layout = None
        if GRANDALF_AVAILABLE:
            self._build_grandalf_graph()
    
    def _build_grandalf_graph(self):
        """Build grandalf graph for layout computation."""
        try:
            # Create grandalf vertices
            vertices = {}
            for node_id in self.nodes.keys():
                v = Vertex(node_id)
                vertices[node_id] = v
            
            # Create grandalf edges
            grandalf_edges = []
            for edge in self.edges:
                if edge.source in vertices and edge.target in vertices:
                    e = Edge(vertices[edge.source], vertices[edge.target])
                    e.data = {'condition': edge.data if edge.conditional else None}
                    grandalf_edges.append(e)
            
            # Create graph and compute layout
            if vertices and grandalf_edges:
                self.grandalf_graph = Graph(list(vertices.values()), grandalf_edges)
                if self.grandalf_graph.C:  # Check if components exist
                    self.layout = SugiyamaLayout(self.grandalf_graph.C[0])
                    self.layout.init_all()
                    self.layout.draw()
                else:
                    self.layout = None
            else:
                self.grandalf_graph = None
                self.layout = None
        except Exception as e:
            print(f"Warning: Could not build grandalf layout: {e}")
            self.grandalf_graph = None
            self.layout = None
    
    def _get_user_nodes(self) -> List[str]:
        """Get all user-defined nodes (excluding __start__ and __end__)."""
        return [node_id for node_id in self.nodes.keys() 
                if node_id not in ['__start__', '__end__']]
    
    def _get_edges_by_source(self) -> Dict[str, List]:
        """Group edges by their source node."""
        edges_by_source = {}
        for edge in self.edges:
            if edge.source not in edges_by_source:
                edges_by_source[edge.source] = []
            edges_by_source[edge.source].append(edge)
        return edges_by_source
    
    def _get_conditional_edges(self) -> List:
        """Get all conditional edges."""
        return [edge for edge in self.edges if edge.conditional]
    
    def _get_entry_points(self) -> List[str]:
        """Get nodes that are entry points (targets of __start__)."""
        return [edge.target for edge in self.edges if edge.source == '__start__']
    
    def _get_exit_points(self) -> List[str]:
        """Get nodes that lead to __end__."""
        return [edge.source for edge in self.edges if edge.target == '__end__']
    
    def _build_execution_tree(self) -> Dict:
        """Build a tree structure representing execution flow."""
        edges_by_source = self._get_edges_by_source()
        entry_points = self._get_entry_points()
        
        def build_subtree(node: str, visited: Optional[Set[str]] = None) -> Dict:
            if visited is None:
                visited = set() 
            if node in visited:
                return {"node": node, "children": [], "cyclic": True}
            
            visited.add(node)
            children = []
            
            if node in edges_by_source:
                for edge in edges_by_source[node]:
                    if edge.target != '__end__':
                        child_tree = build_subtree(edge.target, visited.copy())
                        child_tree["condition"] = edge.data if edge.conditional else None
                        children.append(child_tree)
            
            return {"node": node, "children": children, "cyclic": False}
        
        if entry_points:
            return build_subtree(entry_points[0])
        return {}
    
    def print_header(self):
        """Print visualization header."""
        print("=" * 80)
        print("                    DYNAMIC LANGGRAPH VISUALIZATION")
        print("=" * 80)
        print()
    
    def print_nodes_summary(self):
        """Print summary of all nodes."""
        user_nodes = self._get_user_nodes()
        
        print("📊 NODES SUMMARY:")
        print("=" * 40)
        print(f"  Total nodes: {len(self.nodes)}")
        print(f"  User nodes: {len(user_nodes)}")
        print()
        
        print("📋 ALL NODES:")
        for node_id, node_data in self.nodes.items():
            if node_id == '__start__':
                print(f"  🟢 {node_id} (Entry)")
            elif node_id == '__end__':
                print(f"  🔴 {node_id} (Exit)")
            else:
                node_type = type(node_data.data).__name__ if hasattr(node_data, 'data') and node_data.data else "Unknown"
                print(f"  🔹 {node_id} ({node_type})")
        print()
    
    def print_edges_summary(self):
        """Print summary of all edges."""
        conditional_edges = self._get_conditional_edges()
        unconditional_edges = [edge for edge in self.edges if not edge.conditional]
        
        print("🔗 EDGES SUMMARY:")
        print("=" * 40)
        print(f"  Total edges: {len(self.edges)}")
        print(f"  Conditional edges: {len(conditional_edges)}")
        print(f"  Unconditional edges: {len(unconditional_edges)}")
        print()
        
        print("🔀 ROUTING TABLE:")
        edges_by_source = self._get_edges_by_source()
        for source, edges in sorted(edges_by_source.items()):
            if source == '__start__':
                print(f"  🟢 {source}")
            elif source in self._get_user_nodes():
                print(f"  📦 {source}")
            else:
                continue
                
            for edge in edges:
                target_display = "🔴 END" if edge.target == '__end__' else edge.target
                if edge.conditional and edge.data:
                    print(f"      ├─[{edge.data}]─► {target_display}")
                else:
                    print(f"      └──────────► {target_display}")
        print()
    
    def print_execution_flow(self):
        """Print dynamic execution flow tree."""
        print("🌊 EXECUTION FLOW:")
        print("=" * 40)
        
        tree = self._build_execution_tree()
        
        def print_tree(node_data: Dict, prefix: str = "", is_last: bool = True):
            if not node_data:
                return
                
            node = node_data["node"]
            children = node_data.get("children", [])
            condition = node_data.get("condition")
            
            # Determine node symbol
            if node == '__start__':
                symbol = "🟢"
            elif node in self._get_exit_points():
                symbol = "🎯"
            else:
                symbol = "📦"
            
            # Print current node
            connector = "└── " if is_last else "├── "
            condition_text = f"[{condition}] " if condition else ""
            print(f"{prefix}{connector}{condition_text}{symbol} {node}")
            
            # Print children
            if children:
                child_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(children):
                    is_last_child = (i == len(children) - 1)
                    print_tree(child, child_prefix, is_last_child)
        
        print_tree(tree)
        print()
    
    def print_state_flow(self):
        """Print state transformation flow."""
        print("📋 STATE TRANSFORMATION:")
        print("=" * 40)
        
        # Get the SearchState structure dynamically
        state_class = None
        for name, obj in vars(sys.modules[self.chain.__module__]).items():
            if hasattr(obj, '__annotations__') and 'query' in getattr(obj, '__annotations__', {}):
                state_class = obj
                break
        
        if state_class and hasattr(state_class, '__annotations__'):
            print("  State fields:")
            for field, field_type in state_class.__annotations__.items():
                type_name = getattr(field_type, '__name__', str(field_type))
                print(f"    • {field}: {type_name}")
        else:
            print("  State structure not found dynamically")
        print()
    
    def print_mermaid_diagram(self):
        """Print enhanced Mermaid diagram code with better styling."""
        print("📈 MERMAID DIAGRAM:")
        print("=" * 40)
        print("```mermaid")
        print("graph TD")
        
        # Add nodes with better styling
        for node_id in self.nodes.keys():
            if node_id == '__start__':
                print(f"    {node_id}([\"{node_id}\"])")
            elif node_id == '__end__':
                print(f"    {node_id}([\"END\"])")
            else:
                # Clean node name for display
                clean_name = node_id.replace('_', ' ').title()
                print(f"    {node_id}[\"{clean_name}\"]")
        
        print()
        
        # Add edges with conditions
        for edge in self.edges:
            source = edge.source
            target = edge.target
            
            if edge.conditional and edge.data:
                condition = str(edge.data).replace('"', "'")
                print(f"    {source} -->|{condition}| {target}")
            else:
                print(f"    {source} --> {target}")
        
        print()
        
        # Enhanced styling
        print("    %% Styling")
        print("    style __start__ fill:#e8f5e8,stroke:#4caf50,stroke-width:2px")
        print("    style __end__ fill:#ffebee,stroke:#f44336,stroke-width:2px")
        
        # Style user nodes based on their function
        user_nodes = self._get_user_nodes()
        for node in user_nodes:
            if 'validate' in node.lower():
                print(f"    style {node} fill:#fff3e0,stroke:#ff9800,stroke-width:2px")
            elif 'search' in node.lower():
                print(f"    style {node} fill:#e3f2fd,stroke:#2196f3,stroke-width:2px")
            elif 'prepare' in node.lower() or 'context' in node.lower():
                print(f"    style {node} fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px")
            elif 'format' in node.lower() or 'structure' in node.lower():
                print(f"    style {node} fill:#e0f2f1,stroke:#009688,stroke-width:2px")
            elif 'analyze' in node.lower() or 'summarize' in node.lower():
                print(f"    style {node} fill:#fce4ec,stroke:#e91e63,stroke-width:2px")
            elif 'error' in node.lower():
                print(f"    style {node} fill:#ffebee,stroke:#f44336,stroke-width:2px")
            else:
                print(f"    style {node} fill:#f5f5f5,stroke:#757575,stroke-width:2px")
        
        print("```")
        print()
        
    def print_ascii_diagram(self):
        """Print ASCII art diagram using grandalf layout."""
        print("🎨 ASCII DIAGRAM:")
        print("=" * 40)
        
        if not self.layout or not self.grandalf_graph or not hasattr(self.grandalf_graph, 'C') or not self.grandalf_graph.C:
            print("  Layout not available, using fallback ASCII diagram")
            self._print_fallback_ascii()
            return
            
        # Get layout dimensions
        vertices = self.grandalf_graph.C[0].sV
        min_x = min(v.view.xy[0] for v in vertices)
        max_x = max(v.view.xy[0] for v in vertices)
        min_y = min(v.view.xy[1] for v in vertices)
        max_y = max(v.view.xy[1] for v in vertices)
        
        # Scale to reasonable ASCII size
        width = min(80, max(40, int(max_x - min_x) + 20))
        height = min(30, max(15, int(max_y - min_y) + 10))
        
        # Create ASCII grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Node positions mapping
        node_positions = {}
        
        # Place nodes
        for vertex in vertices:
            node_id = vertex.data
            x = int((vertex.view.xy[0] - min_x) / (max_x - min_x) * (width - 10)) + 5
            y = int((vertex.view.xy[1] - min_y) / (max_y - min_y) * (height - 5)) + 2
            
            # Ensure bounds
            x = max(1, min(width - 8, x))
            y = max(1, min(height - 2, y))
            
            node_positions[node_id] = (x, y)
            
            # Place node symbol and text
            if node_id == '__start__':
                symbol = '●'
            elif node_id == '__end__':
                symbol = '◉'
            else:
                symbol = '□'
            
            # Place symbol
            if y < height and x < width:
                grid[y][x] = symbol
                
            # Place shortened node name
            display_name = node_id[:6] if len(node_id) > 6 else node_id
            if node_id.startswith('__'):
                display_name = node_id[2:5].upper()
                
            for i, char in enumerate(display_name):
                if x + i + 1 < width and y < height:
                    grid[y][x + i + 1] = char
        
        # Draw edges
        for edge in self.edges:
            if edge.source in node_positions and edge.target in node_positions:
                start_pos = node_positions[edge.source]
                end_pos = node_positions[edge.target]
                
                # Simple line drawing
                self._draw_ascii_line(grid, start_pos, end_pos, width, height)
        
        # Print the ASCII diagram
        print()
        for row in grid:
            print('  ' + ''.join(row))
        print()
        
        # Print legend
        print("  Legend:")
        print("    ● = START node")
        print("    ◉ = END node") 
        print("    □ = Process node")
        print("    | - \\ / = Connections")
        print()
    
    def _print_fallback_ascii(self):
        """Print a simple fallback ASCII diagram when grandalf is not available."""
        print()
        print("  Simple Flow Diagram:")
        print("  " + "─" * 50)
        
        user_nodes = self._get_user_nodes()
        entry_points = self._get_entry_points()
        exit_points = self._get_exit_points()
        
        # Start node
        print("    ●  START")
        print("    │")
        
        # Entry points
        for entry in entry_points:
            print(f"    ├─► □  {entry}")
            
        # Other user nodes
        remaining_nodes = [n for n in user_nodes if n not in entry_points and n not in exit_points]
        for node in remaining_nodes:
            print(f"    ├─► □  {node}")
            
        # Exit points
        for exit_node in exit_points:
            if exit_node not in entry_points:
                print(f"    ├─► □  {exit_node}")
        
        print("    │")
        print("    ◉  END")
        print()
    
    def _draw_ascii_line(self, grid, start, end, width, height):
        """Draw a simple ASCII line between two points."""
        x1, y1 = start
        x2, y2 = end
        
        # Skip if positions are invalid
        if not all(0 <= coord < height for coord in [y1, y2]):
            return
        if not all(0 <= coord < width for coord in [x1, x2]):
            return
            
        # Simple horizontal/vertical line drawing
        if abs(x2 - x1) > abs(y2 - y1):  # More horizontal
            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
            for x in range(x1 + 1, x2):
                if 0 <= x < width and 0 <= y1 < height:
                    if grid[y1][x] == ' ':
                        grid[y1][x] = '-'
        else:  # More vertical
            if y1 > y2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
            for y in range(y1 + 1, y2):
                if 0 <= x1 < width and 0 <= y < height:
                    if grid[y][x1] == ' ':
                        grid[y][x1] = '|'
    
    def print_layout_analysis(self):
        """Print analysis of the graph layout computed by grandalf."""
        print("🔬 LAYOUT ANALYSIS:")
        print("=" * 40)
        
        if not self.layout or not self.grandalf_graph or not hasattr(self.grandalf_graph, 'C') or not self.grandalf_graph.C:
            print("  No grandalf layout computed")
            print("  Using basic graph analysis:")
            
            total_nodes = len(self.nodes)
            total_edges = len(self.edges)
            entry_points = self._get_entry_points()
            exit_points = self._get_exit_points()
            
            print(f"    Total nodes: {total_nodes}")
            print(f"    Total edges: {total_edges}")
            print(f"    Entry points: {len(entry_points)} - {', '.join(entry_points)}")
            print(f"    Exit points: {len(exit_points)} - {', '.join(exit_points)}")
            print(f"    Graph density: {total_edges / (total_nodes * total_nodes) if total_nodes > 0 else 0:.3f}")
            return
            
        # Analyze layout properties
        vertices = self.grandalf_graph.C[0].sV
        total_nodes = len(vertices)
        
        # Calculate layout metrics
        positions = [(v.view.xy[0], v.view.xy[1]) for v in vertices]
        if positions:
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
            
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            
            print(f"  Total nodes: {total_nodes}")
            print(f"  Layout dimensions: {width:.1f} x {height:.1f}")
            print(f"  Layout density: {total_nodes / (width * height + 1):.3f}")
            
            # Find layers
            layers = {}
            for v in vertices:
                layer = int(v.view.xy[1])
                if layer not in layers:
                    layers[layer] = []
                layers[layer].append(v.data)
            
            print(f"  Layout layers: {len(layers)}")
            for layer, nodes in sorted(layers.items()):
                node_names = [n[:8] for n in nodes]
                print(f"    Layer {layer}: {', '.join(node_names)}")
        
        print()
    
    def export_mermaid_file(self, filename: str = "graph_diagram.mmd"):
        """Export Mermaid diagram to file."""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            f.write("graph TD\n\n")
            
            # Add nodes
            for node_id in self.nodes.keys():
                if node_id == '__start__':
                    f.write(f"    {node_id}([\"{node_id}\"])\n")
                elif node_id == '__end__':
                    f.write(f"    {node_id}([\"END\"])\n")
                else:
                    clean_name = node_id.replace('_', ' ').title()
                    f.write(f"    {node_id}[\"{clean_name}\"]\n")
            
            f.write("\n")
            
            # Add edges
            for edge in self.edges:
                source = edge.source
                target = edge.target
                
                if edge.conditional and edge.data:
                    condition = str(edge.data).replace('"', "'")
                    f.write(f"    {source} -->|{condition}| {target}\n")
                else:
                    f.write(f"    {source} --> {target}\n")
            
            f.write("\n")
            
            # Enhanced styling
            f.write("    %% Styling\n")
            f.write("    style __start__ fill:#e8f5e8,stroke:#4caf50,stroke-width:2px\n")
            f.write("    style __end__ fill:#ffebee,stroke:#f44336,stroke-width:2px\n")
            
            # Style user nodes
            user_nodes = self._get_user_nodes()
            for node in user_nodes:
                if 'validate' in node.lower():
                    f.write(f"    style {node} fill:#fff3e0,stroke:#ff9800,stroke-width:2px\n")
                elif 'search' in node.lower():
                    f.write(f"    style {node} fill:#e3f2fd,stroke:#2196f3,stroke-width:2px\n")
                elif 'prepare' in node.lower() or 'context' in node.lower():
                    f.write(f"    style {node} fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px\n")
                elif 'format' in node.lower() or 'structure' in node.lower():
                    f.write(f"    style {node} fill:#e0f2f1,stroke:#009688,stroke-width:2px\n")
                elif 'analyze' in node.lower() or 'summarize' in node.lower():
                    f.write(f"    style {node} fill:#fce4ec,stroke:#e91e63,stroke-width:2px\n")
                elif 'error' in node.lower():
                    f.write(f"    style {node} fill:#ffebee,stroke:#f44336,stroke-width:2px\n")
                else:
                    f.write(f"    style {node} fill:#f5f5f5,stroke:#757575,stroke-width:2px\n")
        
        print(f"  📁 Mermaid diagram exported to: {filepath}")
        return filepath
    
    def export_json_graph(self, filename: str = "graph_structure.json"):
        """Export graph structure as JSON."""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        # Build JSON structure
        graph_data = {
            "metadata": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "entry_points": self._get_entry_points(),
                "exit_points": self._get_exit_points(),
                "generated_by": "GraphVisualizer with grandalf"
            },
            "nodes": [],
            "edges": [],
            "layout": {}
        }
        
        # Add nodes
        for node_id, node_data in self.nodes.items():
            node_info = {
                "id": node_id,
                "type": "start" if node_id == "__start__" else "end" if node_id == "__end__" else "process",
                "data_type": type(node_data.data).__name__ if hasattr(node_data, 'data') and node_data.data else "Unknown"
            }
            graph_data["nodes"].append(node_info)
        
        # Add edges
        for edge in self.edges:
            edge_info = {
                "source": edge.source,
                "target": edge.target,
                "conditional": edge.conditional,
                "condition": edge.data if edge.conditional else None
            }
            graph_data["edges"].append(edge_info)
        
        # Add layout information if available
        if self.layout and self.grandalf_graph and hasattr(self.grandalf_graph, 'C') and self.grandalf_graph.C:
            for vertex in self.grandalf_graph.C[0].sV:
                graph_data["layout"][vertex.data] = {
                    "x": vertex.view.xy[0],
                    "y": vertex.view.xy[1]
                }
        
        with open(filepath, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        print(f"  📁 JSON graph data exported to: {filepath}")
        return filepath
    
    def visualize(self, export_files: bool = False):
        """Print complete visualization with enhanced features."""
        self.print_header()
        self.print_nodes_summary()
        self.print_edges_summary()
        self.print_execution_flow()
        self.print_state_flow()
        self.print_layout_analysis()
        self.print_mermaid_diagram()
        self.print_ascii_diagram()
        
        if export_files:
            print("📂 EXPORTING FILES:")
            print("=" * 40)
            mermaid_file = self.export_mermaid_file()
            json_file = self.export_json_graph()
            print()
            
    def visualize_compact(self):
        """Print a compact version of the visualization."""
        print("🎯 COMPACT GRAPH VISUALIZATION")
        print("=" * 50)
        
        user_nodes = self._get_user_nodes()
        entry_points = self._get_entry_points()
        exit_points = self._get_exit_points()
        
        print(f"📊 {len(self.nodes)} nodes, {len(self.edges)} edges")
        print(f"🟢 Entry: {', '.join(entry_points)}")
        print(f"🔴 Exit: {', '.join(exit_points)}")
        print()
        
        # Compact flow
        print("🌊 Flow: START", end="")
        for node in user_nodes:
            print(f" → {node[:8]}", end="")
        print(" → END")
        print()
        
        # Quick ASCII
        self._print_fallback_ascii()


async def main():
    """Main function to run the enhanced dynamic visualization."""
    print("🚀 Initializing enhanced chain visualization with grandalf...")
    
    try:
        chain = AzureSearchChain()
        visualizer = GraphVisualizer(chain)
        
        # Full visualization
        print("\n" + "="*80)
        print("FULL VISUALIZATION")
        print("="*80)
        visualizer.visualize(export_files=True)
        
        # Compact visualization
        print("\n" + "="*80)
        print("COMPACT VISUALIZATION")
        print("="*80)
        visualizer.visualize_compact()
        
        await chain.close()
        
    except Exception as e:
        print(f"Error during visualization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
