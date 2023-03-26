import pandas as pd
import re
import sys
import os
import shutil
from numpy import mean
import os.path
import argparse

result_path = "./result/"

def average(lst):
    return sum(lst) / len(lst)


def prog_setup():
    param_file_name = str(sys.argv[1])
    reg_ex = 'IO-[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]'    # Find in path/file the IO serial
    reg_ex_hpc = 'DWIOK-[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]'
    hp_serial = re.search(pattern=reg_ex, string=param_file_name).group()
    hpc_serial = re.search(pattern=reg_ex_hpc, string=param_file_name).group()
    return (param_file_name, hp_serial, hpc_serial)


def check_for_usb_error(input_file):
    """
    This function check for USB error. Take a text file and look for specific error string.

    """
    error_strings = ["Read to COM port failed with error code 995"]
    usb_error_count = 0
    # print(input_file)
    with open(input_file, mode='r') as f:
        for line in f:
            for error_str in error_strings:
                if re.match(error_str, line) is not None:
                    usb_error_count += 1
    return (input_file, usb_error_count)

def check_for_usb_error_v2(input_file, hp_serial, hpc_serial):
    """
    This function check for USB error. Take a text file and look for specific error string.

    """
    data_summary = open(result_path + "Data_summary.csv", mode='a')
    error_strings = {"Read to COM port failed with error code 995": 0,
                     "Write to COM port failed with error code 22": 0,
                     "USB error \(update gain CAM2_ID\): 1004": 0,
                     "Stop everything": 0,
                     "USB error \(stop_cam_sequencer\)": 0,
                     "Failed to read sensing head temperature": 0,
                     "Failed to stop low-power heater": 0,
                     "Failed to stop hi-power heater": 0,

                     }

    for error_str, err_count in error_strings.items():
        with open(input_file, mode='r') as f:
            for line in f:

                if re.search(str(error_str), line) is not None:
                    error_strings[error_str] += 1

    for error_str, err_count in error_strings.items():
        data_summary.write(hpc_serial + ',' + hp_serial + ',' + error_str + ',' + str(err_count) + "\n")

    return error_strings


def extract_table_header_from_log(input_log):
    match_string = "\| *Start Capture Loop *\|"
    pattern_string = re.compile(match_string)
    match_sep = " *\| *"
    pattern_sep = re.compile(match_sep)
    header_location = 0
    with open(input_log, mode='r') as f:
        for count, line in enumerate(f):
            if pattern_string.match(line) is not None:
                header_location = count
            if count == header_location+2:
                header = re.sub(pattern=pattern_sep, repl=",", string=line[:-2])
                header = header.split(sep=',')[1:]
    return header


def extract_stress_test_data(input_file):
    """
    This function get in input the file output log from the USB Stress test in format text
    and convert only the test result data second per second into a two dim list of CSV string. Each column are splits
    with comma.

    input_file: usb stress test log.txt
    output: list of a list of string data

    ex on input file
    +--------------------------------------------------------------------------------------+
    | START
    STRESS
    TEST |
    | |
    | Date: 02 / 02 / 22
    12: 21:53 |
    ...
    +----------+---------------+----------------+----------------+----------+----------+----------+--------+--------------+--------------+--------------+--------------+
    | duration |  # total frames | #total bad pkt | #total dropped | #frames  | #dropped | avg. fps |  MB/s  | #C0 Dead img | #C1 Dead img | #C2 Dead img | #C3 Dead img |
    +----------+---------------+----------------+----------------+----------+----------+----------+--------+--------------+--------------+--------------+--------------+
    Warm - Up 2.00 seconds...

    *****Data that will be collected***
    | 1.00 | 30 | 0 | 0 | 30 | 0 | 30.00 | 295.42 | 0 | 0 | 0 | 0 |
    | 2.00 | 60 | 0 | 0 | 30 | 0 | 30.00 | 295.37 | 0 | 0 | 0 | 0 |
    | 3.00 | 90 | 0 | 0 | 30 | 0 | 30.00 | 295.49 | 0 | 0 | 0 | 0 |
    ....
    """

    match_data = "\| +[0-9]+.[0-9][0-9]"    # Regex to find the test result data to filter out any other text
    match_pattern = "\| +"                  # Regex to find all separating character between to text column
    csv_data = [extract_table_header_from_log(input_file)]
    # csv_data = []

    with open(input_file, mode='r') as f:
        for line in f:
            # print(len(re.findall(match_pattern, line)))
            if re.match(match_data, line) is not None:
                new_line = re.sub(pattern=match_pattern, repl=",", string=line)[1:-2]
                csv_data.append(new_line.split(sep=','))
    return csv_data


