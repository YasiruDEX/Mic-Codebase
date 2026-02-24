"""
ReSpeaker Mic Array - Real-time DOA and Audio Visualization
============================================================
- Polar plot showing Direction of Arrival (DOA)
- Time-series plot showing voice activity detection
- Real-time updates with matplotlib animation
"""
import sys
import os

# Fix TCL/TK path for venv on Windows
python_path = sys.base_prefix
if os.path.exists(os.path.join(python_path, 'tcl', 'tcl8.6')):
    os.environ['TCL_LIBRARY'] = os.path.join(python_path, 'tcl', 'tcl8.6')
    os.environ['TK_LIBRARY'] = os.path.join(python_path, 'tcl', 'tk8.6')

sys.path.insert(0, 'usb_4_mic_array')

import matplotlib
matplotlib.use('TkAgg')  # Explicitly set backend
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Wedge
from collections import deque
import time

# Import ReSpeaker tuning
from tuning import Tuning
import usb.core
import usb.util

# Configuration
HISTORY_LENGTH = 100  # Number of data points to show in time series
UPDATE_INTERVAL = 50  # Milliseconds between updates

class ReSpeakerVisualizer:
    def __init__(self):
        # Find the ReSpeaker device
        self.dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
        if not self.dev:
            raise RuntimeError("ReSpeaker Mic Array not found!")
        
        self.mic = Tuning(self.dev)
        print("ReSpeaker Mic Array connected!")
        
        # Data history
        self.doa_history = deque(maxlen=HISTORY_LENGTH)
        self.vad_history = deque(maxlen=HISTORY_LENGTH)
        self.time_history = deque(maxlen=HISTORY_LENGTH)
        self.start_time = time.time()
        
        # Current DOA for polar plot
        self.current_doa = 0
        
        # Setup the figure
        self.setup_plot()
    
    def setup_plot(self):
        """Create the visualization layout"""
        # Create figure with dark background
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(14, 6))
        self.fig.suptitle('ReSpeaker Mic Array - Real-time Visualization', 
                         fontsize=14, fontweight='bold', color='white')
        
        # Create subplots: polar (left), time series (right)
        self.ax_polar = self.fig.add_subplot(121, projection='polar')
        self.ax_time = self.fig.add_subplot(122)
        
        # Setup polar plot for DOA
        self.setup_polar_plot()
        
        # Setup time series plot
        self.setup_time_plot()
        
        plt.tight_layout()
    
    def setup_polar_plot(self):
        """Configure the polar DOA plot"""
        ax = self.ax_polar
        ax.set_title('Direction of Arrival (DOA)', pad=20, fontsize=12, color='cyan')
        
        # Set 0 degrees at top, clockwise direction
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        
        # Set labels
        ax.set_xticks(np.linspace(0, 2*np.pi, 8, endpoint=False))
        ax.set_xticklabels(['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°'])
        
        # Hide radial labels
        ax.set_yticks([])
        ax.set_ylim(0, 1)
        
        # Create arrow/indicator for current direction
        self.doa_arrow, = ax.plot([0, 0], [0, 0.9], 'o-', color='#00ff00', 
                                   linewidth=3, markersize=10, markevery=[1])
        
        # Create trail effect
        self.doa_trail, = ax.plot([], [], 'o', color='#00ff00', alpha=0.3, markersize=5)
        
        # Add microphone positions (assuming 4-mic circular array)
        mic_angles = np.radians([0, 90, 180, 270])
        ax.scatter(mic_angles, [0.95]*4, c='white', s=100, marker='o', zorder=5)
        ax.scatter(mic_angles, [0.95]*4, c='red', s=30, marker='o', zorder=6)
        
        # Add center circle
        ax.scatter([0], [0], c='white', s=50, marker='o', zorder=5)
        
        # Current angle text
        self.angle_text = ax.text(0, 0.3, '0°', ha='center', va='center', 
                                   fontsize=24, fontweight='bold', color='#00ff00')
    
    def setup_time_plot(self):
        """Configure the time series plot"""
        ax = self.ax_time
        ax.set_title('Voice Activity & DOA History', fontsize=12, color='cyan')
        ax.set_xlabel('Time (seconds)', color='white')
        ax.set_facecolor('#1a1a2e')
        
        # Create twin axis for DOA
        self.ax_doa = ax.twinx()
        
        # Voice activity bar/line
        self.vad_line, = ax.plot([], [], color='#ff6b6b', linewidth=2, label='Voice Activity')
        self.vad_fill = None
        
        # DOA line
        self.doa_line, = self.ax_doa.plot([], [], color='#00ff00', linewidth=2, 
                                           label='DOA Angle', linestyle='-')
        
        # Configure axes
        ax.set_ylim(-0.1, 1.5)
        ax.set_ylabel('Voice Activity', color='#ff6b6b')
        ax.tick_params(axis='y', colors='#ff6b6b')
        
        self.ax_doa.set_ylim(-10, 370)
        self.ax_doa.set_ylabel('DOA Angle (°)', color='#00ff00')
        self.ax_doa.tick_params(axis='y', colors='#00ff00')
        
        # Add legend
        lines = [self.vad_line, self.doa_line]
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left', facecolor='#1a1a2e', edgecolor='white')
        
        # Grid
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, HISTORY_LENGTH * UPDATE_INTERVAL / 1000)
    
    def update(self, frame):
        """Update function called by animation"""
        try:
            # Read current values from device
            current_doa = self.mic.direction
            current_vad = self.mic.is_voice()
            current_time = time.time() - self.start_time
            
            # Store in history
            self.doa_history.append(current_doa)
            self.vad_history.append(current_vad)
            self.time_history.append(current_time)
            
            # Update polar plot
            self.update_polar(current_doa)
            
            # Update time series
            self.update_time_series()
            
        except Exception as e:
            print(f"Error reading device: {e}")
        
        return [self.doa_arrow, self.doa_trail, self.angle_text, 
                self.vad_line, self.doa_line]
    
    def update_polar(self, doa):
        """Update the polar DOA indicator"""
        # Convert to radians
        theta = np.radians(doa)
        
        # Update main arrow
        self.doa_arrow.set_data([theta, theta], [0, 0.85])
        
        # Update trail (last few readings)
        if len(self.doa_history) > 1:
            trail_angles = [np.radians(a) for a in list(self.doa_history)[-10:]]
            trail_rs = np.linspace(0.4, 0.7, len(trail_angles))
            self.doa_trail.set_data(trail_angles, trail_rs)
        
        # Update angle text
        self.angle_text.set_text(f'{doa}°')
    
    def update_time_series(self):
        """Update the time series plot"""
        if len(self.time_history) < 2:
            return
        
        times = list(self.time_history)
        doas = list(self.doa_history)
        vads = list(self.vad_history)
        
        # Normalize time to start from 0
        times = [t - times[0] for t in times]
        
        # Update lines
        self.vad_line.set_data(times, vads)
        self.doa_line.set_data(times, doas)
        
        # Update x-axis limits for scrolling effect
        if times[-1] > HISTORY_LENGTH * UPDATE_INTERVAL / 1000:
            self.ax_time.set_xlim(times[-1] - HISTORY_LENGTH * UPDATE_INTERVAL / 1000, 
                                   times[-1] + 0.5)
    
    def run(self):
        """Start the visualization"""
        print("\n" + "="*50)
        print("Real-time DOA and Voice Activity Visualization")
        print("="*50)
        print("• Green arrow: Current sound direction")
        print("• Red line: Voice activity (0=silence, 1=voice)")
        print("• Green line: DOA angle history")
        print("\nClose the window to exit.")
        print("="*50 + "\n")
        
        # Create animation
        self.anim = FuncAnimation(
            self.fig, 
            self.update, 
            interval=UPDATE_INTERVAL,
            blit=False,
            cache_frame_data=False
        )
        
        plt.show()
    
    def close(self):
        """Clean up resources"""
        self.mic.close()


def main():
    try:
        visualizer = ReSpeakerVisualizer()
        visualizer.run()
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Make sure the ReSpeaker Mic Array is connected.")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        plt.close('all')


if __name__ == "__main__":
    main()
