"""
🌐 WEB-BASED DASHBOARD
Interactive browser-based interface for presentations
Runs at http://localhost:8501
"""

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
import sys
import time
from threading import Thread
from ultralytics import YOLO

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.traffic_logic import TrafficController
from src.config import VIDEO_SOURCES, TrafficConfig

# Page config
st.set_page_config(
    page_title="AI Traffic Control System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3em;
        color: #00d4ff;
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00d4ff;
    }
    .status-green {
        color: #00ff00;
        font-weight: bold;
        font-size: 1.5em;
    }
    .status-yellow {
        color: #ffff00;
        font-weight: bold;
        font-size: 1.5em;
    }
    .status-red {
        color: #ff0000;
        font-weight: bold;
        font-size: 1.5em;
    }
    .explanation-box {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #00d4ff;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'controller' not in st.session_state:
    st.session_state.controller = TrafficController(
        ticks_per_second=10,
        lane_names=TrafficConfig.LANE_NAMES
    )
    st.session_state.model = YOLO('yolov8n.pt')
    st.session_state.vehicle_counts = {lane: 0 for lane in TrafficConfig.LANE_NAMES}


def detect_vehicles(video_path):
    """Detect vehicles in video frame."""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if ret:
        results = st.session_state.model.predict(frame, conf=0.4, verbose=False, classes=[2, 3, 5, 7])
        count = len(results[0].boxes)
        annotated = results[0].plot()
        return annotated, count
    return None, 0


# Main header
st.markdown('<h1 class="main-header">🚦 AI-Powered Traffic Control System</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ System Controls")

    run_simulation = st.checkbox("Run Simulation", value=True)
    show_explanations = st.checkbox("Show Detailed Explanations", value=True)

    st.markdown("---")
    st.header("📊 Quick Stats")

    stats = st.session_state.controller.get_statistics()
    st.metric("Total Cycles", stats['total_cycles'])
    st.metric("Vehicles Served", stats['total_vehicles_served'])
    st.metric("Runtime", f"{stats['runtime_seconds']:.0f}s")

    st.markdown("---")
    st.header("🎓 About")
    st.write("""
    **Algorithm:** Max Pressure  
    **Base Green:** 10s  
    **Max Green:** 45s  
    **Time per Vehicle:** 0.5s  

    This system uses AI to optimize traffic flow by:
    1. Detecting vehicles with YOLO
    2. Counting vehicles per lane
    3. Calculating optimal green time
    4. Selecting most congested lane
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📹 Live Camera Feeds")

    # 2x2 grid of lanes
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    lanes_cols = [row1_col1, row1_col2, row2_col1, row2_col2]

    for idx, (lane_name, video_path) in enumerate(VIDEO_SOURCES.items()):
        with lanes_cols[idx]:
            st.subheader(lane_name)

            if isinstance(video_path, str) and Path(video_path).exists():
                frame, count = detect_vehicles(video_path)
                st.session_state.vehicle_counts[lane_name] = count

                if frame is not None:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st.image(frame_rgb, use_column_width=True)
                    st.metric("Vehicles", count)
            else:
                st.warning("Video not found")

with col2:
    st.header("🤖 AI Decision Panel")

    # Update controller
    if run_simulation:
        counts_list = [st.session_state.vehicle_counts[lane] for lane in TrafficConfig.LANE_NAMES]
        st.session_state.controller.update_vehicle_counts(counts_list)
        st.session_state.controller.update_tick()

    # Get current state
    state_info = st.session_state.controller.get_current_state_info()
    current_lane = state_info['lane_names'][state_info['green_lane_index']]
    state = state_info['current_state']
    timer = state_info['timer_sec']

    # Display current signal
    st.markdown("### 🚦 Current Signal")

    if state == "GREEN":
        st.markdown(f'<p class="status-green">🟢 {current_lane} - GREEN</p>', unsafe_allow_html=True)
        color_box = "#00ff00"
    elif state == "YELLOW":
        st.markdown(f'<p class="status-yellow">🟡 {current_lane} - YELLOW</p>', unsafe_allow_html=True)
        color_box = "#ffff00"
    else:
        st.markdown(f'<p class="status-red">🔴 ALL RED</p>', unsafe_allow_html=True)
        color_box = "#ff0000"

    # Timer
    st.progress(min(timer / 45, 1.0))
    st.metric("Time Remaining", f"{timer:.1f}s")

    st.markdown("---")

    # Vehicle counts
    st.markdown("### 🚗 Live Counts")
    for lane, count in st.session_state.vehicle_counts.items():
        is_active = (lane == current_lane)
        if is_active:
            st.success(f"**{lane}:** {count} vehicles ← ACTIVE")
        else:
            st.info(f"{lane}: {count} vehicles")

    if show_explanations:
        st.markdown("---")
        st.markdown("### 📚 How It Works")

        st.markdown("""
        <div class="explanation-box">
        <h4>🔍 Step 1: Detection</h4>
        YOLO AI model detects vehicles in each camera feed
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="explanation-box">
        <h4>📊 Step 2: Analysis</h4>
        System counts vehicles and calculates:
        <br><b>Green Time = 10s + (vehicles × 0.5s)</b>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="explanation-box">
        <h4>🎯 Step 3: Decision</h4>
        Max Pressure algorithm selects the lane with most vehicles
        </div>
        """, unsafe_allow_html=True)

        if state == "GREEN":
            count = st.session_state.vehicle_counts[current_lane]
            calc_time = min(10 + (count * 0.5), 45)

            st.markdown("""
            <div class="explanation-box">
            <h4>💡 Current Calculation</h4>
            """, unsafe_allow_html=True)
            st.write(f"**{current_lane}** has **{count} vehicles**")
            st.write(f"Formula: 10 + ({count} × 0.5) = **{calc_time:.1f}s**")
            st.markdown("</div>", unsafe_allow_html=True)

# Bottom section
st.markdown("---")
st.header("📈 Performance Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cycles", stats['total_cycles'], delta=None)

with col2:
    st.metric("Vehicles Served", stats['total_vehicles_served'])

with col3:
    st.metric("Avg per Cycle", f"{stats.get('avg_vehicles_per_cycle', 0):.1f}")

with col4:
    st.metric("Cycles/Min", f"{stats.get('cycles_per_minute', 0):.1f}")

# Green time distribution
st.subheader("⏱️ Green Time Distribution")
green_times = stats['lane_green_times']
if sum(green_times.values()) > 0:
    import pandas as pd

    df = pd.DataFrame({
        'Lane': list(green_times.keys()),
        'Time (s)': list(green_times.values())
    })
    st.bar_chart(df.set_index('Lane'))

# Auto-refresh
if run_simulation:
    time.sleep(0.5)
    st.rerun()