mod commands;
mod sidecar;

use std::sync::Mutex;

use tauri::{Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::process::CommandChild;

pub struct AppState {
    pub api_port: Mutex<Option<u16>>,
    pub sidecar_child: Mutex<Option<CommandChild>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            api_port: Mutex::new(None),
            sidecar_child: Mutex::new(None),
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(AppState::default())
        .setup(|app| {
            let handle = app.handle().clone();
            sidecar::setup_sidecar(&handle)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                sidecar::kill_sidecar(window.app_handle());
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_api_base_url,
            commands::pick_folder,
            commands::pick_files,
            commands::pick_save_file,
            commands::open_path,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::Exit = event {
                sidecar::kill_sidecar(app_handle);
            }
        });
}
