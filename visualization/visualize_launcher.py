#!/usr/bin/env python3
"""Enhanced visualization launcher and management script.

⭐ IMPORTANT: This is a core component - DO NOT REMOVE
This file provides the main command-line interface for all enhanced visualization features.
It serves as the primary entry point for visualization tools.
"""

import subprocess
import sys
import os
import asyncio
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))
sys.path.insert(0, str(current_dir / "visualization"))

def show_usage():
    """Show usage information."""
    print("🎨 Enhanced Graph Visualization Tools")
    print("=" * 50)
    print("Usage: python visualize.py [option]")
    print()
    print("Options:")
    print("  full      - Complete visualization with all features")
    print("  compact   - Quick compact visualization")
    print("  demo      - Demo all visualization methods")
    print("  export    - Generate and export diagram files")
    print("  ascii     - ASCII art diagram only")
    print("  mermaid   - Mermaid diagram only")
    print("  test      - Run visualization test suite")
    print("  help      - Show this help message")
    print()
    print("Examples:")
    print("  python visualize.py full")
    print("  python visualize.py export")
    print("  python visualize.py demo")
    print()
    print("Generated Files:")
    print("  • visualization/graph_diagram.mmd")
    print("  • visualization/graph_structure.json")

async def run_full_visualization():
    """Run the complete enhanced visualization."""
    try:
        from azure_search_mcp.chain import AzureSearchChain
        from dynamic_graph_viz import GraphVisualizer
        
        print("🚀 Running full enhanced visualization...")
        chain = AzureSearchChain()
        visualizer = GraphVisualizer(chain)
        visualizer.visualize(export_files=True)
        await chain.close()
        print("✅ Full visualization completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def run_compact_visualization():
    """Run compact visualization."""
    try:
        from azure_search_mcp.chain import AzureSearchChain
        from dynamic_graph_viz import GraphVisualizer
        
        print("⚡ Running compact visualization...")
        chain = AzureSearchChain()
        visualizer = GraphVisualizer(chain)
        visualizer.visualize_compact()
        await chain.close()
        print("✅ Compact visualization completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def run_export_only():
    """Export diagrams without full display."""
    try:
        from azure_search_mcp.chain import AzureSearchChain
        from dynamic_graph_viz import GraphVisualizer
        
        print("📂 Exporting diagram files...")
        chain = AzureSearchChain()
        visualizer = GraphVisualizer(chain)
        
        mermaid_file = visualizer.export_mermaid_file()
        json_file = visualizer.export_json_graph()
        
        print(f"✅ Files exported:")
        print(f"  • {mermaid_file}")
        print(f"  • {json_file}")
        
        await chain.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def run_ascii_only():
    """Show ASCII diagram only."""
    try:
        from azure_search_mcp.chain import AzureSearchChain
        from dynamic_graph_viz import GraphVisualizer
        
        print("🎨 ASCII Diagram:")
        print("=" * 40)
        chain = AzureSearchChain()
        visualizer = GraphVisualizer(chain)
        visualizer.print_ascii_diagram()
        await chain.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def run_mermaid_only():
    """Show Mermaid diagram only."""
    try:
        from azure_search_mcp.chain import AzureSearchChain
        from dynamic_graph_viz import GraphVisualizer
        
        print("📈 Mermaid Diagram:")
        print("=" * 40)
        chain = AzureSearchChain()
        visualizer = GraphVisualizer(chain)
        visualizer.print_mermaid_diagram()
        await chain.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def run_demo():
    """Run the demo script."""
    try:
        demo_path = current_dir / "visualization" / "demo_enhanced_viz.py"
        if demo_path.exists():
            print("🎭 Running visualization demo...")
            result = subprocess.run([sys.executable, str(demo_path)], 
                                  capture_output=False, text=True)
            if result.returncode == 0:
                print("✅ Demo completed!")
            else:
                print("❌ Demo failed!")
        else:
            print("❌ Demo script not found!")
    except Exception as e:
        print(f"❌ Error running demo: {e}")

def run_test():
    """Run the test suite."""
    try:
        test_path = current_dir / "visualization" / "test_enhanced_visualization.py"
        if test_path.exists():
            print("🧪 Running visualization tests...")
            result = subprocess.run([sys.executable, str(test_path)], 
                                  capture_output=False, text=True)
            if result.returncode == 0:
                print("✅ Tests completed!")
            else:
                print("❌ Tests failed!")
        else:
            print("❌ Test script not found!")
    except Exception as e:
        print(f"❌ Error running tests: {e}")

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    option = sys.argv[1].lower()
    
    if option in ['help', '-h', '--help']:
        show_usage()
    elif option == 'full':
        await run_full_visualization()
    elif option == 'compact':
        await run_compact_visualization()
    elif option == 'export':
        await run_export_only()
    elif option == 'ascii':
        await run_ascii_only()
    elif option == 'mermaid':
        await run_mermaid_only()
    elif option == 'demo':
        run_demo()
    elif option == 'test':
        run_test()
    else:
        print(f"❌ Unknown option: {option}")
        print()
        show_usage()

if __name__ == "__main__":
    asyncio.run(main())
