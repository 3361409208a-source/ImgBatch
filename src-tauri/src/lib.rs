mod cli;
mod commands;
mod sidecar;

use std::sync::Mutex;

use tauri::{Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::process::CommandChild;

use cli::LaunchPayload;

pub struct AppState {
    pub api_port: Mutex<Option<u16>>,
    pub sidecar_child: Mutex<Option<CommandChild>>,
    pub pending_launch: Mutex<Option<LaunchPayload>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            api_port: Mutex::new(None),
            sidecar_child: Mutex::new(None),
            pending_launch: Mutex::new(None),
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let initial = cli::parse_env_args();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_single_instance::init(|app, argv, _cwd| {
            let payload = cli::parse_args_from(argv);
            if payload.quick_action.is_some() {
                let _ = cli::open_or_focus_quick(app, &payload);
            } else {
                cli::focus_main(app);
            }
        }))
        .manage(AppState::default())
        .setup(move |app| {
            let handle = app.handle().clone();
            sidecar::setup_sidecar(&handle)?;
            cli::apply_initial_launch(&handle, &initial)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                let label = window.label().to_string();
                let app = window.app_handle().clone();
                if label == "main" {
                    sidecar::kill_sidecar(&app);
                } else if label == "quick" {
                    // Quick-only launch leaves main hidden — exit when popup closes.
                    if let Some(main) = app.get_webview_window("main") {
                        if !main.is_visible().unwrap_or(true) {
                            app.exit(0);
                        }
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_api_base_url,
            commands::pick_folder,
            commands::pick_files,
            commands::pick_save_file,
            commands::open_path,
            commands::get_launch_payload,
            commands::get_window_label,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::Exit = event {
                sidecar::kill_sidecar(app_handle);
            }
        });
}
