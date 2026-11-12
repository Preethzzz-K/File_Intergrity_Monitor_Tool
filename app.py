from pathlib import Path
import argparse
import dumper_loader_file #created module with function used dump and load the json file
import functions #created module to store the functions
import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def __init__(self, path, monitor_path):
        self.path = Path(path)
        self.monitor_path = Path(monitor_path)
        self.last_modified = {}
        
    def on_created(self, event):
        if event.is_directory:
            return
        else:
            current_time = time.time()
            file_path = event.src_path
            if file_path in self.last_modified:
                if current_time - self.last_modified[file_path] < 0.5:
                    return
            self.last_modified[file_path] = current_time
            print("--------------------------------------------------")
            message = f"File_path {event.src_path}\nStatus: Added"
            print(message)
            functions.log_entry(message, self.path, self.monitor_path, "add")    
        
    def on_deleted(self, event):
        if event.is_directory:
            return
        else:
            print("--------------------------------------------------")
            message = f"File_path {event.src_path}\nStatus: Deleted"
            print(message)
            functions.log_entry(message, self.path, self.monitor_path, "delete")

    def on_modified(self, event):
        if event.is_directory:
            return
        else:
            current_time = time.time()
            file_path = event.src_path
            if file_path in self.last_modified:
                if current_time - self.last_modified[file_path] < 0.5:
                    return
            self.last_modified[file_path] = current_time
            print("--------------------------------------------------\n")
            message = f"File_path {event.src_path}\nStatus: Modified"
            print(message)
            functions.log_entry(message, self.path, self.monitor_path, "modify")



