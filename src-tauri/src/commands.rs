use tauri::State;
use tauri_plugin_dialog::DialogExt;

use crate::cli::LaunchPayload;
use crate::AppState;

fn path_to_string(p: tauri_plugin_dialog::FilePath) -> Option<String> {
    p.into_path()
        .ok()
        .map(|pb| pb.to_string_lossy().into_owned())
}

#[tauri::command]
pub fn get_api_base_url(state: State<'_, AppState>) -> Result<String, String> {
    let port = state.api_port.lock().unwrap();
    match *port {
        Some(p) => Ok(format!("http://127.0.0.1:{p}")),
        None => Err("API sidecar not ready".into()),
    }
}

/// Sync command — avoid async + blocking_dialog deadlock on Windows.
#[tauri::command]
pub fn pick_folder(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let path = app.dialog().file().blocking_pick_folder();
    Ok(path.and_then(path_to_string))
}

#[tauri::command]
pub fn pick_files(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let paths = app
        .dialog()
        .file()
        .add_filter(
            "Images",
            &["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"],
        )
        .blocking_pick_files();
    Ok(paths
        .unwrap_or_default()
        .into_iter()
        .filter_map(path_to_string)
        .collect())
}

#[tauri::command]
pub fn pick_save_file(
    app: tauri::AppHandle,
    default_name: String,
) -> Result<Option<String>, String> {
    let path = app
        .dialog()
        .file()
        .set_file_name(&default_name)
        .blocking_save_file();
    Ok(path.and_then(path_to_string))
}

#[tauri::command]
pub fn get_launch_payload(state: State<'_, AppState>) -> LaunchPayload {
    state
        .pending_launch
        .lock()
        .unwrap()
        .clone()
        .unwrap_or_default()
}

#[tauri::command]
pub fn get_window_label(window: tauri::Window) -> String {
    window.label().to_string()
}

#[tauri::command]
pub fn quick_window_ready(app: tauri::AppHandle) -> Result<(), String> {
    crate::cli::show_quick_window(&app)
}

#[tauri::command]
pub fn close_quick_session(app: tauri::AppHandle) -> Result<(), String> {
    crate::cli::on_quick_window_closed(&app);
    Ok(())
}

#[tauri::command]
pub async fn open_metaso_assistant(
    app: tauri::AppHandle,
    prompt_text: String,
) -> Result<(), String> {
    crate::cli::open_metaso_window(&app, prompt_text)
}

#[tauri::command]
pub fn open_path(path: String) -> Result<(), String> {
    // Use OS default handler without deprecated shell.open
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("cmd")
            .args(["/C", "start", "", &path])
            .spawn()
            .map_err(|e| format!("Failed to open path: {e}"))?;
        return Ok(());
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open path: {e}"))?;
        return Ok(());
    }
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open path: {e}"))?;
        Ok(())
    }
}
