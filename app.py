from pathlib import Path
import hashlib as hl


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

    print(f"hased File path {path.name}: {hashed.hexdigest()}")



#to identify the path contains a file or another directory. so that if file is identified it can be hashed
def path_selector(path):
    counter = 0
    if path.is_dir():
        identify_path = list(path.glob("*"))
        for p in identify_path:
            if p.is_dir():
                path_selector(p)
            else:
                file_hasing(p)
                
     
    else:
         file_hasing(path)
    

path = list(Path("/mnt/hgfs/Kali_HDD_Storage/My_Projects/project_file_monitor").glob("*"))
for p in path:
    path_selector(p)


    

            









        
        