import os
import json
import gradio as gr
from openai import OpenAI

# --- 1. API CONFIGURATION ---
# Using os.getenv is safer for local apps. 
# Make sure you set your HF_TOKEN in your terminal before running!
HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(
    base_url="https://router.huggingface.co/v1", 
    api_key=HF_TOKEN
)

# --- 2. DATA PERSISTENCE ---
USER_DATA_FILE = "users.json"
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w") as f:
        # Default admin account
        json.dump({"admin": {"password": "byte123", "class": "General"}}, f)

# --- 3. UI & LOGIC ---
force_dark_js = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

def prompt(user_class):
    return f"""You are ByteBuddy, an AI tutor. The student is currently in: {user_class}.

    PEDAGOGICAL RULES:
    1. Socratic Method: Never give direct answers. Ask questions like "What is the problem asking?"
    2. Class Focus:
       - If AP Computer Science A (Java): Focus on OOP, inheritance, and logic.
       - If AP CS Principles (Python/JS): Focus on algorithms and big-picture logic.
       - If AI & Machine Learning: Focus on Python, data models, and neural logic.
       - If Web Development: Focus on creating websites, covering css, js, and html.
       - If Intro to C++ : Take into consideration these are 6th graders possibly with no prior knowledge.
    3. Safeguards: If asked to "write code," refuse and offer to help with logic instead.
    4. Tone: Encouraging and witty. Use "You're close!"
    5. What if questions: Always end with a "What if..." question tailored to {user_class}.
    6. If the student doesn't understand something, try to break it down slightly.
    """

def predict(message, history, user_class):
    system_content = prompt(user_class)
    messages = [{"role": "system", "content": system_content}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct:novita",
            messages=messages,
            stream=True
        )
        response = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
                yield response
    except Exception as e:
        yield f"Neural Link Error: {str(e)}"

# --- 4. CSS STYLING ---
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Syncopate:wght@700&display=swap');

body {
 background-color: #020617 !important;
}
.gradio-container { background-color: #020617 !important; border: none !important;}
#splash-view {
   display: flex !important;
   flex-direction: column !important;
   align-items: center !important;
   justify-content: center !important;
   min-height: 80vh !important;
}
.logo-text {
   font-family: 'Orbitron', sans-serif !important;
   font-weight: 900 !important;
   font-size: clamp(3rem, 10vw, 6rem) !important;
   color: #38bdf8 !important;
   text-transform: uppercase;
   letter-spacing: 10px;
}
.grad-btn {
   background: linear-gradient(90deg, #1e40af, #3b82f6, #1e40af) !important;
   color: white !important;
   padding: 18px 60px !important;
   border-radius: 50px !important;
   font-family: 'Syncopate', sans-serif !important;
   cursor: pointer;
}
.chatbot span, .chatbot p { color: #cfdae6 !important; }
"""

# --- 5. INTERFACE BUILDER ---
with gr.Blocks(css=custom_css, js=force_dark_js, theme=gr.themes.Default()) as demo:
    current_user_class = gr.State("General")

    with gr.Column(visible=True, elem_id="splash-view") as cover_view:
        gr.HTML("""
            <div style="display: flex; flex-direction: column; align-items: center;">
                <h1 class='logo-text'>BYTEBUDDY</h1>
                <p style='color: #64748b; font-family: "Syncopate", sans-serif; font-size: 0.8rem; letter-spacing: 4px; margin-top: -10px;'>V 1.0</p>
            </div>
        """)
        enter_btn = gr.Button("GET STARTED", elem_classes="grad-btn")

    with gr.Column(visible=False) as auth_view:
        with gr.Row():
            with gr.Column(scale=1): pass
            with gr.Column(scale=2):
                gr.HTML("<h2 style='color: #38bdf8; text-align: center; font-family: Orbitron;'>LOGIN/SIGNUP</h2>")
                with gr.Tabs():
                    with gr.TabItem("Login"):
                        l_user = gr.Textbox(label="User ID")
                        l_pw = gr.Textbox(label="Passcode", type="password")
                        l_btn = gr.Button("AUTHORIZE", variant="primary")
                        l_msg = gr.Markdown("")
                    with gr.TabItem("Sign Up"):
                        s_user = gr.Textbox(label="New User ID")
                        s_pw = gr.Textbox(label="New Passcode", type="password")
                        s_class = gr.Dropdown(
                            ["AP Computer Science A (Java)", "AP CS Principles (Python/JS)", "AI & Machine Learning", "Intro to C++", "Web Development"],
                            label="Class"
                        )
                        s_btn = gr.Button("CREATE PROFILE")
                        s_msg = gr.Markdown("")
            with gr.Column(scale=1): pass

    with gr.Column(visible=False) as main_view:
        class_label = gr.Markdown("Chatbot Running")
        chatbot = gr.Chatbot(type="messages", height=550)
        with gr.Row(variant="compact"):
            msg_input = gr.Textbox(placeholder="Input command...", scale=8, label="", container=False)
            send_btn = gr.Button("SEND", scale=1, variant="primary")

    # --- BUTTON LOGIC ---
    enter_btn.click(lambda: (gr.update(visible=False), gr.update(visible=True)), None, [cover_view, auth_view])

    def handle_login(u, p):
        try:
            with open(USER_DATA_FILE, "r") as f:
                users = json.load(f)
            if u in users:
                user_entry = users[u]
                stored_pw = user_entry["password"] if isinstance(user_entry, dict) else user_entry
                u_class = user_entry.get("class", "General") if isinstance(user_entry, dict) else "General"
                if stored_pw == p:
                    return (gr.update(visible=False), gr.update(visible=True), f"Class: {u_class}", u_class, "")
            return gr.update(visible=True), gr.update(visible=False), "", "General", " Invalid Credentials"
        except Exception as e:
            return gr.update(visible=True), gr.update(visible=False), "", "General", f" System Error: {str(e)}"

    l_btn.click(handle_login, [l_user, l_pw], [auth_view, main_view, class_label, current_user_class, l_msg])

    def handle_signup(u, p, c):
        if not u or not p or not c: return "Fields Empty"
        with open(USER_DATA_FILE, "r") as f: users = json.load(f)
        if u in users: return " Username Taken"
        users[u] = {"password": p, "class": c}
        with open(USER_DATA_FILE, "w") as f: json.dump(users, f)
        return f"Profile Created for {c}. Please Login."

    s_btn.click(handle_signup, [s_user, s_pw, s_class], s_msg)

    def chat_flow(msg, history, user_class):
        if not msg: yield history; return
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": ""})
        yield history
        response = ""
        for r in predict(msg, history[:-2], user_class):
            response = r
            history[-1]["content"] = response
            yield history

    send_btn.click(chat_flow, [msg_input, chatbot, current_user_class], [chatbot]).then(lambda: "", None, [msg_input])
    msg_input.submit(chat_flow, [msg_input, chatbot, current_user_class], [chatbot]).then(lambda: "", None, [msg_input])

# --- 6. RUN THE APP ---
if __name__ == "__main__":
    # share=True creates a public URL link for 72 hours
    demo.launch(share=True)