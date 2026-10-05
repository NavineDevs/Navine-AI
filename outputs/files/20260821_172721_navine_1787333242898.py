import tkinter as tk


def main():
    root = tk.Tk()
    root.title("Hello World")
    root.geometry("320x160")
    label = tk.Label(root, text="Hello World", font=("Segoe UI", 16))
    label.pack(expand=True, padx=20, pady=20)
    root.mainloop()


if __name__ == "__main__":
    main()
