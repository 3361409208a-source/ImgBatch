use tauri::{Manager, AppHandle};
use tauri_plugin_shell::{process::CommandEvent, ShellExt};

use crate::AppState;

/// Start the Python sidecar process and parse its stdout for the port line.
pub fn setup_sidecar(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let sidecar = app
        .shell()
        .sidecar("imgbatch-api")
        .map_err(|e| format!("Failed to create sidecar command: {e}"))?;

    let (mut rx, child) = sidecar
        .spawn()
        .map_err(|e| format!("Failed to spawn sidecar: {e}"))?;

    {
        let state = app.state::<AppState>();
        *state.sidecar_child.lock().unwrap() = Some(child);
    }

    let app_handle = app.clone();
    tauri::async_runtime::spawn(async move {
        let mut found_port = false;
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(bytes) => {
                    let line = String::from_utf8_lossy(&bytes);
                    let line = line.trim();
                    if !found_port {
                        if let Some(port_str) = line.strip_prefix("IMG_BATCH_PORT=") {
                            if let Ok(port) = port_str.trim().parse::<u16>() {
                                let state = app_handle.state::<AppState>();
                                *state.api_port.lock().unwrap() = Some(port);
                                found_port = true;
                                println!("Sidecar started on port {port}");
                            }
                        }
                    }
                }
                CommandEvent::Stderr(bytes) => {
                    let msg = String::from_utf8_lossy(&bytes);
                    eprint!("Sidecar stderr: {msg}");
                }
                CommandEvent::Error(err) => {
                    eprintln!("Sidecar error: {err:?}");
                }
                CommandEvent::Terminated(_) => {
                    eprintln!("Sidecar terminated");
                    let state = app_handle.state::<AppState>();
                    *state.sidecar_child.lock().unwrap() = None;
                    *state.api_port.lock().unwrap() = None;
                }
                _ => {}
            }
        }
    });

    Ok(())
}

/// Kill the sidecar process if it is still running.
pub fn kill_sidecar(app: &AppHandle) {
    let state = app.state::<AppState>();
    if let Some(child) = state.sidecar_child.lock().unwrap().take() {
        if let Err(e) = child.kill() {
            eprintln!("Failed to kill sidecar: {e}");
        } else {
            println!("Sidecar killed");
        }
    }
    *state.api_port.lock().unwrap() = None;
}