# header = ["Duration", "# Total Frame", "# total bad pkt",  "# total dropped", "# frames",
#           "# dropped", "avg. fps", "MB/s", "#C0 Dead img", "#C1 Dead img", "#C2 Dead img", "#C3 Dead img"]



def convert_listcsv_to_dataframe(csv_data, file_path):
    """
    This function take as input a list of list of string extracted from the USB Stress
    test and convert it to a dataframe.
     """

    # header = ["Duration", "# Total Frame", "# total bad pkt", "# total dropped", "# frames",
    #           "# dropped", "avg. fps", "MB/s", "#C0 Dead img", "#C1 Dead img", "#C2 Dead img", "#C3 Dead img"]
    # header2 = ["Duration", "# Total Frame", "# Total Error", "# total dropped", "# Frame", "# Dropped", "avg. fps", "MB/s"]

    # if len(csv_data[0]) == 8:
    #     df = pd.DataFrame(csv_data, columns=header2)
    # else:
    #     df = pd.DataFrame(csv_data, columns=header)

    df = pd.DataFrame(csv_data[1:], columns=csv_data[0])

    df["duration"] = df["duration"].astype(float)
    df["avg. fps"] = df["avg. fps"].astype(float)
    df["#total dropped"] = df["#total dropped"].astype(int)
    df.to_excel(result_path + "Export_data for " + get_file_name(file_path) + ".xlsx")
    return df


def compile_test_data_per_minute(df, log_file):
    total_drop = []
    avg_fps_list = []
    avg_fps = []
    stream_duration = []
    nb_line, nb_col = df.shape
    for i in range(0, nb_line):
        if i == 0:
            avg_fps.append(df["avg. fps"].iloc[i])
        elif float(df["duration"].iloc[i]) > float(df["duration"].iloc[i-1]):
            avg_fps.append(df["avg. fps"].iloc[i])
        else:
            total_drop.append(df["#total dropped"].iloc[i-1])
            avg_fps_list.append(average(avg_fps))
            avg_fps = []
            avg_fps.append(df["avg. fps"].iloc[i])
            stream_duration.append(df["duration"].iloc[i-1])

    df_summary = pd.DataFrame()
    df_summary["Total Drop Frame"] = total_drop
    df_summary["Total Drop Frame"] = df_summary["Total Drop Frame"].astype(int)
    df_summary["Avg FPS"] = avg_fps_list
    df_summary["Avg FPS"] = df_summary["Avg FPS"].round(decimals=3)
    df_summary["Stream Duration"] = stream_duration
    df_summary.to_excel(result_path + "Export_summary for " + log_file + ".xlsx")
    # if os.path.exists("result/Export_summary IO-04-002675.xlsx"):
    #
    #     print("FiLE ALREADY EXIST")
    # else:
    #     print("Data summarry create")
    #     df_summary.to_excel(result_path + "Export_summary " + hp_serial + ".xlsx")
    return df_summary

