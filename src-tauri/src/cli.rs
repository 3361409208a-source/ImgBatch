use serde::Serialize;
use std::path::{Path, PathBuf};
use std::time::Duration;
use tauri::{AppHandle, Emitter, Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder};

const QUICK_ACTIONS: &[&str] = &[
    "compress",
    "convert",
    "rename",
    "watermark",
    "trim",
    "normalize",
    "inspect",
];

const QUICK_MERGE_DELAY_MS: u64 = 150;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LaunchProfile {
    Main,
    QuickOnly,
}

#[derive(Debug, Clone, Default, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LaunchPayload {
    pub quick_action: Option<String>,
    pub paths: Vec<String>,
    pub out: Option<String>,
}

pub fn parse_args_from<I, S>(args: I) -> LaunchPayload
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let mut payload = LaunchPayload::default();
    let mut iter = args.into_iter().map(|s| s.as_ref().to_string());
    // skip argv[0]
    let _ = iter.next();

    while let Some(arg) = iter.next() {
        if arg == "--quick" {
            if let Some(action) = iter.next() {
                let a = action.to_lowercase();
                if QUICK_ACTIONS.contains(&a.as_str()) {
                    payload.quick_action = Some(a);
                }
            }
        } else if arg == "--out" {
            if let Some(out) = iter.next() {
                payload.out = Some(out);
            }
        } else if arg.starts_with('-') {
            // ignore unknown flags
        } else if !arg.is_empty() {
            payload.paths.push(normalize_path(&arg));
        }
    }
    payload
}

pub fn parse_env_args() -> LaunchPayload {
    parse_args_from(std::env::args())
}

fn normalize_path(s: &str) -> String {
    let p = PathBuf::from(s.trim_matches('"'));
    p.to_string_lossy().into_owned()
}

fn window_config(app: &AppHandle, label: &str) -> Option<tauri::utils::config::WindowConfig> {
    app.config()
        .app
        .windows
        .iter()
        .find(|w| w.label == label)
        .cloned()
}

fn build_window_from_config(app: &AppHandle, label: &str) -> Result<WebviewWindow, String> {
    let cfg = window_config(app, label)
        .ok_or_else(|| format!("Missing window config for '{label}'"))?;
    WebviewWindowBuilder::from_config(app, &cfg)
        .map_err(|e| format!("{label} window config: {e}"))?
        .build()
        .map_err(|e| format!("Failed to create {label} window: {e}"))
}

pub fn ensure_main_window(app: &AppHandle) -> Result<WebviewWindow, String> {
    if let Some(w) = app.get_webview_window("main") {
        return Ok(w);
    }
    build_window_from_config(app, "main")
}

fn build_quick_window(app: &AppHandle) -> Result<WebviewWindow, String> {
    if let Some(w) = app.get_webview_window("quick") {
        return Ok(w);
    }

    if window_config(app, "quick").is_some() {
        return build_window_from_config(app, "quick");
    }

    WebviewWindowBuilder::new(app, "quick", WebviewUrl::App("index.html".into()))
        .title("ImgBatch 快捷操作")
        .inner_size(420.0, 580.0)
        .min_inner_size(360.0, 420.0)
        .decorations(false)
        .center()
        .visible(false)
        .focused(false)
        .build()
        .map_err(|e| format!("Failed to create quick window: {e}"))
}

fn action_title(action: &str) -> &'static str {
    match action {
        "compress" => "图片压缩",
        "convert" => "格式转换",
        "rename" => "批量重命名",
        "watermark" => "添加水印",
        "trim" => "裁边",
        "normalize" => "规范化",
        "inspect" => "图片检查",
        _ => "快捷操作",
    }
}

fn store_pending_launch(app: &AppHandle, payload: &LaunchPayload) {
    let state = app.state::<crate::AppState>();
    *state.pending_launch.lock().unwrap() = Some(payload.clone());
}

