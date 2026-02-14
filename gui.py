import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from tkcalendar import Calendar
import threading
from datetime import datetime
from ai_client import ask_ai
from db import db

# Panel width settings (adjust these to change Goals/To-Dos widths)
class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - AI Assistant")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f0f0")
        
        self.debug = False
        self.response_thread = None
        self.conversation_history = []  # Maintain conversation context
        
        # Track calendar double-clicks
        self.last_calendar_click = None
        self.last_calendar_click_time = None
        
        # Configure styles
        self.setup_styles()
        
        # Create container with left (chat) and right (goals) panes
        container = ttk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left pane: existing chat UI (keep its current dimensions)
        chat_frame = ttk.Frame(container)
        chat_frame.grid(row=0, column=0, sticky=tk.NSEW)

        # Right pane: goals list
        goal_frame = ttk.Frame(container)
        goal_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))

        # Far-right pane: todos list (to the right of goals)
        todo_frame = ttk.Frame(container)
        todo_frame.grid(row=0, column=2, sticky=tk.NSEW, padx=(10, 0))

        # Make left chat area expand, keep right panels fixed width
        container.columnconfigure(0, weight=1, minsize=180)
        container.columnconfigure(1, weight=0, minsize=180)
        container.columnconfigure(2, weight=0, minsize=180)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        # Calendar panel (full width at bottom)
        calendar_frame = ttk.LabelFrame(container, text="Calendar", padding=10)
        calendar_frame.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, pady=(10, 0))
        
        # Header
        header_frame = ttk.Frame(chat_frame)
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
        display_frame = ttk.Frame(chat_frame)
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
        input_frame = ttk.Frame(chat_frame)
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

        # Database reference
        self.db = db

        # Create goals panel on the right
        # Force goal_frame to a fixed width so treeview doesn't expand it
        goal_frame.config(width=180)
        goal_frame.grid_propagate(False)
        ttk.Label(goal_frame, text="Goals:").pack(anchor=tk.W)

        # Treeview for goals
        columns = ("title", "priority", "due")
        self.goals_tree = ttk.Treeview(goal_frame, columns=columns, show="headings", selectmode="browse", height=20)
        self.goals_tree.heading("title", text="Title")
        self.goals_tree.heading("priority", text="Priority")
        self.goals_tree.heading("due", text="Due")
        self.goals_tree.column("title", width=150, anchor=tk.W)
        self.goals_tree.column("priority", width=50, anchor=tk.CENTER)
        self.goals_tree.column("due", width=80, anchor=tk.CENTER)
        self.goals_tree.pack(fill=tk.BOTH, expand=True)

        # Attach a vertical scrollbar for goals
        goals_scroll = ttk.Scrollbar(goal_frame, orient=tk.VERTICAL, command=self.goals_tree.yview)
        self.goals_tree.configure(yscrollcommand=goals_scroll.set)
        goals_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to show/edit details
        self.goals_tree.bind("<Double-1>", self._on_goal_double_click)

        # Load goals into the panel
        self.load_goals()

        # --- To-Do panel setup (to the right of goals) ---
        # Force todo_frame to a fixed width
        todo_frame.config(width=180)
        todo_frame.grid_propagate(False)
        ttk.Label(todo_frame, text="To-Dos:").pack(anchor=tk.W)

        todo_columns = ("title", "priority", "due", "completed")
        self.todos_tree = ttk.Treeview(todo_frame, columns=todo_columns, show="headings", selectmode="browse", height=20)
        self.todos_tree.heading("title", text="Title")
        self.todos_tree.heading("priority", text="Prio")
        self.todos_tree.heading("due", text="Due")
        self.todos_tree.heading("completed", text="Done")
        self.todos_tree.column("title", width=200, anchor=tk.W)
        self.todos_tree.column("priority", width=50, anchor=tk.CENTER)
        self.todos_tree.column("due", width=80, anchor=tk.CENTER)
        self.todos_tree.column("completed", width=50, anchor=tk.CENTER)
        self.todos_tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for todos
        todos_scroll = ttk.Scrollbar(todo_frame, orient=tk.VERTICAL, command=self.todos_tree.yview)
        self.todos_tree.configure(yscrollcommand=todos_scroll.set)
        todos_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to edit todo
        self.todos_tree.bind("<Double-1>", self._on_todo_double_click)

        # Load todos into the panel
        self.load_todos()

        # Create calendar widget
        self.calendar = Calendar(calendar_frame, year=datetime.now().year, month=datetime.now().month, selectmode='day')
        self.calendar.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure calendar tag for event dates
        self.calendar.tag_config("event", background="lightgreen", foreground="black")
        
        # Load and tag event dates on calendar
        self.load_event_dates()
        
        # Bind click events to all calendar date labels
        self.calendar.bind("<Button-1>", self._on_calendar_click, add=True)
        for child in self.calendar.winfo_children():
            child.bind("<Button-1>", self._on_calendar_click, add=True)
            for grandchild in child.winfo_children():
                grandchild.bind("<Button-1>", self._on_calendar_click, add=True)
    
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

    def load_goals(self):
        """Load goals from the database into the goals treeview."""
        try:
            for i in self.goals_tree.get_children():
                self.goals_tree.delete(i)

            goals = self.db.get_goals(completed=False)
            for g in goals:
                gid = g.get('id')
                title = g.get('title', '')
                priority = g.get('priority', '')
                due = g.get('due_date') or ''
                if due:
                    # show date portion only
                    due = due.split('T')[0]
                self.goals_tree.insert('', tk.END, iid=str(gid), values=(title, priority, due))
        except Exception as e:
            self.add_message(f"Error loading goals: {e}", "error")

    def _on_goal_double_click(self, event):
        """Open an edit dialog for the selected goal."""
        sel = self.goals_tree.selection()
        if not sel:
            return
        try:
            gid = int(sel[0])
        except Exception:
            return

        # Find goal object in database
        goal_obj = next((g for g in self.db.goals if g.id == gid), None)
        if not goal_obj:
            messagebox.showinfo("Goal Details", "No details found for selected goal.")
            return

        # Edit window
        win = tk.Toplevel(self.root)
        win.title(f"Edit Goal: {goal_obj.title}")
        win.transient(self.root)
        win.grab_set()

        # Title
        ttk.Label(win, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
        title_var = tk.StringVar(value=goal_obj.title)
        title_entry = ttk.Entry(win, textvariable=title_var, width=60)
        title_entry.grid(row=0, column=1, padx=8, pady=6)

        # Description
        ttk.Label(win, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=8, pady=6)
        desc_text = tk.Text(win, width=60, height=8)
        desc_text.grid(row=1, column=1, padx=8, pady=6)
        desc_text.insert(tk.END, goal_obj.description or "")

        # Priority
        ttk.Label(win, text="Priority (1-5):").grid(row=2, column=0, sticky=tk.W, padx=8, pady=6)
        priority_var = tk.IntVar(value=getattr(goal_obj, 'priority', 3))
        priority_spin = ttk.Spinbox(win, from_=1, to=5, textvariable=priority_var, width=5)
        priority_spin.grid(row=2, column=1, sticky=tk.W, padx=8, pady=6)

        # Due date
        ttk.Label(win, text="Due date (YYYY-MM-DD or blank):").grid(row=3, column=0, sticky=tk.W, padx=8, pady=6)
        due_var = tk.StringVar(value=(goal_obj.due_date.isoformat().split('T')[0] if getattr(goal_obj, 'due_date', None) else ""))
        due_entry = ttk.Entry(win, textvariable=due_var, width=20)
        due_entry.grid(row=3, column=1, sticky=tk.W, padx=8, pady=6)

        # Completed
        completed_var = tk.BooleanVar(value=getattr(goal_obj, 'completed', False))
        completed_check = ttk.Checkbutton(win, text="Completed", variable=completed_var)
        completed_check.grid(row=4, column=1, sticky=tk.W, padx=8, pady=6)

        # Buttons
        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)

        def on_save():
            new_title = title_var.get().strip()
            new_desc = desc_text.get("1.0", tk.END).strip()
            try:
                new_priority = int(priority_var.get())
            except Exception:
                messagebox.showerror("Validation Error", "Priority must be an integer between 1 and 5.")
                return

            due_input = due_var.get().strip()
            new_due = None
            if due_input:
                try:
                    new_due = datetime.fromisoformat(due_input)
                except Exception:
                    messagebox.showerror("Validation Error", "Due date must be YYYY-MM-DD.")
                    return

            # Update goal object
            goal_obj.title = new_title
            goal_obj.description = new_desc
            goal_obj.priority = new_priority
            goal_obj.due_date = new_due
            goal_obj.completed = bool(completed_var.get())

            try:
                # Save DB and refresh UI
                self.db.save()
                self.load_goals()
                win.destroy()
                self.add_message(f"Goal '{new_title}' updated.", "info")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save goal: {e}")

        def on_cancel():
            win.destroy()

        save_btn = ttk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=6)
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=6)

        # Set focus
        title_entry.focus()

        # Center the edit window on the screen
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        win.geometry(f"+{x}+{y}")

    def load_todos(self):
        """Load todos from the database into the todos treeview."""
        try:
            for i in self.todos_tree.get_children():
                self.todos_tree.delete(i)

            todos = self.db.get_all_todos()
            for t in todos:
                tid = t.get('id')
                title = t.get('title', '')
                priority = t.get('priority', '')
                due = t.get('due_date') or ''
                if due:
                    due = due.split('T')[0]
                completed = 'Yes' if t.get('completed') else 'No'
                self.todos_tree.insert('', tk.END, iid=str(tid), values=(title, priority, due, completed))
        except Exception as e:
            self.add_message(f"Error loading todos: {e}", "error")

    def load_event_dates(self):
        """Load event dates from database and tag them on the calendar."""
        try:
            # Get all events from database
            events = self.db.get_all_events()
            
            # Extract unique dates and tag them
            event_dates = set()
            for event in events:
                # Extract date from event
                event_date = event.get('date')
                if event_date:
                    # Parse ISO format date
                    if isinstance(event_date, str):
                        date_only = event_date.split('T')[0]
                        parsed_date = datetime.fromisoformat(date_only).date()
                        event_dates.add(parsed_date)
                    else:
                        parsed_date = event_date.date() if isinstance(event_date, datetime) else event_date
                        event_dates.add(parsed_date)
            
            # Tag each event date on the calendar using calevent_create
            for date in event_dates:
                self.calendar.calevent_create(date, "", "event")
        except Exception as e:
            self.add_message(f"Error loading event dates: {e}", "error")

    def _on_calendar_click(self, event):
        """Handle calendar single click. Detect double-click by rapid succession."""
        import time
        
        try:
            selected_date = self.calendar.selection_get()
            
            current_time = time.time()
            
            # Check if this is a double-click (same date clicked within 500ms)
            if (self.last_calendar_click == selected_date and 
                self.last_calendar_click_time and 
                (current_time - self.last_calendar_click_time) < 0.5):
                self._handle_calendar_double_click(selected_date)
                self.last_calendar_click = None
                self.last_calendar_click_time = None
            else:
                self.last_calendar_click = selected_date
                self.last_calendar_click_time = current_time
        except Exception as e:
            self.add_message(f"Error in calendar click: {e}", "error")

    def _handle_calendar_double_click(self, selected_date):
        """Process the double-click event on a calendar date."""
        try:
            if not selected_date:
                return
            
            # Check if there are events on this date
            events_on_date = []
            all_events = self.db.get_all_events()
            
            for e in all_events:
                event_date = e.get('date')
                
                if isinstance(event_date, str):
                    parsed_date = datetime.fromisoformat(event_date.split('T')[0]).date()
                else:
                    parsed_date = event_date.date() if isinstance(event_date, datetime) else event_date
                
                if parsed_date == selected_date:
                    events_on_date.append(e)
            
            # If no events, allow creating a new one; if one event, edit it; if multiple, show list
            if not events_on_date:
                self._open_event_editor(None, selected_date)
            elif len(events_on_date) == 1:
                # Open editor for the single event
                event_id = events_on_date[0].get('id')
                event_obj = next((e for e in self.db.events if e.id == event_id), None)
                if event_obj:
                    self._open_event_editor(event_obj)
            else:
                # Multiple events - show selection dialog
                messagebox.showinfo("Multiple Events", f"Found {len(events_on_date)} events on this date. Feature coming soon.")
        except Exception as e:
            self.add_message(f"Error handling calendar date: {e}", "error")

    def _open_event_editor(self, event_obj=None, new_date=None):
        """Open an event editor dialog."""
        if event_obj is None and new_date is None:
            return
        
        win = tk.Toplevel(self.root)
        if event_obj:
            win.title(f"Edit Event: {event_obj.title}")
        else:
            win.title(f"New Event: {new_date}")
        win.transient(self.root)
        win.grab_set()

        # Title
        ttk.Label(win, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
        title_var = tk.StringVar(value=event_obj.title if event_obj else "")
        title_entry = ttk.Entry(win, textvariable=title_var, width=60)
        title_entry.grid(row=0, column=1, padx=8, pady=6)

        # Description
        ttk.Label(win, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=8, pady=6)
        desc_text = tk.Text(win, width=60, height=8)
        desc_text.grid(row=1, column=1, padx=8, pady=6)
        if event_obj:
            desc_text.insert(tk.END, event_obj.description or "")

        # Date
        ttk.Label(win, text="Date (YYYY-MM-DD HH:MM):").grid(row=2, column=0, sticky=tk.W, padx=8, pady=6)
        if event_obj:
            date_val = event_obj.date.isoformat() if event_obj.date else ""
        else:
            date_val = f"{new_date} 12:00"
        date_var = tk.StringVar(value=date_val)
        date_entry = ttk.Entry(win, textvariable=date_var, width=30)
        date_entry.grid(row=2, column=1, sticky=tk.W, padx=8, pady=6)

        # Tags
        ttk.Label(win, text="Tags (comma separated):").grid(row=3, column=0, sticky=tk.W, padx=8, pady=6)
        tags_var = tk.StringVar(value=','.join(getattr(event_obj, 'tags', []) or []) if event_obj else "")
        tags_entry = ttk.Entry(win, textvariable=tags_var, width=40)
        tags_entry.grid(row=3, column=1, sticky=tk.W, padx=8, pady=6)

        # Buttons
        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

        def on_save():
            new_title = title_var.get().strip()
            new_desc = desc_text.get("1.0", tk.END).strip()
            
            # Parse date - handle ISO format (2026-02-06T12:30:00) and regular format
            try:
                date_input = date_var.get().strip()
                # Replace T with space if present (ISO format)
                date_input = date_input.replace('T', ' ')
                # Try parsing with seconds first, then without
                try:
                    new_date_obj = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # Try without seconds
                    if " " not in date_input:
                        date_input += " 12:00"
                    new_date_obj = datetime.strptime(date_input, "%Y-%m-%d %H:%M")
            except Exception as ex:
                messagebox.showerror("Validation Error", "Date must be YYYY-MM-DD or YYYY-MM-DD HH:MM")
                return

            # Tags
            tags_input = tags_var.get().strip()
            new_tags = [t.strip() for t in tags_input.split(',') if t.strip()]

            if event_obj:
                # Update existing event
                event_obj.title = new_title
                event_obj.description = new_desc
                event_obj.date = new_date_obj
                event_obj.tags = new_tags
                msg = f"Event '{new_title}' updated."
            else:
                # Create new event
                self.db.add_event(new_title, new_date_obj, new_desc, new_tags)
                msg = f"Event '{new_title}' created."

            try:
                self.db.save()
                self.load_event_dates()  # Refresh calendar
                win.destroy()
                self.add_message(msg, "info")
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror("Save Error", f"Failed to save event: {e}")

        def on_cancel():
            win.destroy()

        save_btn = ttk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=6)
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=6)

        # Set focus
        title_entry.focus()

        # Center window
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        win.geometry(f"+{x}+{y}")

    def _on_todo_double_click(self, event):
        """Open an edit dialog for the selected todo."""
        sel = self.todos_tree.selection()
        if not sel:
            return
        try:
            tid = int(sel[0])
        except Exception:
            return

        todo_obj = next((t for t in self.db.todos if t.id == tid), None)
        if not todo_obj:
            messagebox.showinfo("To-Do Details", "No details found for selected to-do.")
            return

        win = tk.Toplevel(self.root)
        win.title(f"Edit To-Do: {todo_obj.title}")
        win.transient(self.root)
        win.grab_set()

        # Title
        ttk.Label(win, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
        title_var = tk.StringVar(value=todo_obj.title)
        title_entry = ttk.Entry(win, textvariable=title_var, width=60)
        title_entry.grid(row=0, column=1, padx=8, pady=6)

        # Description
        ttk.Label(win, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=8, pady=6)
        desc_text = tk.Text(win, width=60, height=8)
        desc_text.grid(row=1, column=1, padx=8, pady=6)
        desc_text.insert(tk.END, todo_obj.description or "")

        # Priority
        ttk.Label(win, text="Priority (1-5):").grid(row=2, column=0, sticky=tk.W, padx=8, pady=6)
        priority_var = tk.IntVar(value=getattr(todo_obj, 'priority', 3))
        priority_spin = ttk.Spinbox(win, from_=1, to=5, textvariable=priority_var, width=5)
        priority_spin.grid(row=2, column=1, sticky=tk.W, padx=8, pady=6)

        # Due date
        ttk.Label(win, text="Due date (YYYY-MM-DD or blank):").grid(row=3, column=0, sticky=tk.W, padx=8, pady=6)
        due_var = tk.StringVar(value=(todo_obj.due_date.isoformat().split('T')[0] if getattr(todo_obj, 'due_date', None) else ""))
        due_entry = ttk.Entry(win, textvariable=due_var, width=20)
        due_entry.grid(row=3, column=1, sticky=tk.W, padx=8, pady=6)

        # Start date
        ttk.Label(win, text="Start date (YYYY-MM-DD or blank):").grid(row=4, column=0, sticky=tk.W, padx=8, pady=6)
        start_var = tk.StringVar(value=(todo_obj.start_date.isoformat().split('T')[0] if getattr(todo_obj, 'start_date', None) else ""))
        start_entry = ttk.Entry(win, textvariable=start_var, width=20)
        start_entry.grid(row=4, column=1, sticky=tk.W, padx=8, pady=6)

        # Completed
        completed_var = tk.BooleanVar(value=getattr(todo_obj, 'completed', False))
        completed_check = ttk.Checkbutton(win, text="Completed", variable=completed_var)
        completed_check.grid(row=5, column=1, sticky=tk.W, padx=8, pady=6)

        # Tags
        ttk.Label(win, text="Tags (comma separated):").grid(row=6, column=0, sticky=tk.W, padx=8, pady=6)
        tags_var = tk.StringVar(value=','.join(getattr(todo_obj, 'tags', []) or []))
        tags_entry = ttk.Entry(win, textvariable=tags_var, width=40)
        tags_entry.grid(row=6, column=1, sticky=tk.W, padx=8, pady=6)

        # Buttons
        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)

        def on_save():
            new_title = title_var.get().strip()
            new_desc = desc_text.get("1.0", tk.END).strip()
            try:
                new_priority = int(priority_var.get())
            except Exception:
                messagebox.showerror("Validation Error", "Priority must be an integer between 1 and 5.")
                return

            # Parse dates
            new_due = None
            due_input = due_var.get().strip()
            if due_input:
                try:
                    new_due = datetime.fromisoformat(due_input)
                except Exception:
                    messagebox.showerror("Validation Error", "Due date must be YYYY-MM-DD.")
                    return

            new_start = None
            start_input = start_var.get().strip()
            if start_input:
                try:
                    new_start = datetime.fromisoformat(start_input)
                except Exception:
                    messagebox.showerror("Validation Error", "Start date must be YYYY-MM-DD.")
                    return

            # Tags
            tags_input = tags_var.get().strip()
            new_tags = [t.strip() for t in tags_input.split(',') if t.strip()]

            # Update todo object
            todo_obj.title = new_title
            todo_obj.description = new_desc
            todo_obj.priority = new_priority
            todo_obj.due_date = new_due
            todo_obj.start_date = new_start
            todo_obj.completed = bool(completed_var.get())
            todo_obj.tags = new_tags

            try:
                self.db.save()
                self.load_todos()
                win.destroy()
                self.add_message(f"To-Do '{new_title}' updated.", "info")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save to-do: {e}")

        def on_cancel():
            win.destroy()

        save_btn = ttk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=6)
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=6)

        # Set focus
        title_entry.focus()

        # Center window
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        win.geometry(f"+{x}+{y}")

def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
