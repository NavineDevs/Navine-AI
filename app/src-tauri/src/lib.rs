use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::Manager;

struct ServerProcess(Mutex<Option<Child>>);

fn project_root() -> PathBuf {
    if let Ok(root) = std::env::var("NAVINE_ROOT") {
        return PathBuf::from(root);
    }
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest.parent().unwrap().parent().unwrap().to_path_buf()
}

fn python_executable(root: &PathBuf) -> PathBuf {
    let venv_python = root.join("venv").join("Scripts").join("python.exe");
    if venv_python.exists() {
        return venv_python;
    }
    PathBuf::from("python")
}

fn wait_for_server(url: &str, attempts: u32) -> bool {
    for _ in 0..attempts {
        if let Ok(resp) = reqwest::blocking::get(url) {
            if resp.status().is_success() {
                return true;
            }
        }
        thread::sleep(Duration::from_millis(500));
    }
    false
}

fn start_python_server(root: PathBuf) -> Option<Child> {
    let python = python_executable(&root);
    let mut cmd = Command::new(python);
    cmd.args(["-m", "navine.server", "--host", "127.0.0.1", "--port", "8765"])
        .current_dir(&root)
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    cmd.spawn().ok()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let root = project_root();
            let child = start_python_server(root);
            let ready = wait_for_server("http://127.0.0.1:8765/api/health", 60);
            if !ready {
                eprintln!("Navine server did not start. Run: python -m navine.server");
            }
            app.manage(ServerProcess(Mutex::new(child)));
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if let Some(state) = window.app_handle().try_state::<ServerProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(mut child) = guard.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Navine AI desktop app");
}
