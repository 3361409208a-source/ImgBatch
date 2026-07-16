use serde::Serialize;
use std::path::{Path, PathBuf};
use tauri::{AppHandle, Emitter, Manager, WebviewUrl, WebviewWindowBuilder};

const QUICK_ACTIONS: &[&str] = &[
    "compress",
    "convert",
    "rename",
    "watermark",
    "trim",
    "normalize",
    "inspect",
];

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

fn build_quick_window(app: &AppHandle) -> Result<tauri::WebviewWindow, String> {
    // Prefer tauri.conf.json "quick" entry so size/title stay consistent.
    if let Some(cfg) = app
        .config()
        .app
        .windows
        .iter()
        .find(|w| w.label == "quick")
        .cloned()
    {
        return WebviewWindowBuilder::from_config(app, &cfg)
            .map_err(|e| format!("quick window config: {e}"))?
            .build()
            .map_err(|e| format!("Failed to create quick window: {e}"));
    }

    WebviewWindowBuilder::new(app, "quick", WebviewUrl::App("index.html".into()))
        .title("ImgBatch 快捷操作")
        .inner_size(420.0, 580.0)
        .min_inner_size(360.0, 420.0)
        .center()
        .visible(true)
        .focused(true)
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

pub fn open_or_focus_quick(app: &AppHandle, payload: &LaunchPayload) -> Result<(), String> {
    {
        let state = app.state::<crate::AppState>();
        *state.pending_launch.lock().unwrap() = Some(payload.clone());
    }

    // Keep main hidden — never show it during quick-action flow (prevents flash).
    if let Some(main) = app.get_webview_window("main") {
        let _ = main.hide();
    }

    let title = payload
        .quick_action
        .as_deref()
        .map(action_title)
        .unwrap_or("快捷操作");

    let window = if let Some(w) = app.get_webview_window("quick") {
        let _ = w.set_title(&format!("ImgBatch · {title}"));
        w
    } else {
        let w = build_quick_window(app)?;
        let _ = w.set_title(&format!("ImgBatch · {title}"));
        w
    };

    let _ = window.show();
    let _ = window.set_focus();
    let _ = window.unminimize();

    let _ = app.emit("quick-action", payload);
    Ok(())
}

pub fn focus_main(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

/// Main starts invisible; show it only for normal launches.
pub fn apply_initial_launch(app: &AppHandle, payload: &LaunchPayload) -> Result<(), String> {
    {
        let state = app.state::<crate::AppState>();
        *state.pending_launch.lock().unwrap() = Some(payload.clone());
    }

    if payload.quick_action.is_some() {
        open_or_focus_quick(app, payload)?;
    } else {
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
