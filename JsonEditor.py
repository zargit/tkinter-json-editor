import tkinter as tk
from tkinter import ttk
import collections
import json
from tkinter import simpledialog as sd
from tkinter import filedialog as fd
from tkinter import messagebox as mb

"""
Layout:
-master
 |--wrapper
 |  |--header_wrapper
 |  |  |--title
 |  |  |--expand_all
 |  |  |--new_json_btn
 |  |  |--new_json_file_btn
 |  |  |--load_json_file_btn
 |  |--body_wrapper
 |  |  |--tree

"""


class ValueTypes:
    DICT = 1
    LIST = 2
    STR = 3
    FILEPATH = 4


class Tags:
    DICT = 'dict'
    LIST = 'list'
    ROOT = 'root'
    LEAF = 'leaf'
    FILE = 'file'


class JsonEditor:

    def __init__(self, master, **options):

        self.popup_menu_actions = collections.OrderedDict()  # Format: {'id':{'text':'','action':function}, ...}

        if not options.get("readonly"):

            self.popup_menu_actions['add_child_dict'] = {'text': 'Add Dict',
                                                         'action': lambda: self.add_item_from_input(ValueTypes.DICT)}

            self.popup_menu_actions['add_child_list'] = {'text': 'Add List',
                                                         'action': lambda: self.add_item_from_input(ValueTypes.LIST)}

            self.popup_menu_actions['add_child_value'] = {'text': 'Add Value',
                                                          'action': lambda: self.add_item_from_input(ValueTypes.STR)}

            self.popup_menu_actions['add_child_filepath'] = {'text': 'Add Filepath',
                                                             'action': lambda: self.add_item_from_input(ValueTypes.FILEPATH)}

            self.popup_menu_actions['edit_child'] = {'text': 'Edit',
                                                     'action': lambda: self.edit_item_from_input()}

            self.popup_menu_actions['remove_child'] = {'text': 'Remove',
                                                       'action': lambda: self.remove_item_from_input(self.get_selected_index())}

        wrapper = ttk.Frame(master)
        wrapper.pack(fill=tk.BOTH, expand=True)

        header_wrapper = ttk.Frame(wrapper)
        header_wrapper.pack(fill=tk.X)

        self.title = tk.StringVar()
        ttk.Label(header_wrapper, textvariable=self.title).pack(side=tk.LEFT, anchor=tk.N)

        ttk.Button(header_wrapper,
                   text="Load JSON File",
                   command=lambda: self.load_json_from_file(fd.askopenfilename())).pack(side=tk.RIGHT)

        if not options.get("readonly"):
            ttk.Button(header_wrapper,
                       text="New JSON File",
                       command=lambda: self.create_empty_json_file(fd.asksaveasfilename())).pack(side=tk.RIGHT)

            ttk.Button(header_wrapper,
                       text="New JSON",
                       command=lambda: self.create_json_from_data(sd.askstring("JSON name?", "name = "), {})).pack(side=tk.RIGHT)

        self.show_detail = tk.IntVar()
        self.show_detail.set(0)
        ttk.Checkbutton(header_wrapper, text="Expand All", variable=self.show_detail, onvalue=1, offvalue=0,
                        command=self.toggle_detail_view).pack(side=tk.RIGHT)

        body_wrapper = ttk.Frame(wrapper)
        body_wrapper.pack(fill=tk.BOTH, expand=True)
        body_wrapper.columnconfigure(0, weight=1)
        body_wrapper.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(body_wrapper, selectmode='browse')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind('<Button-3>', lambda event: self.show_popup_menu(event))

        self.tree.item('', tags=[Tags.DICT])
        self.tree.tag_configure(Tags.ROOT, background='yellow')

        yscroll = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.configure(yscrollcommand=yscroll.set)

        self.set_columns()

        self.popup_menu = tk.Menu(self.tree, tearoff=0)
        self.update_popup_menu()

    def toggle_detail_view(self):
        """
        This function toggles between expanding the tree and closing it.
        """
        if self.show_detail.get():
            childrens = self.tree.get_children()
            for child in childrens:
                self.expand_item(child)
        else:
            childrens = self.tree.get_children()
            for child in childrens:
                self.close_item(child)

    def set_title(self, title):
        """
        :param title: Its a <str> object.
        """
        self.title.set(title)

    def set_columns(self, columns=('Key', 'Value')):
        """
        Sets the column headings with the given column tuple.
        :param columns: A <tuple> containing <str> objects.
        """
        col_ids = ['#'+str(i) for i in range(len(columns)-1)]
        self.tree.configure(column=col_ids)
        for i in range(len(columns)):
            self.tree.heading('#'+str(i), text=columns[i])

    def set_action_item_selected(self, action):
        """
        :param action: Its a function, the format must be action(selected_item).
        """
        self.tree.bind("<<TreeviewSelect>>", lambda event: action(self.get_selected_index()))

    def set_action_item_opened(self, action):
        """
        :param action: Its a function, the format must be action(selected_item).
        """
        self.tree.bind("<<TreeviewOpen>>", lambda event: action(self.get_selected_index()))

    def set_action_item_closed(self, action):
        """
        :param action: Its a function, the format must be action(selected_item).
        """
        self.tree.bind("<<TreeviewClose>>", lambda event: action(self.get_selected_index()))

    def add_popup_menu_action(self, menu_id, action, text=None):
        """
        This function allows the controller to add custom popup menu actions.
        :param menu_id: Unigue id for the menu.
        :param action: The function execute for this menu event.
        :param text: Display text for menu, default is menu_id.
        """
        self.popup_menu_actions[menu_id] = {'text': text or menu_id, 'action': action}
        self.update_popup_menu()

    def expand_item(self, index):
        """
        Expands the existing item and its children.
        :param index: Its a <tk.Treeview> node object. Acting as a root.
        """
        self.tree.item(index, open=True)
        childrens = self.tree.get_children([index])

        if len(childrens) > 0:
            for child in childrens:
                self.expand_item(child)

    def close_item(self, index):
        """
        Closes the existing item and its children.
        :param index: Its a <tk.Treeview> node object. Acting as a root.
        """
        childrens = self.tree.get_children([index])

        if len(childrens) > 0:
            for child in childrens:
                self.close_item(child)

        self.tree.item(index, open=False)

    def populate_item(self, key, value, node='', tags=[]):
        """
        Performs a recursive traversal to populate the item tree starting from given node.
        Each item is a key-value pair. Root node is defined by node=''.
        :param key: A <str> key, can be <int> in absence of a key, for example list items.
        :param value: It can be any of the primitive data type.
        :param node: Initially '', otherwise a <tk.Treeview> node object.
        """
        if node == '':
            tags = tags+[Tags.ROOT]

        if type(value) is dict:
            node = self.tree.insert(node, tk.END, text=str(key)+'={}', tags=tags+[Tags.DICT])
            for k in value:
                self.populate_item(k, value[k], node)
        elif type(value) is list:
            node = self.tree.insert(node, tk.END, text=str(key)+'=[]', tags=tags+[Tags.LIST])
            for k in range(len(value)):
                self.populate_item(k, value[k], node)
        else:
            self.tree.insert(node, tk.END, text=str(key), tags=tags+[Tags.LEAF], values=[value])

    def add_item(self, key, value, parent='', tags=[]):
        """
        Adds a new item at the selected parent item.
        :param key: A <str> key for the new item.
        :param value: A value.
        :param parent: The parent under which the new item will be added.
        '' means absolute root, json roots are direct children of it.
        """
        self.populate_item(key, value, parent, tags)
        if parent == '':
            return
        json_root = self.get_json_root(parent)
        if self.tree.tag_has(Tags.FILE, json_root):
            self.save_json_file(self.get_json_filepath(json_root), self.get_value(json_root))

    def add_item_from_input(self, vtype=ValueTypes.STR):
        """
        :param vtype: A <int> value from ValueTypes. Determines what input to take.
        """
        parent = self.get_selected_index()

        if self.verify_selection(Tags.DICT):

            key = sd.askstring("Input", "key = ").strip()

            if not key: return

            value = None

            if vtype == ValueTypes.STR:
                value = sd.askstring("Input String Value", "value = ").strip()
            elif vtype == ValueTypes.DICT:
                value = {}
            elif vtype == ValueTypes.LIST:
                value = []
            elif vtype == ValueTypes.FILEPATH:
                value = fd.askopenfilename()

            if key and value is not None:
                self.add_item(key, value, parent)

        elif self.verify_selection(Tags.LIST):

            value = None

            if vtype == ValueTypes.STR:
                value = sd.askstring("Input String Value", "value = ")
            elif vtype == ValueTypes.DICT:
                value = {}
            elif vtype == ValueTypes.LIST:
                value = []
            elif vtype == ValueTypes.FILEPATH:
                value = fd.askopenfilename()

            if value is not None:
                self.add_item(len(self.tree.get_children(parent)), value, parent)

        else:
            # Leaf node in selection, change selection and call method again
            self.tree.selection_set(self.tree.parent(parent))  # Changing selection to parent
            self.add_item_from_input(type)

    def edit_item(self, index, key=None, value=None):
        """
        Updates the existing item with the new key and value at index.
        :param index: Existing item index.
        :param key: A <str>, the new key.
        :param value: A <str>, the new value.
        :return: In case of absolute root this function does not do anything and returns empty.
        """
        if key:
            self.tree.item(index, text=key)

        if value:
            self.tree.item(index, values=[value])

        if index == '':
            return
        json_root = self.get_json_root(index)
        if self.tree.tag_has(Tags.FILE, json_root):
            self.save_json_file(self.get_json_filepath(json_root), self.get_value(json_root))

    def edit_item_from_input(self):
        """
        Allows editing of key and value in case of a <dict> item and only value in case of <list> item.
        """
        selection = self.get_selected_index()

        is_parent_dict = self.tree.tag_has(Tags.DICT, self.tree.parent(selection))
        is_leaf = self.tree.tag_has(Tags.LEAF, selection)

        if is_parent_dict and mb.askyesno("Confirm?", "Edit key?"):
            key = sd.askstring("Key Input", "new key = ")

            if self.verify_key(key):
                if self.tree.tag_has(Tags.DICT, selection):
                    key += '={}'
                elif self.tree.tag_has(Tags.LIST, selection):
                    key += '=[]'

            self.edit_item(selection, key=key)

        if is_leaf and mb.askyesno("Confirm?", "Edit Value?"):
            value = sd.askstring("Value Input", "new value = ")
            if self.verify_value(value):
                self.edit_item(selection, value=value)

    def remove_item(self, index):
        """
        :param index: Removes the item at index and its children from the list.
        """
        self.tree.delete([index])

    def remove_item_from_input(self, index):
        """
        :param index: Removes the item at index and its children from the list.
        Does not remove a json root item, instead removes all its children.
        """

        json_root = self.get_json_root(index)

        if index == json_root:
            for item in self.tree.get_children(index):
                self.remove_item(item)
        else:
            self.remove_item(index)

        if self.tree.tag_has(Tags.FILE, json_root):
            self.save_json_file(self.get_json_filepath(json_root), self.get_value(json_root))

    def remove_all_item(self):
        """
        :return: Removes all item from the tree.
        """
        # self.tree.delete([''])  # '' is the absolute root node # This is buggy in the treeview
        for child in self.tree.get_children():
            self.remove_item(child)

    def load_json_from_file(self, filepath):
        """
        :param filepath: An absolute filepath to the json file.
        :return: The <dict> object parsed from the json file.
        """
        data = {}
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.add_item(f.name, data, tags=[Tags.FILE])
        except FileNotFoundError():
            print(e)
        return data

    def create_empty_json_file(self, filepath):
        """
        :param filepath: An absolute filepath to create the json file.
        :return: The <dict> object parsed from the json file.
        """
        self.save_json_file(filepath, {})
        return self.load_json_from_file(filepath)

    def create_json_from_data(self, name, data):
        """
        Creates a new json root with given data.
        :param name: A <str> object, name of the new json root.
        :param data: A <dict> object.
        """
        if self.verify_key(name):
            self.add_item(name, data)

    def save_json_file(self, filepath, data):
        """
        :param filepath: An absolute filepath to save the json file.
        :param data: A <dict> object.
        """
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def get_selected_index(self):
        """
        :return: Returns the currently selected/focused item from the list.
        """
        return self.tree.selection()

    def get_json_root(self, index):
        """
        This function traverses up until finding an item with Tags.ROOT and returns.
        :param index: An item index in the tree.
        :return: The corresponding json root index.
        """
        if index == '': return None
        if self.tree.tag_has(Tags.ROOT, index):
            return index
        return self.get_json_root(self.tree.parent(index))

    def get_json_filepath(self, index):
        """
        The key of the json root item is the absolute filepath of the json file.
        In future version this might change.
        :param index: The item index for which the filepath is asked.
        :return: The absolute filepath.
        """
        return self.get_key(self.get_json_root(index))

    def get_key(self, index):
        """
        Extracts the tree from the node text.
        :param index: Node index.
        :return: The key <str> object.
        """
        item = self.tree.item(index)
        key = item['text']
        if self.tree.tag_has(Tags.DICT, index) or self.tree.tag_has(Tags.LIST, index):
            key = item['text'].split('=')[0].strip()
        return key

    def get_value(self, index):
        """
        This functions traverses down the tree and returns all the values.
        :param index: Its a <tk.Treeview> node object. Acting as a root.
        :return: The value object.
        """
        item = self.tree.item(index)
        value = None
        if self.tree.tag_has(Tags.DICT, index):
            value = {}
            child_nodes = self.tree.get_children(index)
            for child in child_nodes:
                value[self.get_key(child)] = self.get_value(child)
        elif self.tree.tag_has(Tags.LIST, index):
            value = []
            child_nodes = self.tree.get_children(index)
            for child in child_nodes:
                value.append(self.get_value(child))
        else:
            value = item['values'][0]
        return value

    def get_key_value_pair(self, index):
        """
        :param index: A tkinter index, either <int> or <str>.
        :return: A tuple of (key, value) format.
        """
        return self.get_key(index), self.get_value(index)

    def show_popup_menu(self, event):
        """
        Pops up menu for controller defined actions.
        :param event: The event where <Button-3> was clicked.
        """
        self.tree.selection_set(self.tree.identify_row(event.y))  # Before popping up selecting the clicked item
        if self.get_selected_index():
            self.popup_menu.post(event.x_root, event.y_root)

    def update_popup_menu(self):
        """
        Updating the self.popup_menu object with actions defined in self.popup_menu_actions.
        """
        self.popup_menu.delete(0, tk.END)  # Delete old entries
        for key in self.popup_menu_actions:
            self.popup_menu.add_command(label=self.popup_menu_actions[key]['text'],
                                        command=self.popup_menu_actions[key]['action'])

    def verify_selection(self, expected=Tags.LEAF):
        """
        Checks whether currently selected item has the expected tag.
        :param expected: The expected tag, default is Tags.LEAF
        :return: Boolean
        """
        selection = self.get_selected_index()
        if self.tree.tag_has(expected, selection):
            return True
        return False

    def verify_key(self, key):
        if len(key.encode('utf-8')):
            return True
        return False

    def verify_value(self, value):
        if len(value.encode('utf-8')):
            return True
        return False