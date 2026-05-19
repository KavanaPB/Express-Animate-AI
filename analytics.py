import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import json
import os
import io

class AnimationAnalytics:
    def __init__(self, data_file="animation_data.json"):
        self.data_file = data_file
        self.ensure_data_file()
        
    def ensure_data_file(self):
        if not os.path.exists(self.data_file):
            initial_data = {"animations": []}
            with open(self.data_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def log_animation(self, prompt, script_length, has_avatar, generation_time, services_used, success=True):
        with open(self.data_file, 'r') as f:
            data = json.load(f)
        
        animation_data = {
            "id": len(data["animations"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "script_length": script_length,
            "has_avatar": has_avatar,
            "generation_time": generation_time,
            "services_used": services_used,
            "success": success,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        data["animations"].append(animation_data)
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

def add_analytics_routes(app, analytics):
    @app.route('/analytics')
    def analytics_dashboard():
        return "Analytics Dashboard - Coming Soon"