fn merge_quick_buffer(app: &AppHandle, payload: &LaunchPayload) {
    let state = app.state::<crate::AppState>();
    let mut buf = state.quick_buffer.lock().unwrap();
    match buf.as_mut() {
        Some(existing) if existing.quick_action == payload.quick_action => {
            for p in &payload.paths {
                let norm = normalize_path(p);
                if !existing
                    .paths
                    .iter()
                    .any(|x| x.eq_ignore_ascii_case(&norm))
                {
                    existing.paths.push(norm);
                }
            }
            if payload.out.is_some() {
                existing.out = payload.out.clone();
            }
        }
        _ => {
            let mut merged = payload.clone();
            merged.paths = payload
                .paths
                .iter()
                .map(|p| normalize_path(p))
                .collect();
            *buf = Some(merged);
        }
    }
}

fn dispatch_quick_launch(app: &AppHandle, payload: &LaunchPayload) -> Result<(), String> {
    store_pending_launch(app, payload);

    if let Some(main) = app.get_webview_window("main") {
        let was_visible = main.is_visible().unwrap_or(false);
        if was_visible {
            let state = app.state::<crate::AppState>();
            *state.main_hidden_for_quick.lock().unwrap() = true;
        }
        let _ = main.hide();
    }

    let title = payload
        .quick_action
        .as_deref()
        .map(action_title)
        .unwrap_or("快捷操作");

    let window = build_quick_window(app)?;
    let _ = window.set_title(&format!("ImgBatch · {title}"));

    let _ = app.emit("quick-action", payload);
    Ok(())
}

fn flush_quick_buffer(app: &AppHandle, generation: u64) -> Result<(), String> {
    let state = app.state::<crate::AppState>();
    if *state.quick_flush_gen.lock().unwrap() != generation {
        return Ok(());
    }
    let payload = state.quick_buffer.lock().unwrap().take();
    let Some(payload) = payload else {
        return Ok(());
    };
    dispatch_quick_launch(app, &payload)
}

/// Merge rapid multi-select launches (legacy Player mode) and dispatch once.
pub fn queue_quick_launch(app: &AppHandle, payload: &LaunchPayload) -> Result<(), String> {
    merge_quick_buffer(app, payload);

    let state = app.state::<crate::AppState>();
    let mut gen = state.quick_flush_gen.lock().unwrap();
    *gen += 1;
    let generation = *gen;
    drop(gen);

    let app = app.clone();
    std::thread::spawn(move || {
        std::thread::sleep(Duration::from_millis(QUICK_MERGE_DELAY_MS));
        if let Err(e) = flush_quick_buffer(&app, generation) {
            eprintln!("quick flush: {e}");
        }
    });
    Ok(())
}

pub fn show_quick_window(app: &AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("quick")
        .ok_or_else(|| "Quick window not found".to_string())?;
    let _ = window.show();
    let _ = window.unminimize();
    let _ = window.set_focus();
    Ok(())
}

pub fn focus_main(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

pub fn on_quick_window_closed(app: &AppHandle) {
    let state = app.state::<crate::AppState>();
    let profile = *state.launch_profile.lock().unwrap();
    if profile == LaunchProfile::QuickOnly {
        app.exit(0);
        return;
    }

    let restore_main = *state.main_hidden_for_quick.lock().unwrap();
    if restore_main {
        *state.main_hidden_for_quick.lock().unwrap() = false;
        focus_main(app);
    }
}

/// Create only the window needed for the initial launch mode.
pub fn apply_initial_launch(app: &AppHandle, payload: &LaunchPayload) -> Result<(), String> {
    let state = app.state::<crate::AppState>();

    if payload.quick_action.is_some() {
        *state.launch_profile.lock().unwrap() = LaunchProfile::QuickOnly;
        merge_quick_buffer(app, payload);
        let merged = state.quick_buffer.lock().unwrap().take().unwrap_or_else(|| payload.clone());
        dispatch_quick_launch(app, &merged)?;
    } else {
        *state.launch_profile.lock().unwrap() = LaunchProfile::Main;
        ensure_main_window(app)?;
        focus_main(app);
    }
    Ok(())
}

#[allow(dead_code)]
pub fn path_is_dir(path: &str) -> bool {
    Path::new(path).is_dir()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_quick_and_paths() {
        let p = parse_args_from([
            "imgbatch.exe",
            "--quick",
            "compress",
            r"C:\a\b.png",
            r"C:\a\c.jpg",
        ]);
        assert_eq!(p.quick_action.as_deref(), Some("compress"));
        assert_eq!(p.paths.len(), 2);
    }
}
