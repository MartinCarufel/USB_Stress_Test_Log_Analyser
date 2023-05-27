import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from log_parser import *
import argparse
import shutil
import os

class main_app(tk.Tk):
    def __init__(self):
        super().__init__()

        self.DIR_ROW = 0
        self.FILE_ROW = self.DIR_ROW + 3
        self.TEXT_BOX_ROW = self.FILE_ROW + 2
        self.PROCESS_ROW = self.TEXT_BOX_ROW + 1

        self.dir_entry_var = tk.StringVar()
        self.file_entry_var = tk.StringVar()
        self.file_ext_entry_var = tk.StringVar()

        self.dir_label = tk.Label(self, text="Directory", justify="right", anchor="e")
        self.dir_label.grid(row=self.DIR_ROW, column=0, padx=5, pady=5, sticky=tk.E)
        self.dir_entry = tk.Entry(self, width=110, textvariable=self.dir_entry_var)
        self.dir_entry.grid(row=self.DIR_ROW, column=1, padx=0, pady=5, ipady=2, sticky=tk.W)
        self.dir_browse_button = tk.Button(self, text="Browse", anchor="w",
                                           command=lambda: self.browse(filedialog.askdirectory, self.dir_entry_var))
        self.dir_browse_button.grid(row=self.DIR_ROW, column=1, padx=(675, 10), pady=5, sticky=tk.W)
        self.file_ext_lbl = tk.Label(self, text="File Ext.", justify="right", anchor="e")
        self.file_ext_lbl.grid(row=self.DIR_ROW+1, column=0, padx=5, pady=5, sticky=tk.E)
        self.file_ext_entry = tk.Entry(self, width=30, textvariable=self.file_ext_entry_var)
        self.file_ext_entry.grid(row=self.DIR_ROW+1, column=1, padx=0, pady=5, ipady=2, sticky=tk.W)
        self.add_all_button = tk.Button(self, text="Add All", command=self.add_all_corresponding_file)
        self.add_all_button.grid(row=self.DIR_ROW+1, column=1, padx=190, sticky=tk.W)
        self.ext_entry_example = tk.Label(self,
                                          text="Enter extension of the file to add, separate by comma ex: .log, .txt ")
        self.ext_entry_example.grid(row=self.DIR_ROW+1, column=1, padx=(250, 0), sticky=tk.W)

        self.spacer_row = tk.Label(self, text="").grid(row=self.DIR_ROW+2, column=0)

        self.file_label = tk.Label(self, text="File", justify="right", anchor="e")
        self.file_label.grid(row=self.FILE_ROW, column=0, padx=5, pady=5, sticky=tk.E)
        self.file_entry = tk.Entry(self, width=110, textvariable=self.file_entry_var)
        self.file_entry.grid(row=self.FILE_ROW, column=1, padx=0, pady=5, ipady=2, sticky=tk.W)
        # self.file_browse_button = tk.Button(self, text="Browse", command=lambda: self.browse("filedialog.askdirectory", "variable"))
        self.file_browse_button = tk.Button(self, text="Browse",
                                            command=lambda: self.browse(filedialog.askopenfilenames, self.file_entry_var))
        self.file_browse_button.grid(row=self.FILE_ROW, column=1, padx=(675, 10), pady=5, sticky=tk.W)
        self.add_file_button = tk.Button(self, text="Add file", command=self.add_file)
        self.add_file_button.grid(row=self.FILE_ROW + 1, column=1, padx=190, sticky=tk.W)

        self.file_box = tk.Text(self, width=90, height=10)
        self.file_box.grid(row=self.TEXT_BOX_ROW, column=1, pady=10, sticky=tk.W)

        self.process_button = tk.Button(self, text="Process", command=self.process)
        self.process_button.grid(row=self.PROCESS_ROW, column=1, padx=40, pady=5)


    def browse(self, command, variable):
        print(f"{command}")
        # self.dir_path = filedialog.askdirectory()
        self.dir_path = command()
        variable.set(self.dir_path)
        pass

    def add_all_corresponding_file(self):
        self.ext_list = self.file_ext_entry_var.get().split(",")
        self.ext_list = [x.strip() for x in self.ext_list]

        for ext in self.ext_list:
            pattern = ext
            for file in os.listdir(self.dir_path):
                if re.search(ext, file) != None:
                    self.file_box.insert(tk.END, self.dir_path + "/" + file + "\n")
                    print(self.dir_path + "/" + pattern)
                    # tf.writelines(path + "/" + file + "\n")

        print(self.ext_list)
        pass

    def add_file(self):
        print(self.file_entry_var.get())
        char_to_strip = ["(", ")", " ", ",", "'"]
        files = self.file_entry_var.get().split(", ")
        for file in files:
            for ch in char_to_strip:
                file = file.strip(ch)

            self.file_box.insert(tk.END, file + "\n")
        pass

    def create_file_list_from_text_box(self):
        files_list_clean = []
        self.files_list = self.file_box.get("1.0", "end").split("\n")
        for file in self.files_list:
            if file != "":
                files_list_clean.append(file)
        return files_list_clean
    def process(self):
        usb_err_summary = []
        messagebox.showwarning(title="Warning", message="Previous result data will be erase/overwrite")
        shutil.rmtree('result', ignore_errors=True)
        os.mkdir("./result/")
        file_list = self.create_file_list_from_text_box()
        for file in file_list:
            reg_ex = 'IO-[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]'  # Find in path/file the IO serial
            hp_serial = re.search(pattern=reg_ex, string=file).group()

            reg_ex_hpc = 'DWIOK-[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]'
            try:
                hpc_serial = re.search(pattern=reg_ex_hpc, string=file).group()
            except AttributeError:
                hpc_serial = "SN not Found"

            print("Process the log for HP {}.".format(hp_serial))
            usb_err_summary.append(check_for_usb_error(file))
            csv_data = extract_stress_test_data(file)  # CSV_data are a python table
            df = convert_listcsv_to_dataframe(csv_data, file)
            summary = compile_test_data_per_minute(df, get_file_name(file))  # return dataframe
            create_test_result_summary_csv(hp_serial, summary, hpc_serial)
            check_for_usb_error_v2(file, hp_serial, hpc_serial)

        tk.messagebox.showinfo("Done", message="Completed")


app = main_app()
app.mainloop()