def acceptance_test(df, hp_serial="xxxxxxx", drop_frame_criteria=6, fps_criteria=29.95):
    total_drop = []
    avg_fps_list = []
    avg_fps = []
    nb_line, nb_col = df.shape
    for i in range(0, nb_line):
        if i == 0:
            avg_fps.append(df["avg. fps"].iloc[i])
        elif i == nb_line-1:
            total_drop.append(df["#total dropped"].iloc[i])
            avg_fps_list.append(average(avg_fps))
            avg_fps = []
            avg_fps.append(df["avg. fps"].iloc[i])
        elif float(df["duration"].iloc[i]) > float(df["duration"].iloc[i-1]):
            avg_fps.append(df["avg. fps"].iloc[i])

        else:
            total_drop.append(df["#total dropped"].iloc[i-1])
            avg_fps_list.append(average(avg_fps))
            avg_fps = []
            avg_fps.append(df["avg. fps"].iloc[i])
    df_summary = pd.DataFrame()
    fail_flag = 0x00
    try:
        if max(total_drop) > drop_frame_criteria:
            fail_flag = fail_flag | 0x01
    except ValueError:
        print("Thread too short to perform dropframe calculation")
    try:
        if min(avg_fps_list) < fps_criteria:
            fail_flag = fail_flag | 0x02
    except ValueError:
        print("Thread too short to perform average calculation")
        
    return fail_flag

    # df_summary["Total Drop Frame"] = total_drop
    # df_summary["Total Drop Frame"] = df_summary["Total Drop Frame"].astype(int)
    # df_summary["Avg FPS"] = avg_fps_list
    # df_summary["Avg FPS"] = df_summary["Avg FPS"].round(decimals=3)
    # df_summary.to_excel("Export_summary " + hp_serial + ".xlsx")
    # return df_summary


def create_test_result_summary_csv(hp_serial, df_summary, hpc_serial):
    """
    This function create a CSV file that summarize for the given HP the total of drop frame and the average FPS
    for each thread
    :param hp_serial:
    :param df_summary:
    :return:
    """
    if not os.path.exists(result_path + "Data_summary.csv"):
        data_summary = open(result_path + "Data_summary.csv", mode='w')
        data_summary.close()


    data_summary = open(result_path + "Data_summary.csv", mode='a')
    data_summary.writelines("HPC serial,HP serial,Thread,Total Drop Frame,Avg FPS\n")
    print('File Data_summary.csv created\n')
    x, y = df_summary.shape
    for index, row in df_summary.iterrows():
        data_summary.write(hpc_serial + ',' + hp_serial + ',' + str(int(index)+1) + ',' + str(int((row["Total Drop Frame"]))) + ',' + str(row["Avg FPS"]) + ',')
        data_summary.write("\n")
    data_summary.write(hpc_serial + ',' + hp_serial + ',' + 'Nb iteration,' + str(x) + "\n")
    data_summary.write(hpc_serial + ',' + hp_serial + ',' + 'Avg Stream Duration,' + str(round(df_summary["Stream Duration"].mean(), 2)) + "\n")
    data_summary.write(hpc_serial + ',' + hp_serial + ',' + 'Average drop frame,' + str(round(df_summary["Total Drop Frame"].mean(), 2)) + "\n")
    data_summary.write(hpc_serial + ',' + hp_serial + ',' + 'Max drop frame,' + str(df_summary["Total Drop Frame"].max()) + "\n")
    data_summary.write(hpc_serial + ',' + hp_serial + ',' + 'Min drop frame,' + str(df_summary["Total Drop Frame"].min()) + "\n")
    data_summary.write(hpc_serial + ',' + hp_serial + ',' + 'Avg FPS,' + str(round(df_summary["Avg FPS"].mean(), 3)) + "\n")

    data_summary.close()


def get_path_list_from_file(file):
    """
    Read a text file that contain path\filename and return a list of path and convert DOS '\' with Python '/'
    :param file:
    :return: list
    """
    with open(file, mode='r') as f:
        path_list = []
        for line in f:
            line = line.replace('\\', '/')
            line = line.replace('\n', '')
            path_list.append(line)
    return path_list

def get_file_name(file_path):
    return file_path.split(sep='/')[-1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='*', default=["File_list_to_analyse.txt"])
    arg = parser.parse_args()
    usb_err_summary = []
    print("\n\n********************************************************")
    print("***** Previous result data will be erase/overwrite *****")
    print("********************************************************\n")
    input("    Press enter to continue?\n")
    shutil.rmtree('result', ignore_errors=True)
    os.mkdir("./result/")
    print(arg.filename)
    for file in get_path_list_from_file(arg.filename[0]):
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
        summary = compile_test_data_per_minute(df, get_file_name(file))   # return dataframe
        create_test_result_summary_csv(hp_serial, summary, hpc_serial)
        check_for_usb_error_v2(file, hp_serial, hpc_serial)

    print('DONE !')


if __name__ == '__main__':
    main()



