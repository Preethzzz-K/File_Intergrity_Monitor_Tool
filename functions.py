import hashlib as hl
import stat
import dumper_loader_file
import sys

#function used to get details ot stats of the path given
def file_details_hunt(hunt,base_dict,data_dict,op):
    print("\n")
    if op == "delete":
        dict_store = data_dict
    else:
        dict_store = base_dict

    for key in hunt:
        try:
            if base_dict[key]["stat_mode"] == data_dict[key]["stat_mode"]:
                permission_changed = False
                
            elif base_dict[key]["stat_mode"] != data_dict[key]["stat_mode"]:
                permission_changed = True
            
            else:
                permission_changed = None
        
        except KeyError :
            permission_changed = None
        
        finally:
            print(f"Parent Dir : {dict_store[key]['Parent Dir']}")
            print(f"File Name : {dict_store[key]['File Name']}")
            print(f"stat_mode : {dict_store[key]['stat_mode']}")
            print(f"stat_uid : {dict_store[key]['stat_uid']}")
            print(f"stat_gid : {dict_store[key]['stat_gid']}")
            print(f"stat_size : {dict_store[key]['stat_size']}")
            print(f"stat_acess_time : {dict_store[key]['stat_acess_time']}")
            print(f"stat_modified_time : {dict_store[key]['stat_modified_time']}")
            print(f"stat_creation_time : {dict_store[key]['stat_creation_time']}")
            print(f"File Permission Change Status: {permission_changed}")
            if op == "permission":
                print(f"Actual stat_mode: {data_dict[key]['stat_mode']}")
            print("\n")
            
#function used log file details on CLI screen
def file_logger(path,base_dict,stats,path_details):
    with open("paths.txt","r") as filehandler:
        file = filehandler.read()

    
        if str(path) in file: 
            path_details.append(str(path))  
            path_specifier = path.glob("*") ## path of the given folder
            
            for p in path_specifier:
                path_details.append(p)
                path_selector(p, base_dict,path_details) #function used to check for dir and files and select path and store
            
            try:
                parent_dir = path.parent
                file_name = f"{parent_dir}/json_files/{path.stem}.json"
                data = dumper_loader_file.json_load_op(file_name,path) #loads the data
                is_added = base_dict.keys() - data.keys() # to identify if any additional file has been added to our folder
                is_deleted = data.keys() - base_dict.keys() #to identify if any  file has been deleted from our folder
                is_modified = data.keys() & base_dict.keys() #to identify if any  file has been modified to our folder
                
                
                #parsing the set elements and passes to the function
                add_count = 0
                delete_count = 0
                modified_count = 0
                modified_list = []
                # not_modified_list = []
                not_modified_count = 0
                permission_changed_count = 0
                permission_changed_list = []
    
    
                if is_added != set():
                    for op in is_added: 
                        add_count = add_count+1
                    if stats == True:
                        print("--------------------------------------------------------")
                        print("--------------------------------------------------------")
                        print(f"Total Files Added: {add_count}")
                        print("Below are the Stats of the Added files")
                        file_details_hunt(is_added,base_dict,data,"add")
    
                        
                if is_deleted != set():
                    for op in is_deleted:
                        delete_count = delete_count+1
                    if stats == True:
                        print("--------------------------------------------------------")
                        print("--------------------------------------------------------")
                        print(f"Total Files Deleted: {delete_count}")
                        print("Below are the Stats of the Deleted files")
                        file_details_hunt(is_deleted,base_dict,data,"delete")
    
                if is_modified != set():
                    for op in is_modified:
                        if base_dict[op]["stat_mode"] != data[op]["stat_mode"]:
                            permission_changed_count = permission_changed_count + 1
                            permission_changed_list.append(op)
                            
    
                        if base_dict[op]["hash"] != data[op]["hash"]:
                            modified_count = modified_count+1
                            modified_list.append(op)
    
    
                        else:
                         not_modified_count = not_modified_count + 1
                        #     not_modified_list.append(op)
    
                    if stats  == True and permission_changed_count > 0:
                        print("--------------------------------------------------------")
                        print("--------------------------------------------------------")
                        print(f"Total Files with changed Permission: {permission_changed_count}")
                        print("Below are the stats of Permission Changed Files")
                        file_details_hunt(permission_changed_list,base_dict,data,"permission") 
    
                    if stats == True and modified_count > 0:
                        print("--------------------------------------------------------")
                        print("--------------------------------------------------------")
                        print(f"Total Files Content Modified: {modified_count}")
                        print("Below are the stats of Content Modified Files")
                        file_details_hunt(modified_list,base_dict,data,"modify")
    
                    
                    # if stats == True and not_modified_count >= 0:
                    #     print("--------------------------------------------------------")
                    #     print("--------------------------------------------------------")
                    #     print(f"Total Files Classified: {not_modified_count}")
                    #     print("Below are the stats of Classified Files")
                    #     file_details_hunt(not_modified_list,base_dict,data,"not_modify")
                
                if stats == True and (add_count + delete_count + modified_count + permission_changed_count) == 0 :
                    print("---------------------------------------------------------------------------------")  
                    print("Please Note: There are no Additions, Deletions, Content Modifications or Peromission_changes done on the monitoring files")                         
    
                if stats == False:
                    print("--------------------------------------------------------")
                    print("--------------------------------------------------------")          
                    print("Please find the below Details of your files being monitored: ")
                    print(f"Path being Monitored: {path}")
                    print(f"Total Files Being Monitored: {add_count + delete_count + modified_count + not_modified_count }")
                    print(f"Files Added:{add_count}")
                    print(f"Files Deleted:{delete_count}")
                    print(f"File Content Modified:{modified_count}")
                    # print(f"Files Classified: {not_modified_count}")
                    print(f"File Permissions Changed: {permission_changed_count}")

                if (add_count+delete_count+modified_count+permission_changed_count) == 0:
                    sys.exit(0)
                else:
                    sys.exit(1)
                    
            

            except FileNotFoundError:
                print("Looks like the given path to file or directory is not been iniated for monitoring\n Kindly init the path for monitoring\n You can also check '--help' for any assitance")

        
        else:
            print("Looks like the given path to file or directory is not been iniated for monitoring\n Kindly init the path for monitoring\n You can also check '--help' for any assitance")


                           
