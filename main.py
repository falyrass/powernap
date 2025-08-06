import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys

# Application Power Nap : minuterie pour éteindre l'ordinateur automatiquement

class PowerNapApp(tk.Tk):
    # Classe principale de l'application
    def __init__(self):
        # Initialisation de la fenêtre principale
        super().__init__()
        self.title("Power Nap")  # Titre de la fenêtre
        self.geometry("420x320")  # Taille fixe
        self.resizable(False, False)
        self.configure(bg="#f5f6fa")  # Couleur de fond
        # Gestion du chemin des ressources (PyInstaller ou script)
        if hasattr(sys, '_MEIPASS'):
            resource_path = sys._MEIPASS
        else:
            resource_path = os.path.abspath('.')

        # Définir l'icône de l'application
        try:
            icon_path = os.path.join(resource_path, "logo.ico")
            print(f"[PowerNap] Chemin utilisé pour l'icône : {icon_path}")
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"[PowerNap] Erreur chargement icône : {e}")
            pass  # Si le logo n'est pas trouvé, ignorer

        # Variables d'état du minuteur
        self.timer_running = False  # Le minuteur est-il en cours ?
        self.timer_paused = False  # Le minuteur est-il en pause ?
        self.remaining_seconds = 2 * 3600  # Temps restant en secondes (2h par défaut)

        # Création des éléments de l'interface
        # Chargement des images pour les boutons (doivent être dans le dossier)
        try:
            self.start_img = tk.PhotoImage(file=os.path.join(resource_path, "start.png"))
            self.start_img = self.start_img.subsample(max(self.start_img.width() // 18, 1), max(self.start_img.height() // 18, 1))
        except Exception:
            self.start_img = None
        try:
            self.pause_img = tk.PhotoImage(file=os.path.join(resource_path, "pause.png"))
            self.pause_img = self.pause_img.subsample(max(self.pause_img.width() // 18, 1), max(self.pause_img.height() // 18, 1))
        except Exception:
            self.pause_img = None
        try:
            self.quit_img = tk.PhotoImage(file=os.path.join(resource_path, "quit.png"))
            self.quit_img = self.quit_img.subsample(max(self.quit_img.width() // 18, 1), max(self.quit_img.height() // 18, 1))
        except Exception:
            self.quit_img = None

        self.create_menu()      # Barre de menu
        self.create_toolbar()   # Barre d'outils
        self.create_main_area() # Zone principale (saisie temps + boutons)
        self.create_statusbar() # Barre d'état
        self.update_time_fields() # Affichage initial du temps
        self.update_buttons()     # État initial des boutons


    def create_menu(self):
        # Création de la barre de menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Quit - Alt+F4", command=self.on_quit)  # Option pour quitter
        menubar.add_cascade(label="File", menu=file_menu)

        # Ajout du menu Help
        help_menu = tk.Menu(menubar, tearoff=0)
        # Ajout de l'image help.png si disponible
        try:
            resource_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath('.')
            self.help_img = tk.PhotoImage(file=os.path.join(resource_path, "help.png"))
            # Ajuster la taille de l'image pour le menu (plus petit, ~24px max)
            target_size = 24
            w, h = self.help_img.width(), self.help_img.height()
            scale_w = max(w // target_size, 1)
            scale_h = max(h // target_size, 1)
            self.help_img = self.help_img.subsample(scale_w, scale_h)
            help_menu.add_command(label="Help - F1", image=self.help_img, compound="left", command=self.show_help)
        except Exception:
            self.help_img = None
            help_menu.add_command(label="Help -F1", command=self.show_help)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

        # Bind F1 to open help
        self.bind_all('<F1>', lambda event: self.show_help())

    def show_help(self):
        # Ouvre une fenêtre d'aide affichant le contenu de help.txt avec scrollbar, logo et focus
        help_win = tk.Toplevel(self)
        help_win.title("Help - Power Nap")
        help_win.geometry("500x500")
        help_win.resizable(True, True)
        # Définir l'icône si possible
        try:
            resource_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath('.')
            help_win.iconbitmap(os.path.join(resource_path, "logo.ico"))
        except Exception:
            pass
        # Frame principale
        main_frame = tk.Frame(help_win, bg="#f5f6fa")
        main_frame.pack(expand=True, fill=tk.BOTH)
        # Ajout d'une scrollbar
        scrollbar = tk.Scrollbar(main_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text = tk.Text(main_frame, wrap="word", font=("Segoe UI", 11), bg="#f5f6fa", yscrollcommand=scrollbar.set)
        text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        scrollbar.config(command=text.yview)
        # Charger le texte d'aide
        try:
            with open(os.path.join(resource_path, "help.txt"), encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = "Help file not found."
        text.insert("1.0", content)
        text.config(state="disabled")
        # Bouton pour fermer la fenêtre d'aide
        close_btn = ttk.Button(help_win, text="Close", command=help_win.destroy)
        close_btn.pack(pady=5)
        # Focus sur la fenêtre d'aide
        help_win.transient(self)
        help_win.grab_set()
        help_win.focus()

    def create_toolbar(self):
        # Création de la barre d'outils en haut
        toolbar = tk.Frame(self, bd=1, relief=tk.RAISED, bg="#dcdde1")
        ttk.Label(toolbar, text="Power Nap", font=("Segoe UI", 12, "bold"), background="#dcdde1").pack(side=tk.LEFT, padx=8, pady=4)
        toolbar.pack(side=tk.TOP, fill=tk.X)

    def create_main_area(self):
        # Zone principale : sélecteurs de temps et boutons
        main = tk.Frame(self, bg="#f5f6fa")
        main.pack(expand=True, fill=tk.BOTH, pady=(16, 0))

        # Sélecteurs de temps (heures, minutes, secondes)
        time_frame = tk.Frame(main, bg="#f5f6fa")
        time_frame.pack(pady=8)

        self.time_vars = {
            'hours': tk.IntVar(value=2),   # Heures
            'minutes': tk.IntVar(value=0), # Minutes
            'seconds': tk.IntVar(value=0)  # Secondes
        }

        for idx, (label, var) in enumerate(self.time_vars.items()):
            col = idx * 2
            box = tk.Frame(time_frame, bg="#f5f6fa")
            box.grid(row=0, column=col, padx=6)
            # Bouton flèche haut
            up_btn = ttk.Button(box, text="▲", width=2, command=lambda k=label: self.increment_time(k))
            up_btn.pack()
            # Champ de saisie (readonly)
            entry = ttk.Entry(box, textvariable=var, width=3, font=("Segoe UI", 16), justify="center")
            entry.pack(pady=2)
            entry.configure(state="readonly")
            # Bouton flèche bas
            down_btn = ttk.Button(box, text="▼", width=2, command=lambda k=label: self.decrement_time(k))
            down_btn.pack()
            # Libellé (Hours, Minutes, Seconds)
            ttk.Label(time_frame, text=label.capitalize(), background="#f5f6fa").grid(row=1, column=col, pady=(2,0))
            if idx < 2:
                # Deux-points entre les champs
                ttk.Label(time_frame, text=":", font=("Segoe UI", 16), background="#f5f6fa").grid(row=0, column=col+1, rowspan=2)

        # Boutons principaux (Start, Pause, +10 min, Quit)
        btn_frame = tk.Frame(main, bg="#f5f6fa")
        btn_frame.pack(pady=18)

        # Bouton Start avec icône
        if self.start_img:
            self.launch_btn = ttk.Button(btn_frame, text="Start", image=self.start_img, compound="left", width=10, command=self.start_timer)
        else:
            self.launch_btn = ttk.Button(btn_frame, text="Start", width=10, command=self.start_timer)
        self.launch_btn.grid(row=0, column=0, padx=6)

        # Bouton Pause avec icône
        if self.pause_img:
            self.pause_btn = ttk.Button(btn_frame, text="Pause", image=self.pause_img, compound="left", width=10, command=self.pause_timer, state=tk.DISABLED)
        else:
            self.pause_btn = ttk.Button(btn_frame, text="Pause", width=10, command=self.pause_timer, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=1, padx=6)

        # Bouton +10 min (pas d'icône demandée)
        self.add10_btn = ttk.Button(btn_frame, text="+ 10 min", width=10, command=self.add_10_minutes)  # +10 minutes
        self.add10_btn.grid(row=0, column=2, padx=6)

        # Bouton Quit avec icône
        if self.quit_img:
            self.quit_btn = ttk.Button(btn_frame, text="Quit", image=self.quit_img, compound="left", width=10, command=self.on_quit)
        else:
            self.quit_btn = ttk.Button(btn_frame, text="Quit", width=10, command=self.on_quit)
        self.quit_btn.grid(row=0, column=3, padx=6)

    def create_statusbar(self):
        # Création de la barre d'état en bas
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#dcdde1")
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def update_time_fields(self):
        # Met à jour l'affichage des champs de temps (toujours 2 chiffres)
        h, m, s = self.seconds_to_hms(self.remaining_seconds)
        # Always display two digits
        self.time_vars['hours'].set(f"{h:02d}")
        self.time_vars['minutes'].set(f"{m:02d}")
        self.time_vars['seconds'].set(f"{s:02d}")

    def increment_time(self, unit):
        # Incrémente la valeur d'un champ de temps
        h = int(self.time_vars['hours'].get())
        m = int(self.time_vars['minutes'].get())
        s = int(self.time_vars['seconds'].get())
        if unit == 'hours':
            h = min(h + 1, 23)
        elif unit == 'minutes':
            m = (m + 1) % 60
        elif unit == 'seconds':
            s = (s + 1) % 60
        self.time_vars['hours'].set(f"{h:02d}")
        self.time_vars['minutes'].set(f"{m:02d}")
        self.time_vars['seconds'].set(f"{s:02d}")
        self.sync_time_vars_to_seconds()

    def decrement_time(self, unit):
        # Décrémente la valeur d'un champ de temps
        h = int(self.time_vars['hours'].get())
        m = int(self.time_vars['minutes'].get())
        s = int(self.time_vars['seconds'].get())
        if unit == 'hours':
            h = max(h - 1, 0)
        elif unit == 'minutes':
            m = (m - 1) % 60
        elif unit == 'seconds':
            s = (s - 1) % 60
        self.time_vars['hours'].set(f"{h:02d}")
        self.time_vars['minutes'].set(f"{m:02d}")
        self.time_vars['seconds'].set(f"{s:02d}")
        self.sync_time_vars_to_seconds()

    def sync_time_vars_to_seconds(self):
        # Synchronise les champs de temps avec la variable en secondes
        h = int(self.time_vars['hours'].get())
        m = int(self.time_vars['minutes'].get())
        s = int(self.time_vars['seconds'].get())
        total_seconds = h * 3600 + m * 60 + s
        if total_seconds > 5 * 3600:
            messagebox.showwarning("Warning", "Maximum allowed time is 5 hours.")
            h, m, s = 5, 0, 0
            total_seconds = 5 * 3600
            self.time_vars['hours'].set(f"05")
            self.time_vars['minutes'].set(f"00")
            self.time_vars['seconds'].set(f"00")
        self.remaining_seconds = total_seconds
        self.update_time_fields()

    def seconds_to_hms(self, total):
        # Convertit un nombre de secondes en (heures, minutes, secondes)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return h, m, s

    def start_timer(self):
        # Démarre ou relance le compte à rebours
        if self.remaining_seconds == 0:
            messagebox.showinfo("Info", "Set a time greater than 0.")
            return
        if not self.timer_running:
            self.timer_running = True
            self.timer_paused = False
            self.status_var.set("Timer running...")
            self.update_buttons()
            threading.Thread(target=self.run_timer, daemon=True).start()
        elif self.timer_paused:
            self.timer_paused = False
            self.status_var.set("Timer running...")
            self.update_buttons()

    def pause_timer(self):
        # Met en pause le compte à rebours
        if self.timer_running and not self.timer_paused:
            self.timer_paused = True
            self.status_var.set("Paused")
            self.update_buttons()

    def add_10_minutes(self):
        # Ajoute 10 minutes au temps restant
        self.remaining_seconds += 600
        self.update_time_fields()
        if self.timer_running:
            self.status_var.set("+10 minutes added")

    def run_timer(self):
        # Boucle du compte à rebours (thread séparé)
        while self.timer_running and self.remaining_seconds > 0:
            if self.timer_paused:
                time.sleep(0.2)
                continue
            time.sleep(1)
            self.remaining_seconds -= 1
            self.update_time_fields()
        if self.remaining_seconds <= 0 and self.timer_running:
            self.status_var.set("Shutting down...")
            self.shutdown_computer()
        self.timer_running = False
        self.timer_paused = False
        self.update_buttons()
        self.status_var.set("Ready")

    def update_buttons(self):
        # Met à jour l'état (enabled/disabled) des boutons selon l'état du minuteur
        if self.timer_running and not self.timer_paused:
            self.launch_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
        elif self.timer_running and self.timer_paused:
            self.launch_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
        else:
            self.launch_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)

    def shutdown_computer(self):
        # Éteint l'ordinateur (Windows ou Linux)
        if os.name == 'nt':
            os.system("shutdown /s /t 0")
        else:
            os.system("shutdown -h now")

    def on_quit(self):
        # Gestion de la fermeture de l'application
        if self.timer_running:
            if not messagebox.askokcancel("Quit", "Timer is running. Quit anyway?"):
                return
        self.destroy()

if __name__ == "__main__":
    # Point d'entrée de l'application
    app = PowerNapApp()
    app.mainloop()
