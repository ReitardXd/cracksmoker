import hashlib
import itertools
import string
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from multiprocessing import Pool, Manager, cpu_count
from functools import partial
from queue import Queue, Empty

# --- Passlib is a powerful optional dependency for modern hashes ---
try:
    from passlib.hash import sha256_crypt, sha512_crypt, md5_crypt, bcrypt
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False

# ==============================================================================
# --- HASH VERIFICATION LOGIC (FROM ORIGINAL SCRIPT, LARGELY UNCHANGED) ---
# ==============================================================================

def get_verifier(hash_str):
    """
    Identifies the hash type and returns the appropriate verification function.
    """
    if PASSLIB_AVAILABLE:
        if hash_str.startswith('$6$'):
            return sha512_crypt.verify
        if hash_str.startswith('$5$'):
            return sha256_crypt.verify
        if hash_str.startswith('$1$'):
            return md5_crypt.verify
        if hash_str.startswith('$2b$') or hash_str.startswith('$2a$'):
            return bcrypt.verify
    
    # Fallback for simple, unsalted hashes
    hash_len = len(hash_str)
    if hash_len == 32:
        return lambda p, h: hashlib.md5(p.encode()).hexdigest() == h
    if hash_len == 40:
        return lambda p, h: hashlib.sha1(p.encode()).hexdigest() == h
    if hash_len == 64:
        return lambda p, h: hashlib.sha256(p.encode()).hexdigest() == h
        
    return None

# ==============================================================================
# --- WORKER FUNCTIONS FOR PARALLEL PROCESSING (UNCHANGED) ---
# ==============================================================================

def dictionary_worker(word, target_hash, verifier, found_event):
    """Worker function for the dictionary attack."""
    if found_event.is_set():
        return None
    try:
        if verifier(word, target_hash):
            found_event.set()
            return word
    except (ValueError, TypeError):
        pass
    return None

def brute_force_worker(password_tuple, target_hash, verifier, found_event):
    """Worker function for the brute-force attack."""
    if found_event.is_set():
        return None
    password = "".join(password_tuple)
    try:
        if verifier(password, target_hash):
            found_event.set()
            return password
    except (ValueError, TypeError):
        pass
    return None

# ==============================================================================
# --- MAIN ATTACK LOGIC (MODIFIED FOR GUI FEEDBACK) ---
# ==============================================================================

def run_dictionary_attack(target_hash, wordlist_path, verifier, num_processes, queue, stop_event):
    """Manages the parallel dictionary attack, sending feedback to the GUI queue."""
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            wordlist = [line.strip() for line in f]
    except FileNotFoundError:
        queue.put(("result", f"Error: Wordlist file not found at '{wordlist_path}'", "red"))
        return

    with Manager() as manager:
        found_event = manager.Event()
        worker_func = partial(dictionary_worker, target_hash=target_hash, verifier=verifier, found_event=found_event)
        
        with Pool(processes=num_processes) as pool:
            total_words = len(wordlist)
            queue.put(("progress_max", total_words))
            
            # Use imap_unordered for efficiency
            results_iterator = pool.imap_unordered(worker_func, wordlist, chunksize=5000)
            
            count = 0
            for result in results_iterator:
                if stop_event.is_set():
                    pool.terminate()
                    queue.put(("log", "Attack stopped by user.", "orange"))
                    return
                
                count += 1
                if count % 1000 == 0: # Update progress bar periodically
                    queue.put(("progress", count))

                if result:
                    pool.terminate()
                    queue.put(("result", result, "green"))
                    return
    # If loop finishes without finding a result
    queue.put(("result", "Password not found in the wordlist.", "red"))


def run_brute_force_attack(target_hash, charset, max_length, verifier, num_processes, queue, stop_event):
    """Manages the parallel brute-force attack, sending feedback to the GUI queue."""
    with Manager() as manager:
        found_event = manager.Event()
        worker_func = partial(brute_force_worker, target_hash=target_hash, verifier=verifier, found_event=found_event)

        with Pool(processes=num_processes) as pool:
            for length in range(1, max_length + 1):
                if found_event.is_set() or stop_event.is_set():
                    break
                
                queue.put(("log", f"Trying passwords of length {length}...", "cyan"))
                passwords_to_check = itertools.product(charset, repeat=length)
                total_passwords = len(charset) ** length
                queue.put(("progress_max", total_passwords))

                results_iterator = pool.imap_unordered(worker_func, passwords_to_check, chunksize=10000)

                count = 0
                for result in results_iterator:
                    if stop_event.is_set():
                        pool.terminate()
                        queue.put(("log", "Attack stopped by user.", "orange"))
                        return

                    count += 1
                    if count % 5000 == 0: # Update progress bar periodically
                        queue.put(("progress", count))
                        
                    if result:
                        pool.terminate()
                        queue.put(("result", result, "green"))
                        return
                        
    # If loop finishes without finding
    if not found_event.is_set():
        queue.put(("result", "Password not found within the specified constraints.", "red"))