# Hashing function
def file_hasing(path):
    hashed = hl.sha256()
    with open(path, "rb") as fileHandler:
              while True:
                read_binary = fileHandler.read(8500)
                if read_binary == b"":
                    break
                else:
                    hashed.update(read_binary)
    return hashed.hexdigest()
   

#function to read the metdata of the file
def stat_reader(path):
    stp = path.stat()
    stat_mode = stat.filemode(stp.st_mode)
    stat_uid = stp.st_uid
    stat_gid = stp.st_gid
    stat_size = stp.st_size 
    stat_acess_time = stp.st_atime
    stat_modified_time = stp.st_mtime
    stat_creation_time = stp.st_ctime
    return (stat_mode,
            stat_uid,
            stat_gid,
            stat_size,
            stat_acess_time,
            stat_creation_time,
            stat_modified_time)

#to identify the path contains a file or another directory. so that if file is identified it can be hashed
def path_selector(path,base_dict,path_details):
    if path.is_dir(): #if current path leads to directory performs below operation 
        identify_path = list(path.glob("*"))
        for path in identify_path:
            path_details.append(path)
            if path.is_dir():
                path_selector(path,base_dict,path_details) #function called recurselvely till file path is identified
            else:
                file_stat_details  = stat_reader(path)
                file_details_op(path,base_dict,file_stat_details) #if file is found then copies the path and baseline dict and passess to file_details_op
        
    else:
        file_stat_details  = stat_reader(path)
        file_details_op(path,base_dict,file_stat_details)

#function performing operation to store the file details
def file_details_op(path,base_dict,file_stat):
    dir_path = str(path) # to store the path 
    parent_dir = str(path.parent) # to store the parent directory
    file_name = path.name #to store the name of the file
    hashed_file_val = file_hasing(path) #to store the hased value of the file
    base_dict[dir_path] = {
        "Parent Dir" : parent_dir,
        "File Name" : file_name,
        "hash" : hashed_file_val ,
        "stat_mode" : file_stat[0],
        "stat_uid" : file_stat[1],
        "stat_gid" : file_stat[2],
        "stat_size" : file_stat[3],
        "stat_acess_time" : file_stat[4],
        "stat_modified_time" : file_stat[5],
        "stat_creation_time" : file_stat[6],
    }

    
    