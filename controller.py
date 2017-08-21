import tkinter as tk
from JsonEditor import JsonEditor

if __name__ == '__main__':
    root = tk.Tk()
    editor = JsonEditor(root)
    editor.set_title('JSON Editor')
    root.mainloop()
