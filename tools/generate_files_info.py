import os, json, hashlib, logging, uuid, time

import dotenv
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

BASE_PATH = os.getenv("BASE_PATH") or ""
PROJECT_DATA_PATH = os.getenv("PROJECT_DATA_PATH") or ""

if not BASE_PATH and BASE_PATH is not None and not os.path.exists(BASE_PATH):
    raise ValueError("BASE_PATH is not set in .env")
if not PROJECT_DATA_PATH and PROJECT_DATA_PATH is not None and not os.path.exists(PROJECT_DATA_PATH):
    raise ValueError("PROJECT_DATA_PATH is not set in .env")

def generate_checksums(path):
    checksums = {}

    if os.path.isfile(path):
        logger.info(f"Generating checksum for file {path}")
        with open(path, "rb") as f:
            data = f.read()
        sha256 = hashlib.sha256()
        sha256.update(data)
        checksums[os.path.basename(path)] = {
            "checksum": sha256.hexdigest(),
            "last_modified": os.path.getmtime(path),
            "last_modified_human": time.ctime(os.path.getmtime(path))
        }
    else:
        for root, _, files in os.walk(path):
            for file in files:
                if file == "files_info.json":
                    continue
                file_path = os.path.join(root, file)
                logger.info(f"Generating checksum for file {file_path}")
                with open(file_path, "rb") as f:
                    data = f.read()
                sha256 = hashlib.sha256()
                sha256.update(data)
                relative_path = os.path.relpath(file_path, path)
                checksums[relative_path] = {
                    "checksum": sha256.hexdigest(),
                    "last_modified": os.path.getmtime(file_path),
                    "last_modified_human": time.ctime(os.path.getmtime(path))
                }

    return checksums

def save_files_info(project_path):
    output_file = os.path.join(project_path, "files_info.json")
    checksums = generate_checksums(project_path)

    files_info = {
        "version": os.path.basename(project_path),
        "files": checksums,
    }

    with open(output_file, "w") as f:
        json.dump(files_info, f, indent=4, default=str)

    logger.info(f"Saved files_info.json to {output_file}")

def generate_for_all_projects(base_directory):
    if PROJECT_DATA_PATH is not None and not os.path.exists(PROJECT_DATA_PATH):
        open(str(PROJECT_DATA_PATH), "w").write(json.dumps({}))
    project_data = json.loads(open(PROJECT_DATA_PATH, "r").read())
    for project in os.listdir(base_directory):
        project_path = os.path.join(base_directory, project)
        if os.path.isdir(project_path):
            logger.info(f"Generating files_info.json for project {project}")
            save_files_info(project_path)
        if os.path.relpath(project_path, base_directory) not in project_data.values():
            project_data[str(uuid.uuid4())] = os.path.relpath(project_path, base_directory)
    open(PROJECT_DATA_PATH, "w").write(json.dumps(project_data, indent=4))    


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s][%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info("Starting script generate_files_info.py")

    try:
        base_directory = BASE_PATH
        generate_for_all_projects(base_directory)
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt")

    logger.info("Script generate_files_info.py finished")
