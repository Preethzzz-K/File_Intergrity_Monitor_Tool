import json
import hmac
import secrets
import hashlib as hl
from pathlib import Path

def secret_key(project_path, path):
    key_file = f"{project_path}/key_files/{path.stem}.key"
    if Path(key_file).exists():
        with open(key_file, "rb") as fileHandler:
            key = fileHandler.read()
        return key
    else:
        key = secrets.token_bytes(32)
        with open(key_file, "wb") as fileHandler:
            fileHandler.write(key)
        Path(key_file).chmod(0o600)
        return key

def hmac_signature(key,file_name):
    with open(file_name, "rb") as filehandler:
        file_hash = filehandler.read()
    signature = hmac.new(key,file_hash,hl.sha256)
    return signature.hexdigest()


def json_dump_op(baseline_file_details,path,project_path):
    parent_dir = project_path
    file_name = f"{parent_dir}/json_files/{path.stem}.json"
    with open(file_name, "w") as filehander:
        file_details = baseline_file_details
        json.dump(file_details,filehander,indent=4)

    key = secret_key(project_path, path)
    
    signature = hmac_signature(key,file_name)
    sig_parent = path.parent
    file_sig = f"{sig_parent}/sig_files/{path.stem}.sig"
    with open(file_sig,"w") as filehandler:
        filehandler.write(signature)


def json_load_op(json_file,path, project_path):
    key = secret_key(project_path,path)
    signature = hmac_signature(key,json_file)
    file_sig = f"{project_path}/sig_files/{path.stem}.sig"
    with open(file_sig,"r") as filehandler:
        actual_mac = filehandler.read()
    comparision_of_mac = hmac.compare_digest(actual_mac,signature)
    if comparision_of_mac == True:
        pass
    else:
        print("--------------Warning!!------------\nMAC is been altered, Data is Compromised....")
    with open(json_file, "r") as filehandler:
            return json.load(filehandler)
        
    

    