import os
import subprocess
import threading
import gradio as gr

def run_agent_worker():
    """Runs the LiveKit agent worker in the background."""
    print("Starting Tandem Voice Agent worker...")
    subprocess.run(["python", "-m", "agent.worker", "start"])

# Start the LiveKit voice agent daemon in a background thread
thread = threading.Thread(target=run_agent_worker, daemon=True)
thread.start()

def check_status():
    livekit_url = os.environ.get("LIVEKIT_URL", "Not configured")
    is_alive = thread.is_alive()
    return f"Status: {'Active & Connected' if is_alive else 'Stopped'}\nLiveKit Server: {livekit_url}"

with gr.Blocks(title="Tandem Voice Worker") as demo:
    gr.Markdown("# 🎙️ Tandem Real-Time Voice Worker")
    gr.Markdown("Persistent daemon listening for incoming WebRTC audio rooms via LiveKit.")
    status_box = gr.Textbox(label="Worker Status", value=check_status(), interactive=False)
    refresh_btn = gr.Button("Check Health")
    refresh_btn.click(fn=check_status, outputs=status_box)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, ssr_mode=False)
