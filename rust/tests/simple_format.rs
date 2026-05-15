// Integration test: byte-shape of the simple format.
// The unit-level format module is private; we exercise it by running the
// binary against a tiny synthetic fixture directory.

use std::fs;
use std::process::Command;

fn target_bin() -> String {
    // CARGO sets CARGO_BIN_EXE_<name> for integration tests.
    env!("CARGO_BIN_EXE_about-this-mac").to_string()
}

#[test]
fn simple_format_shape() {
    let tmp = tempdir();
    let hardware_json = r#"{
        "SPHardwareDataType": [{
            "machine_name": "MacBook Pro",
            "machine_model": "Mac15,3",
            "model_number": "MRX33LL/A",
            "serial_number": "ABC123",
            "chip_info": "Apple M3"
        }]
    }"#;
    fs::write(
        tmp.join("system_profiler__SPHardwareDataType__-json.txt"),
        hardware_json,
    )
    .unwrap();
    fs::write(tmp.join("sw_vers__-productVersion.txt"), "14.4").unwrap();

    let out = Command::new(target_bin())
        .args([
            "--fixture-dir",
            tmp.to_str().unwrap(),
            "--format",
            "simple",
        ])
        .output()
        .expect("run binary");
    assert!(
        out.status.success(),
        "binary failed: stderr={}",
        String::from_utf8_lossy(&out.stderr)
    );
    let got = String::from_utf8_lossy(&out.stdout);
    // strip trailing newline added by println!
    let got = got.trim_end_matches('\n');

    // Phase 1: memory/model_size/release_date are not yet populated by the
    // gatherer, so this assertion pins the current stub shape. It will tighten
    // as fields are filled in port-by-port, byte-checked against Python.
    let want = "MacBook Pro\n\
                \n\
                \n\
                Chip          Apple M3\n\
                Memory        \n\
                Startup disk  Macintosh HD\n\
                Serial number ABC123\n\
                macOS         Sonoma 14.4";

    assert_eq!(got, want, "\n--- got ---\n{got}\n--- want ---\n{want}");
}

fn tempdir() -> std::path::PathBuf {
    let p = std::env::temp_dir().join(format!("atm-test-{}", std::process::id()));
    std::fs::create_dir_all(&p).unwrap();
    p
}
