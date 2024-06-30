use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::{Path};
use std::time::{UNIX_EPOCH};
use walkdir::WalkDir;
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use log::{info};
use env_logger;
use uuid::Uuid;

#[derive(Serialize, Deserialize)]
struct FileInfo {
    checksum: String,
    last_modified: u64,
    last_modified_human: String,
}

#[derive(Serialize, Deserialize)]
struct FilesInfo {
    version: String,
    files: HashMap<String, FileInfo>,
}

fn generate_checksum_for_file(file_path: &Path) -> io::Result<FileInfo> {
    info!("Generating checksum for file {:?}", file_path);
    let file = File::open(file_path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0; 4096];
    let mut reader = io::BufReader::new(file);
    while let Ok(n) = reader.read(&mut buffer) {
        if n == 0 { break; }
        hasher.update(&buffer[..n]);
    }
    let result = hasher.finalize();
    let metadata = fs::metadata(file_path)?;
    let modified_time = metadata.modified()?.duration_since(UNIX_EPOCH).unwrap_or_else(|_| std::time::Duration::from_secs(0)).as_secs();
    let modified_time_human: std::time::SystemTime = metadata.modified()?.into();
    Ok(FileInfo {
        checksum: format!("{:x}", result),
        last_modified: modified_time,
        last_modified_human: format!("{:?}", modified_time_human),
    })
}

fn generate_checksums(path: &Path) -> io::Result<HashMap<String, FileInfo>> {
    let mut checksums = HashMap::new();
    if path.is_file() {
        if let Ok(file_info) = generate_checksum_for_file(path) {
            checksums.insert(path.file_name().unwrap().to_string_lossy().to_string(), file_info);
        }
    } else {
        for entry in WalkDir::new(path) {
            let entry = entry?;
            if entry.file_type().is_file() {
                if entry.file_name() == "files_info.json" {
                    continue;
                }
                if let Ok(file_info) = generate_checksum_for_file(entry.path()) {
                    let relative_path = entry.path().strip_prefix(path).unwrap().to_string_lossy().to_string();
                    checksums.insert(relative_path, file_info);
                }
            }
        }
    }
    Ok(checksums)
}

fn save_files_info(project_path: &Path) -> io::Result<()> {
    let output_file = project_path.join("files_info.json");
    let checksums = generate_checksums(project_path)?;

    let files_info = FilesInfo {
        version: project_path.file_name().unwrap().to_string_lossy().to_string(),
        files: checksums,
    };

    let json_data = serde_json::to_string_pretty(&files_info)?;
    fs::write(output_file.clone(), json_data)?;

    info!("Saved files_info.json to {:?}", output_file.clone());
    Ok(())
}

fn main() -> io::Result<()> {
    env_logger::init();
    info!("Starting script generate_files_info");

    let base_path = std::env::var("BASE_PATH").unwrap_or_else(|_| ".".to_string());
    let project_data_path = std::env::var("PROJECT_DATA_PATH").unwrap_or_else(|_| "project_data.json".to_string());

    let base_directory = Path::new(&base_path);

    if !base_directory.exists() {
        return Err(io::Error::new(io::ErrorKind::NotFound, "BASE_PATH does not exist"));
    }

    let mut project_data: HashMap<String, String> = if Path::new(&project_data_path).exists() {
        let data = fs::read_to_string(&project_data_path)?;
        serde_json::from_str(&data)?
    } else {
        HashMap::new()
    };

    for entry in fs::read_dir(base_directory)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            info!("Generating files_info.json for project {:?}", path);
            save_files_info(&path)?;
            let rel_path = path.strip_prefix(base_directory).unwrap().to_string_lossy().to_string();
            if !project_data.values().any(|v| v == &rel_path) {
                project_data.insert(Uuid::new_v4().to_string(), rel_path);
            }
        }
    }

    let json_data = serde_json::to_string_pretty(&project_data)?;
    fs::write(project_data_path, json_data)?;

    info!("Script generate_files_info finished");
    Ok(())
}
