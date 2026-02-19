#!/usr/bin/env python
"""Simple script to run the Dealink API server"""
import uvicorn

if __name__ == "__main__":
    print("Starting Dealink API server...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("API docs at: http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )



