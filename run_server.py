#!/usr/bin/env python
"""Local development server runner"""
import sys
import os

# Add necessary paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

# Now import and run the app
from server.app import app
import uvicorn

if __name__ == "__main__":
    print("Starting Cascade server")
    print("API running on http://localhost:8000")
    print("Docs at http://localhost:8000/docs")
    print("Press CTRL+C to stop\n")
    
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        reload=False,  # Disable reload to avoid import issues
        log_level="info"
    )
