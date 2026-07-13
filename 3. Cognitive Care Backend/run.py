import sys
import os
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ensure '3. Cognitive Care Backend' is first in sys.path and remove root path to avoid namespace conflicts
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

root_dir = os.path.dirname(current_dir)
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(root_dir)]

import uvicorn
from backend.app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
