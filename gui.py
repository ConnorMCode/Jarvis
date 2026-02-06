import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
from ai_client import ask_ai
from db import db

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - AI Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        self.debug = False
        self.response_thread = None
        self.conversation_history = []  # Maintain conversation context
        
        # Configure styles
        self.setup_styles()
        
        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="Jarvis Chat Assistant", foreground="#1f77b4")
        title_label.pack(side=tk.LEFT)
        title_label.configure(font=("Segoe UI", 14, "bold"))
        
        debug_button = ttk.Button(header_frame, text="Debug: OFF", command=self.toggle_debug, width=12)
        debug_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.debug_button = debug_button
        
        clear_history_button = ttk.Button(header_frame, text="Clear History", command=self.clear_history, width=12)
        clear_history_button.pack(side=tk.RIGHT)
        
        # Chat display area
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Add label
        ttk.Label(display_frame, text="Conversation:").pack(anchor=tk.W, pady=(0, 5))
        
        # Text widget with scrollbar
        self.chat_display = scrolledtext.ScrolledText(
            display_frame,
            wrap=tk.WORD,
            height=20,
            font=("Courier New", 10),
            bg="#ffffff",
            fg="#000000",
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Configure text tags for styling
        self.chat_display.tag_config("user", foreground="#1f77b4", font=("Courier New", 10, "bold"))
        self.chat_display.tag_config("ai", foreground="#2ca02c", font=("Courier New", 10))
        self.chat_display.tag_config("debug", foreground="#ff7f0e", font=("Courier New", 9))
        self.chat_display.tag_config("info", foreground="#7f7f7f", font=("Courier New", 9))
        self.chat_display.tag_config("error", foreground="#d62728", font=("Courier New", 10))
        
        # Input area
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="Your message:").pack(anchor=tk.W, pady=(0, 5))
        
        # Input box frame
        entry_frame = ttk.Frame(input_frame)
        entry_frame.pack(fill=tk.X)
        
        self.input_field = ttk.Entry(entry_frame, font=("Segoe UI", 10))
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        send_button = ttk.Button(entry_frame, text="Send", command=self.send_message, width=10)
        send_button.pack(side=tk.RIGHT)
        
        # Welcome message
        self.add_message("Welcome to Jarvis!", "info")
        self.add_message("Ask me about your events, todos, goals, and notes.", "info")
        self.add_message("I can only see the data I need for your question.\n", "info")
        
        # Focus on input field
        self.input_field.focus()
    
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure button style
        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=5
        )
        
        # Configure label style
        style.configure(
            "TLabel",
            font=("Segoe UI", 10),
            background="#f0f0f0"
        )
        
        # Configure frame background
        style.configure("TFrame", background="#f0f0f0")
    
    def add_message(self, message, tag=""):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        if self.chat_display.index(tk.END) != "1.0":
            self.chat_display.insert(tk.END, "\n")
        self.chat_display.insert(tk.END, message, tag)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.root.update()
    
    def toggle_debug(self):
        """Toggle debug mode"""
        self.debug = not self.debug
        status = "ON" if self.debug else "OFF"
        self.debug_button.config(text=f"Debug: {status}")
        self.add_message(f"Debug mode {status}\n", "info")
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.add_message("Conversation history cleared.\n", "info")
    
    def send_message(self):
        """Send message and get AI response"""
        user_input = self.input_field.get().strip()
        
        if not user_input:
            return
        
        # Clear input field
        self.input_field.delete(0, tk.END)
        
        # Add user message to display
        self.add_message(f"You: {user_input}", "user")
        
        # Disable send button and input field while processing
        self.input_field.config(state=tk.DISABLED)
        
        # Start AI response in a separate thread to keep UI responsive
        self.response_thread = threading.Thread(
            target=self._get_ai_response,
            args=(user_input,),
            daemon=True
        )
        self.response_thread.start()
    
    def _get_ai_response(self, user_input):
        """Get AI response in background thread"""
        try:
            if self.debug:
                self.add_message("\n[DEBUG] Sending query to AI...", "debug")
            
            ai_message, usage = ask_ai(user_input, debug=self.debug, messages_history=self.conversation_history)
            
            # Add this exchange to conversation history for context
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": ai_message})
            
            # Add AI response to display in main thread
            self.root.after(0, self._display_ai_response, ai_message, usage)
        
        except Exception as e:
            self.root.after(0, self._display_error, str(e))
        
        finally:
            # Re-enable input field
            self.root.after(0, self._enable_input)
    
    def _display_ai_response(self, ai_message, usage):
        """Display AI response (called from main thread)"""
        self.add_message(f"\nJarvis: {ai_message}", "ai")
        tokens_info = f"\n(Tokens used: Input: {usage.prompt_tokens}, Output: {usage.completion_tokens})"
        self.add_message(tokens_info, "info")
    
    def _display_error(self, error_msg):
        """Display error message (called from main thread)"""
        self.add_message(f"\nError: {error_msg}", "error")
    
    def _enable_input(self):
        """Re-enable input field (called from main thread)"""
        self.input_field.config(state=tk.NORMAL)
        self.input_field.focus()

def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
