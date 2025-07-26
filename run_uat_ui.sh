#!/bin/bash
"""
UAT Testing UI Launcher
Quick script to launch the Streamlit UAT interface
"""

echo "🚀 Starting SEC Graph Agent UAT Testing UI..."
echo "📍 Open your browser to: http://localhost:8501"
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit
fi

# Launch the UI
streamlit run uat_testing_ui.py --server.port 8501 --server.headless false