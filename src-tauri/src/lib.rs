mod cli;
mod commands;
mod sidecar;

use std::sync::Mutex;

use tauri::{Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::process::CommandChild;

use cli::{LaunchPayload, LaunchProfile};

pub struct AppState {
    pub api_port: Mutex<Option<u16>>,
    pub sidecar_child: Mutex<Option<CommandChild>>,
    pub pending_launch: Mutex<Option<LaunchPayload>>,
    pub launch_profile: Mutex<LaunchProfile>,
    pub main_hidden_for_quick: Mutex<bool>,
    pub quick_buffer: Mutex<Option<LaunchPayload>>,
    pub quick_flush_gen: Mutex<u64>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            api_port: Mutex::new(None),
            sidecar_child: Mutex::new(None),
            pending_launch: Mutex::new(None),
            launch_profile: Mutex::new(LaunchProfile::Main),
            main_hidden_for_quick: Mutex::new(false),
            quick_buffer: Mutex::new(None),
            quick_flush_gen: Mutex::new(0),
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
                let _ = cli::queue_quick_launch(app, &payload);
            } else {
                let _ = cli::ensure_main_window(app);
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
                    cli::on_quick_window_closed(&app);
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
            commands::quick_window_ready,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::Exit = event {
                sidecar::kill_sidecar(app_handle);
            }
        });
}
