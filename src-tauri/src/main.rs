#![cfg_attr(
  all(not(debug_assertions), target_os = "windows"),
  windows_subsystem = "windows"
)]

use tauri::api::process::{Command, CommandEvent};
use tauri::Manager;
use std::collections::HashMap;
use std::time::Duration;
use async_std::task;

fn main() {
  tauri::Builder::default()
    .setup(|app| {
      let splashscreen_window = app.get_window("splashscreen").unwrap();
      let main_window = app.get_window("main").unwrap();

      // Enhanced macOS DPI handling
      #[cfg(target_os = "macos")]
      {
        use tauri::LogicalSize;

        // Try to get the current monitor information
        if let Ok(Some(monitor)) = main_window.current_monitor() {
          let scale_factor = monitor.scale_factor();
          println!("Display scale factor: {}", scale_factor);

          // Force devicePixelRatio to 1 in the webview
          let dpi_script = r#"
            // Override devicePixelRatio
            Object.defineProperty(window, 'devicePixelRatio', {
              get: function() { return 1; },
              configurable: true
            });

            // Add CSS to compensate for any remaining scaling
            const style = document.createElement('style');
            style.textContent = `
              html, body {
                -webkit-text-size-adjust: 100%;
                -webkit-font-smoothing: antialiased;
                zoom: 1;
                transform: scale(1);
                transform-origin: 0 0;
              }
              * {
                image-rendering: -webkit-optimize-contrast;
                image-rendering: crisp-edges;
              }
            `;
            document.head.appendChild(style);

            console.log('DPI override applied, devicePixelRatio:', window.devicePixelRatio);
          "#;

          // Apply the DPI override script
          let _ = main_window.eval(dpi_script);

          // If on a high DPI display (Retina), adjust window size for better appearance
          if scale_factor > 1.5 {
            // Set a larger logical size that will look crisp
            let size = LogicalSize::new(1200.0, 800.0);
            let _ = main_window.set_size(size);
            println!("Adjusted window size to 1200x800 for Retina display");
          }
        }
      }

      let mut env = HashMap::new();
      env.insert("PYTHONUNBUFFERED".to_string(), "1".to_string());

      let (mut rx, _) = Command::new_sidecar("trame")
        .expect("failed to create sidecar")
        .args(["--server", "--port", "0", "--timeout", "10", "--user-home"])
        .envs(env)
        .spawn()
        .expect("Failed to spawn server");

      tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
          match event {
            CommandEvent::Stdout(line) => {
              println!("Stdout: {}", line);
              if line.contains("tauri-server-port=") {
                let tokens: Vec<&str> = line.split("=").collect();
                let port_token = tokens[1].to_string();
                let port = port_token.trim();

                // Navigate and apply DPI settings
                let navigation_script = format!(
                  r#"
                  window.location.replace(window.location.href + '?sessionURL=ws://localhost:{}/ws');

                  // Ensure DPI override persists after navigation
                  window.addEventListener('load', function() {{
                    Object.defineProperty(window, 'devicePixelRatio', {{
                      get: function() {{ return 1; }},
                      configurable: true
                    }});
                    console.log('Post-navigation DPI override applied');
                  }});
                  "#,
                  port
                );

                let _ = main_window.eval(&navigation_script);
              }
              if line.contains("tauri-client-ready") {
                task::sleep(Duration::from_secs(2)).await;

                // Apply final DPI settings before showing main window
                #[cfg(target_os = "macos")]
                {
                  let final_dpi_script = r#"
                    // Final DPI override
                    Object.defineProperty(window, 'devicePixelRatio', {
                      get: function() { return 1; },
                      configurable: true
                    });

                    // Force a repaint
                    document.body.style.display = 'none';
                    document.body.offsetHeight; // Trigger reflow
                    document.body.style.display = '';

                    console.log('Final devicePixelRatio:', window.devicePixelRatio);
                  "#;
                  let _ = main_window.eval(final_dpi_script);
                }

                splashscreen_window.close().unwrap();
                main_window.show().unwrap();
              }
            },
            CommandEvent::Stderr(line) => {
              println!("Stderr: {}", line);
            },
            CommandEvent::Error(error) => {
              println!("[Trame error] {}", error);
            },
            CommandEvent::Terminated(code) => {
              println!("[Trame exited] with code {:?}", code);
            },
            _ => {},
          }
        }
      });
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running application");
}
