import tkinter as tk
from customtkinter import *
from tkinter import messagebox
from tkinter import simpledialog
import paho.mqtt.client as mqtt
import json
import time
import random
import os

CURRENT_CONFIG_NAME = ''
FACTOR = 1

# Determine the base path for the application
if hasattr(sys, '_MEIPASS'):
    basedir = sys._MEIPASS
else:
    basedir = os.path.abspath(os.path.dirname(__file__))


class MQTTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Publisher")
        set_appearance_mode("Dark")

        icon_path = r'rocket-lunch.png'

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.root.iconphoto(False, tk.PhotoImage(file=os.path.join(basedir, icon_path)))

        # Store configurations
        self.config_file = os.path.join(basedir, "mqtt_configurations.json")
        self.configurations = {}
        self.current_config = None

        # Configuration sidebar
        self.sidebar = CTkFrame(root, width=200, corner_radius=10, bg_color='lightgrey')
        self.sidebar.grid(row=0, column=0, rowspan=8, sticky='ns')
        self.sidebar.grid_propagate(False)

        self.config_listbox = tk.Listbox(self.sidebar, state=tk.NORMAL)
        self.config_listbox.pack(fill=tk.BOTH, expand=True)
        self.config_listbox.bind('<<ListboxSelect>>', self.load_config)

        # Update the configuration listbox with loaded configurations
        self.update_config_listbox()

        # Load configurations from file
        self.load_configurations()

        # Add Configuration Button
        self.add_config_button = CTkButton(self.sidebar, text="Add Configuration", command=self.add_configuration)
        self.add_config_button.pack(fill=tk.X, padx=5, pady=5)

        # Main frame
        self.main_frame = CTkFrame(root, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=10, pady=5, sticky='n')

        # Broker Address
        self.broker_label = CTkLabel(self.main_frame, text="MQTT Broker Address:")
        self.broker_label.grid(row=0, column=0, padx=10, pady=5)
        self.broker_entry = CTkEntry(self.main_frame)
        self.broker_entry.grid(row=0, column=1, padx=10, pady=5)

        # Port
        self.port_label = CTkLabel(self.main_frame, text="Port:")
        self.port_label.grid(row=0, column=2, padx=10, pady=5)
        self.port_entry = CTkEntry(self.main_frame)
        self.port_entry.grid(row=0, column=3, padx=10, pady=5)

        # Username
        self.username_label = CTkLabel(self.main_frame, text="Username:")
        self.username_label.grid(row=1, column=0, padx=10, pady=5)
        self.username_entry = CTkEntry(self.main_frame)
        self.username_entry.grid(row=1, column=1, padx=10, pady=5)

        # Password
        self.password_label = CTkLabel(self.main_frame, text="Password:")
        self.password_label.grid(row=1, column=2, padx=10, pady=5)
        self.password_entry = CTkEntry(self.main_frame, show="*")
        self.password_entry.grid(row=1, column=3, padx=10, pady=5)

        # Topic
        self.topic_label = CTkLabel(self.main_frame, text="Topic:")
        self.topic_label.grid(row=2, column=0, padx=10, pady=5)
        self.topic_entry = CTkEntry(self.main_frame)
        self.topic_entry.grid(row=2, column=1, padx=10, pady=5)

         # Send Frequency
        self.freq_label = CTkLabel(self.main_frame, text="Send Frequency (ms):")
        self.freq_label.grid(row=2, column=2, padx=10, pady=5)
        self.freq_entry = CTkEntry(self.main_frame)
        self.freq_entry.grid(row=2, column=3, padx=10, pady=5)

        # Message section
        self.message_frame = CTkFrame(self.main_frame)
        self.message_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=5)

        self.fields = []

        # Add Field Button
        self.add_field_button = CTkButton(self.main_frame, text="Add Field", command=self.add_field)
        self.add_field_button.grid(row=4, column=0, padx=10, pady=10)

        # Connect Button
        self.connect_button = CTkButton(self.main_frame, text="Connect", command=self.connect)
        self.connect_button.grid(row=4, column=1, padx=10, pady=10)

        # Latest Message Display
        self.latest_message_label = CTkLabel(self.main_frame, text="Latest Message:", font=("Helvetica", 12, "bold"))
        self.latest_message_label.grid(row=6, column=0, padx=10, pady=5, columnspan=4)

        self.latest_message_box = tk.Text(self.main_frame, height=10, width=50, wrap=tk.WORD)
        self.latest_message_box.grid(row=7, column=0, columnspan=4, padx=10, pady=5)

        # Continuous Publishing Variables
        self.running = False
        self.timer = None

        # Start and Stop Buttons
        self.start_button = CTkButton(self.main_frame, text="Start Publishing", command=self.start_publishing, state=tk.DISABLED)
        self.start_button.grid(row=4, column=2, padx=10, pady=10)

        self.stop_button = CTkButton(self.main_frame, text="Stop Publishing", command=self.stop_publishing, state=tk.DISABLED)
        self.stop_button.grid(row=4, column=3, padx=10, pady=10)

        self.new_connection_button = CTkButton(self.main_frame, text="New Connection", command=self.new_connection)
        self.new_connection_button.grid(row=5, column=1, padx=10, pady=10)

        self.update_button = CTkButton(self.main_frame, text="Update", command=self.save_config)
        self.update_button.grid(row=5, column=2, padx=10, pady=10)

        self.delete_button = CTkButton(self.main_frame, text="Delete", command=self.delete_config)
        self.delete_button.grid(row=5, column=3, padx=10, pady=10)


    def add_field(self):
        field_index = len(self.fields) + 1
        frame = CTkFrame(self.message_frame)
        frame.pack(fill='x', pady=2)

        label = CTkLabel(frame, text=f"Field {field_index}: Min")
        label.pack(side='left', padx=5)

        min_entry = CTkEntry(frame)
        min_entry.pack(side='left', padx=5)

        label = CTkLabel(frame, text="Max")
        label.pack(side='left', padx=5)

        max_entry = CTkEntry(frame)
        max_entry.pack(side='left', padx=5)

        # Remove Button
        remove_button = CTkButton(frame, text="Remove", command=lambda f=frame: self.remove_field(f))
        remove_button.pack(side='right', padx=5)

        self.fields.append((field_index, min_entry, max_entry, frame))

    def remove_field(self, frame_to_remove):
        frame_to_remove.destroy()  # Destroy the frame
        # Filter out the removed field based on frame reference
        self.fields = [field for field in self.fields if field[3] != frame_to_remove]  # Update fields list

    def connect(self):
        broker = self.broker_entry.get()
        port = self.port_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not port.isdigit():
            messagebox.showerror("Connection Error", "Port must be a number")
            return

        try:
            self.client.username_pw_set(username, password)
            self.client.connect(broker, int(port), keepalive=60)
            self.client.loop_start()
            messagebox.showinfo("Connection", "Connected to MQTT Broker")
            self.start_button.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to MQTT Broker: {str(e)}")
    
    def new_connection(self):
        self.reload_gui()  # Reload the GUI after deletion

    def publish_continuously(self):
        if self.running:
            self.publish()
            self.timer = self.root.after(int(self.freq_entry.get()), self.publish_continuously)

    def start_publishing(self):
        if not self.running:
            self.running = True
            self.start_button.configure(state="disabled")
            self.add_field_button.configure(state="disabled")
            self.new_connection_button.configure(state="disabled")
            self.update_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            self.add_config_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.config_listbox.config(state=tk.DISABLED)
            self.publish_continuously()

    def stop_publishing(self):
        if self.running:
            self.running = False
            self.root.after_cancel(self.timer)
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.start_button.configure(state="normal")
            self.add_field_button.configure(state="normal")
            self.new_connection_button.configure(state="normal")
            self.update_button.configure(state="normal")
            self.delete_button.configure(state="normal")
            self.add_config_button.configure(state="normal")
            self.config_listbox.config(state=tk.NORMAL)

    def publish(self):
        global FACTOR
        topic = self.topic_entry.get()
        message_data = {}
        current_time = int(time.time())

        for field_info in self.fields:
            index, min_entry, max_entry, frame = field_info
            try:
                min_value = float(min_entry.get())
                max_value = float(max_entry.get())
                if min_value >= max_value:
                    raise ValueError(f"Min value should be less than Max value for field {index}")

                value = random.uniform(min_value, max_value) * FACTOR
                message_data[str(index)] = [{"t": current_time, "v": value}]
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
                return

        message_json = json.dumps(message_data)
        try:
            self.client.publish(topic, message_json)
            self.update_latest_message(message_json)  # Update latest message box
        except Exception as e:
            messagebox.showerror("Publish Error", str(e))

    def update_latest_message(self, message):
        self.latest_message_box.delete("1.0", tk.END)  # Clear the textbox
        self.latest_message_box.insert(tk.END, message)  # Insert the latest message
    
    def save_configurations(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.configurations, f, indent=4)


    def load_configurations(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.configurations = json.load(f)
            self.update_config_listbox()
        else:
            self.configurations = {}

    def save_config(self):
        global CURRENT_CONFIG_NAME
        if CURRENT_CONFIG_NAME:
            config_data = {
                "broker": self.broker_entry.get(),
                "port": self.port_entry.get(),
                "username": self.username_entry.get(),
                "password": self.password_entry.get(),
                "topic": self.topic_entry.get(),
                "frequency": self.freq_entry.get(),
                "fields": [(min_entry.get(), max_entry.get()) for _, min_entry, max_entry, _ in self.fields]
            }
            self.configurations[CURRENT_CONFIG_NAME] = config_data
            self.update_config_listbox()
            self.save_configurations()  # Save configurations to file
        else:
            messagebox.showerror("Error", "No configuration selected.")


    def delete_config(self):
        global CURRENT_CONFIG_NAME
        if CURRENT_CONFIG_NAME:
            del self.configurations[CURRENT_CONFIG_NAME]
            CURRENT_CONFIG_NAME = ''  # Reset current config name
            self.update_config_listbox()
            self.save_configurations()  # Save configurations to file
            self.reload_gui()  # Reload the GUI after deletion
        else:
            messagebox.showerror("Error", "No configuration selected.")

    def add_configuration(self):
        config_name = simpledialog.askstring("Configuration Name", "Enter a name for this configuration:")
        if config_name:
            config_data = {
                "broker": self.broker_entry.get(),
                "port": self.port_entry.get(),
                "username": self.username_entry.get(),
                "password": self.password_entry.get(),
                "topic": self.topic_entry.get(),
                "frequency": self.freq_entry.get(),
                "fields": [(min_entry.get(), max_entry.get()) for _, min_entry, max_entry, _ in self.fields]
            }
            self.configurations[config_name] = config_data
            self.update_config_listbox()
            self.save_configurations()  # Save configurations to file


    def load_config(self, event):
        global CURRENT_CONFIG_NAME
        selected_index = self.config_listbox.curselection()
        self.start_button.configure(state="disabled")
        if selected_index:
            selected_config = self.config_listbox.get(selected_index[0])
            if selected_config in self.configurations:
                CURRENT_CONFIG_NAME = selected_config  # Set current config name
                config_data = self.configurations[selected_config]
                self.broker_entry.delete(0, tk.END)
                self.broker_entry.insert(0, config_data["broker"])
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, config_data["port"])
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, config_data["username"])
                self.password_entry.delete(0, tk.END)
                self.password_entry.insert(0, config_data["password"])
                self.topic_entry.delete(0, tk.END)
                self.topic_entry.insert(0, config_data["topic"])
                self.freq_entry.delete(0, tk.END)
                self.freq_entry.insert(0, config_data["frequency"])

                for _, _, _, frame in self.fields:
                    frame.destroy()
                self.fields.clear()

                for min_value, max_value in config_data["fields"]:
                    self.add_field()
                    min_entry = self.fields[-1][1]
                    max_entry = self.fields[-1][2]
                    min_entry.insert(0, min_value)
                    max_entry.insert(0, max_value)
        


    def update_config_listbox(self):
        self.config_listbox.delete(0, tk.END)
        for config_name in self.configurations:
            self.config_listbox.insert(tk.END, config_name)

    def reload_gui(self):
        self.broker_entry.delete(0, tk.END)
        self.port_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.topic_entry.delete(0, tk.END)
        self.freq_entry.delete(0, tk.END)
        self.start_button.configure(state="disabled")

        for _, _, _, frame in self.fields:
            frame.destroy()
        self.fields.clear()

        self.update_latest_message("")  # Clear latest message box

    def on_closing(self):
        self.save_configurations()  # Save configurations to file on closing
        if self.client.is_connected():
            self.client.disconnect()
        self.client.loop_stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

