import tkinter as tk


def on_click(label):
    label.config(text="Button clicked")


def main():
    root = tk.Tk()
    root.title("Navine AI App")
    root.geometry("400x300")
    label = tk.Label(root, text="Hello from Navine AI", font=("Segoe UI", 12))
    label.pack(padx=20, pady=20)
    button = tk.Button(root, text="Click Me", command=lambda: on_click(label))
    button.pack(pady=10)
    root.mainloop()


if __name__ == "__main__":
    main()