if __name__ == "__main__":
     #blank dict to store the file path and other details of the file
    baseline_file_details = {}
    path_details = []
    project_path = Path.cwd()
    Path("./paths.txt").chmod(0o600)    
    #code used to build CLI results
    parser = argparse.ArgumentParser(description="Coomands of File Intergrity Mointoring System")
    parser.add_argument("--init", type=str ,help="This command is used to initiate montioring on a file/folder")
    parser.add_argument("--check", type=str, help="This command is used to monitor the files and provide results on changes in dir or file" )
    parser.add_argument("--stat", type = str, help="This command is used to provide stats of each files added,deleted and modified")
    parser.add_argument("--update", type = str, help="This command is used to provide stats of each files added,deleted and modified")
    parser.add_argument("--verify_log", type=str, help="This command is used to verify the log entries to check if any log has been altered or not")
    parser.add_argument("--monitor" , type=str, help="This command is used to automate the process of monitoring files")
    parser.add_argument("--cron_check" , type=str, help="This is an internal command. Please donot Run this command")

    arg = parser.parse_args()

    log_file_path = ""

    # this allows to iniate file/directory to be monitored
    if arg.init:
        path = Path(arg.init)
        if path.exists():
            with open(f"{project_path}/paths.txt","r") as filehandler:
                file = filehandler.read()        
                if str(path) not in file:
                    path_details.append(path)                 
                    path_specifier = path.glob("*") ## path of the given folder
                    for p in path_specifier:
                        path_details.append(p)
                        functions.path_selector(p, baseline_file_details,path_details) #function used to check for dir and files and select path and store
                    with open("paths.txt","a") as filehandler:
                        for details in path_details:
                            filehandler.write(f"{details}\n")
                    dumper_loader_file.json_dump_op(baseline_file_details,path, project_path) #used to dump the json file
                    print(f"Your Given path : {path} is now under monitoring......")
                    print("----------------------------------------------------------------------------------------------------")
                    print("Important: Please run '--monitor <path_name>' for enabling the automated monitoring and logging monitoring details of the given path")
                    print("If this is not run then realtime if any changes are done, Program will not log the changes")

                    logging.basicConfig(
                        level = logging.INFO,
                        force = True,
                        filemode="a",
                        filename = f"{project_path}/log_files/{path.stem}.log",
                        format="{  \n Message: %(message)s \n Date & time: %(asctime)s \n Logging_level: %(levelname)s \n}",
                    )
                    logging.info(f"Path: {path}\n Status: Monitoring Initiated")
                    functions.log_hex(f"{project_path}/log_files/{path.stem}.log", path, project_path)
                            

                else:
                        print("Given path or its parent path already exists and its files are being monitored")
                        print("Kindly run '--check or --stat' on the path or its parent pat to view details of monitoring files")
                        print("Note: You can also run '--help' for assitance with commands")
                    
        else:
    
            print("Given File/Dir path does not exists, kindly check the path provided")
            print("Note: You can also run '--help' for assitance with commands")

    #part that helps to automatcally monitor given path
    elif arg.monitor:        
        path = Path(arg.monitor)
        is_monitoring = True
        
        with open(f"{project_path}/paths.txt","r") as filehandler:
                file = filehandler.read()        
                if str(path) not in file:
                    print("It looks like thr given path has not been iniatied for monitoring.\nKindly iniatie the given path for monitoring using '--init' command")
                    is_monitoring = False
        
        if is_monitoring:
            if path.exists():
                event_handler = MyHandler(project_path, path)
                observer = Observer()
                observer.schedule(event_handler, path, recursive=True)
                print(f"Automated file-montoring has been initiated on {path}")
                observer.start()

                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("--------------------------------------------------------------------------------------------------------------------")
                    print("Please Note: File under monitoring, however realtime automated monitoring has been stopped due to Keyboard Interrupt")
                    observer.stop()
                observer.join()

    #Below code help to provide summary of file which are being monitored for additions,deletions,content modifcations or permission changes in a file
    elif arg.check:
        path_details = []
        check_path = Path(arg.check)
        if check_path.exists():
            functions.file_logger(check_path,baseline_file_details,False,path_details,project_path)
            
        else:
            print("Given Path seems to not exist. Kindly check the path of the file or directory properly")
            print("Note: You can also run '--help' for assitance with commands")


    #Below code help to provides the stats of file which are being monitored for additions,deletions,content modifcations or permission changes in a file
    elif arg.stat: 
        path_details = []
        stat_path = Path(arg.stat)
        if stat_path.exists():
            functions.file_logger(stat_path,baseline_file_details,True,path_details, project_path)
        else:
            print("Given Path seems to not exist. Kindly check the path of the file or directory properly")
            print("Note: You can also run '--help' for assitance with commands")

    #Below code helps to update the directory or file that is getting monitored
    elif arg.update:    
        update_path = Path(arg.update)
        if update_path.exists():
            with open("paths.txt","r") as filehandler:
                file = filehandler.read()
                if str(update_path) in file:
                    path_specifier = update_path.glob("*") ## path of the given folder
                    for p in path_specifier:
                        functions.path_selector(p, baseline_file_details,path_details) #function used to check for dir and files and select path and store
                    print("You are now going to update the monitoring Files and directories. Once updated it cannot be undone.")
                    user_input = input("Do you want to continue to update (Y/N)").upper()
                    if user_input == "Y":
                        dumper_loader_file.json_dump_op(baseline_file_details,update_path,project_path) #used to dump the json file
                        print(f"Your Given path : {update_path} is now updated and under monitoring......")
                        log_details = logging.basicConfig(
                            level = logging.INFO,
                            force = True,
                            filemode="a",
                            filename = f"{update_path.parent}/log_files/{update_path.stem}.log",
                            format="{  \n Message: %(message)s \n Date & time: %(asctime)s \n Logging_level: %(levelname)s \n}",
                            )
                        logging.warning(f"Path: {update_path}\n Status: Updated Monitoring")
                        functions.log_hex(f"{project_path}/log_files/{update_path.stem}.log",update_path, project_path)
                    elif user_input == "N": 
                        print(f"No changes done to your {update_path}")
                    else:
                        print("Invalid Input")
                        print("No changes done..Exiting command")
                else:
                    print("It seems like the given path for file or directory is not been initiated for monitoring.\n Please check path provided and run '-init' command")
                    print("You can also checkout '--help' for any help required with commands and its usage") 
                            
        else:
            print("Given Path seems to not exist. Kindly check the path of the file or directory properly")
            print("Note: You can also run '--help' for assitance with commands")

    elif arg.verify_log:
        path = Path(arg.verify_log)
        if path.exists():
            log_file_path = f"{path.parent}/log_files/{path.stem}.log" 
            json_log_path = f"{path.parent}/log_files/log_json_files/{path.stem}_log.json" 
            functions.log_verify(log_file_path, json_log_path)
        else:
            print("The path does not exists, Kindly check if the given path was iniated for monitoring")

    else:
        print("It seems like there were errors in aruguments or commands given\n Kindly check '--help' for help with commands and arguments")


    
          
        

            
                    
                    

    
                                






    
    
 
    

    
    








        
        