# ==============================================================================
# --- TKINTER GUI APPLICATION ---
# ==============================================================================

class PasswordCrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Cracker")
        self.geometry("650x550")
        
        self.attack_thread = None
        self.stop_event = threading.Event()
        self.queue = Queue()

        # --- Style ---
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("TEntry", padding=5, font=('Helvetica', 10))
        style.configure("TButton", padding=5, font=('Helvetica', 10, 'bold'))
        style.configure("TRadiobutton", padding=5, font=('Helvetica', 10))
        
        self.create_widgets()
        self.process_queue()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input Frame ---
        input_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        input_frame.pack(fill=tk.X, expand=True)
        
        ttk.Label(input_frame, text="Target Hash:").grid(row=0, column=0, sticky=tk.W)
        self.hash_entry = ttk.Entry(input_frame, width=60)
        self.hash_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW)

        ttk.Label(input_frame, text="Attack Mode:").grid(row=1, column=0, sticky=tk.W)
        self.attack_mode = tk.StringVar(value="dictionary")
        ttk.Radiobutton(input_frame, text="Dictionary", variable=self.attack_mode, value="dictionary", command=self.toggle_mode_options).grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Brute-Force", variable=self.attack_mode, value="brute", command=self.toggle_mode_options).grid(row=1, column=2, sticky=tk.W)
        
        # --- Dictionary Attack Frame ---
        self.dict_frame = ttk.LabelFrame(main_frame, text="Dictionary Options", padding="10")
        
        ttk.Label(self.dict_frame, text="Wordlist:").grid(row=0, column=0, sticky=tk.W)
        self.wordlist_entry = ttk.Entry(self.dict_frame, width=50)
        self.wordlist_entry.grid(row=0, column=1, sticky=tk.EW)
        self.browse_button = ttk.Button(self.dict_frame, text="Browse...", command=self.browse_wordlist)
        self.browse_button.grid(row=0, column=2, padx=(5,0))
        
        # --- Brute-Force Attack Frame ---
        self.brute_frame = ttk.LabelFrame(main_frame, text="Brute-Force Options", padding="10")

        ttk.Label(self.brute_frame, text="Charset:").grid(row=0, column=0, sticky=tk.W)
        self.charset_entry = ttk.Entry(self.brute_frame, width=50)
        self.charset_entry.insert(0, string.ascii_lowercase + string.digits)
        self.charset_entry.grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(self.brute_frame, text="Max Length:").grid(row=1, column=0, sticky=tk.W)
        self.max_length_spinbox = ttk.Spinbox(self.brute_frame, from_=1, to=16, width=10)
        self.max_length_spinbox.set(8)
        self.max_length_spinbox.grid(row=1, column=1, sticky=tk.W)
        
        self.dict_frame.pack(fill=tk.X, expand=True, pady=5)
        
        # --- Controls and Output ---
        controls_frame = ttk.Frame(main_frame, padding="5")
        controls_frame.pack(fill=tk.X, expand=True)

        ttk.Label(controls_frame, text="Threads:").pack(side=tk.LEFT, padx=(0, 5))
        self.threads_spinbox = ttk.Spinbox(controls_frame, from_=1, to=cpu_count(), width=5)
        self.threads_spinbox.set(cpu_count())
        self.threads_spinbox.pack(side=tk.LEFT, padx=(0, 20))

        self.start_button = ttk.Button(controls_frame, text="Start Attack", command=self.start_attack)
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.stop_button = ttk.Button(controls_frame, text="Stop Attack", command=self.stop_attack, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))

        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, expand=True, pady=10)

        # --- Log Text Area ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED, bg="#2B2B2B", fg="white", font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for colored text
        self.log_text.tag_config("green", foreground="#7FFF00")
        self.log_text.tag_config("red", foreground="#FF4500")
        self.log_text.tag_config("cyan", foreground="#00FFFF")
        self.log_text.tag_config("orange", foreground="#FFA500")
        self.log_text.tag_config("yellow", foreground="#FFFF00")

        self.toggle_mode_options() # Set initial view

    def toggle_mode_options(self):
        """Show/hide frames based on selected attack mode."""
        if self.attack_mode.get() == "dictionary":
            self.brute_frame.pack_forget()
            self.dict_frame.pack(fill=tk.X, expand=True, pady=5)
        else:
            self.dict_frame.pack_forget()
            self.brute_frame.pack(fill=tk.X, expand=True, pady=5)
            
    def browse_wordlist(self):
        filepath = filedialog.askopenfilename(title="Select a Wordlist", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filepath:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, filepath)
            
    def log(self, message, tag=None):
        """Adds a message to the log text widget."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END) # Auto-scroll

    def start_attack(self):
        target_hash = self.hash_entry.get().strip()
        if not target_hash:
            messagebox.showerror("Error", "Target Hash cannot be empty.")
            return

        verifier = get_verifier(target_hash)
        if not verifier:
            messagebox.showerror("Error", "Unsupported or unrecognized hash format.")
            return

        # Clear previous results and state
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.stop_event.clear()

        self.set_controls_state(tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        mode = self.attack_mode.get()
        num_threads = int(self.threads_spinbox.get())
        
        self.log(f"{'='*50}\n{'Starting Attack':^50}\n{'='*50}", "yellow")
        self.log(f"[*] Target Hash: {target_hash[:30]}...", "cyan")
        self.log(f"[*] Attack Mode: {mode}", "cyan")
        
        # --- Configure and start the background thread ---
        if mode == 'dictionary':
            wordlist_path = self.wordlist_entry.get()
            if not wordlist_path:
                messagebox.showerror("Error", "Wordlist path is required for dictionary mode.")
                self.set_controls_state(tk.NORMAL)
                return
            args = (target_hash, wordlist_path, verifier, num_threads, self.queue, self.stop_event)
            target_func = run_dictionary_attack
        else: # brute
            charset = self.charset_entry.get()
            max_len = int(self.max_length_spinbox.get())
            args = (target_hash, charset, max_len, verifier, num_threads, self.queue, self.stop_event)
            target_func = run_brute_force_attack

        self.attack_thread = threading.Thread(target=target_func, args=args, daemon=True)
        self.attack_thread.start()

    def stop_attack(self):
        """Signals the running thread to stop."""
        if self.attack_thread and self.attack_thread.is_alive():
            self.stop_event.set()
            self.log("[-] Stop signal sent. Please wait...", "orange")
            self.stop_button.config(state=tk.DISABLED)

    def set_controls_state(self, state):
        """Enable or disable all input controls."""
        self.hash_entry.config(state=state)
        self.wordlist_entry.config(state=state)
        self.charset_entry.config(state=state)
        self.browse_button.config(state=state)
        self.start_button.config(state=state)
        # Spinboxes and radio buttons
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Spinbox, ttk.Radiobutton)):
                        widget.config(state=state)

    def process_queue(self):
        """Periodically check the queue for messages from the worker thread."""
        try:
            while True:
                msg = self.queue.get_nowait()
                msg_type, value = msg[0], msg[1]

                if msg_type == "log":
                    self.log(value, msg[2] if len(msg) > 2 else None)
                elif msg_type == "progress":
                    self.progress['value'] = value
                elif msg_type == "progress_max":
                    self.progress['maximum'] = value
                elif msg_type == "result":
                    # Attack finished
                    if msg[2] == "green":
                         self.log(f"\n[+] SUCCESS! Password found: {value}", "green")
                    else:
                         self.log(f"\n[-] FAILURE! {value}", "red")
                    self.attack_finished()

        except Empty:
            pass # No messages in queue
        finally:
            self.after(100, self.process_queue)

    def attack_finished(self):
        """Reset the GUI to its initial state after an attack concludes."""
        self.set_controls_state(tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.stop_event.clear()
        self.attack_thread = None

if __name__ == "__main__":
    if not PASSLIB_AVAILABLE:
        print("Warning: 'passlib' is not installed. Support for modern hash formats like bcrypt will be unavailable.")
        print("Install it using: pip install passlib bcrypt")
    app = PasswordCrackerApp()
    app.mainloop()