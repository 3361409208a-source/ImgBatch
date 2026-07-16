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
    pub target_fmt: Option<String>,
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
        } else if arg == "--format" {
            if let Some(fmt) = iter.next() {
                payload.target_fmt = Some(normalize_format(&fmt));
            }
        } else if arg.starts_with('-') {
            // ignore unknown flags
        } else if !arg.is_empty() && !is_shell_placeholder(&arg) {
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

fn normalize_format(s: &str) -> String {
    let t = s.trim().trim_matches('"').to_lowercase();
    if t.is_empty() {
        return String::new();
    }
    if t.starts_with('.') {
        t
    } else {
        format!(".{t}")
    }
}

fn is_shell_placeholder(s: &str) -> bool {
    let t = s.trim().trim_matches('"');
    t == "%1" || t == "%*" || t == "%V" || t == "%v" || t.starts_with('%')
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
        Some(existing)
            if existing.quick_action == payload.quick_action
                && existing.target_fmt == payload.target_fmt =>
        {
            for p in &payload.paths {
                let norm = normalize_path(p);
                if is_shell_placeholder(&norm) {
                    continue;
                }
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
                .filter(|p| !is_shell_placeholder(p))
                .collect();
            *buf = Some(merged);
        }
    }
}

fn cancel_pending_quick_flush(app: &AppHandle) {
    let state = app.state::<crate::AppState>();
    let mut gen = state.quick_flush_gen.lock().unwrap();
    *gen += 1;
    *state.quick_buffer.lock().unwrap() = None;
}

fn destroy_window_if_exists(app: &AppHandle, label: &str) {
    if let Some(w) = app.get_webview_window(label) {
        let _ = w.destroy();
    }
}

fn dispatch_quick_launch(app: &AppHandle, payload: &LaunchPayload) -> Result<(), String> {
    store_pending_launch(app, payload);

    let state = app.state::<crate::AppState>();
    let profile = *state.launch_profile.lock().unwrap();
    if profile == LaunchProfile::QuickOnly {
        destroy_window_if_exists(app, "main");
    }

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
        .map(|action| {
            if action == "convert" {
                if let Some(fmt) = payload.target_fmt.as_deref() {
                    let ext = fmt.trim_start_matches('.').to_uppercase();
                    return format!("转为 {ext}");
                }
            }
            action_title(action).to_string()
        })
        .unwrap_or_else(|| "快捷操作".to_string());

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
    cancel_pending_quick_flush(app);

    let state = app.state::<crate::AppState>();
    let profile = *state.launch_profile.lock().unwrap();
    if profile == LaunchProfile::QuickOnly {
        destroy_window_if_exists(app, "main");
        crate::sidecar::kill_sidecar(app);
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

    #[test]
    fn parses_convert_with_format() {
        let p = parse_args_from([
            "imgbatch.exe",
            "--quick",
            "convert",
            "--format",
            ".webp",
            r"C:\a\b.png",
        ]);
        assert_eq!(p.quick_action.as_deref(), Some("convert"));
        assert_eq!(p.target_fmt.as_deref(), Some(".webp"));
        assert_eq!(p.paths.len(), 1);
    }

    #[test]
    fn ignores_shell_placeholders() {
        let p = parse_args_from(["imgbatch.exe", "--quick", "compress", "%*", "%1"]);
        assert!(p.paths.is_empty());
    }
}
