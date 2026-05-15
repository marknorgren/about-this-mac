use crate::execx::Runner;
use serde::{Deserialize, Serialize};

#[derive(Default, Debug, Serialize, Deserialize)]
pub struct Memory {
    pub total: String,
    pub r#type: String,
    pub speed: String,
    pub manufacturer: String,
    pub ecc: bool,
}

#[derive(Default, Debug, Serialize, Deserialize)]
pub struct Storage {
    pub name: String,
    pub model: String,
    pub revision: String,
    pub serial: String,
    pub size: String,
    pub r#type: String,
    pub protocol: String,
    pub trim: bool,
    pub smart_status: String,
    pub removable: bool,
    pub internal: bool,
}

#[derive(Default, Debug, Serialize, Deserialize)]
pub struct Info {
    pub model_name: String,
    pub device_identifier: String,
    pub model_number: String,
    pub serial_number: String,
    pub processor: String,
    pub cpu_cores: u32,
    pub performance_cores: u32,
    pub efficiency_cores: u32,
    pub gpu_cores: u32,
    pub memory: Memory,
    pub storage: Storage,
    pub graphics: Vec<std::collections::BTreeMap<String, String>>,
    pub bluetooth_chipset: String,
    pub bluetooth_firmware: String,
    pub bluetooth_transport: String,
    pub macos_version: String,
    pub macos_build: String,
    pub uptime: Option<i64>,
    pub release_date: String,
    pub model_size: String,
    pub model_year: String,
}

#[derive(Deserialize)]
struct SpHardware {
    #[serde(rename = "SPHardwareDataType")]
    items: Vec<serde_json::Value>,
}

/// Gather collects hardware info via the provided runner. Phase 1 stub:
/// populates only what `--format simple` needs. Will be extended field by
/// field, byte-parity tested against Python output.
pub fn gather(runner: &dyn Runner) -> std::io::Result<Info> {
    let mut info = Info::default();

    let (out, _code) = runner.run("system_profiler", &["SPHardwareDataType", "-json"])?;
    if !out.is_empty() {
        if let Ok(parsed) = serde_json::from_str::<SpHardware>(&out) {
            if let Some(hw) = parsed.items.first() {
                info.model_name = json_str(hw, "machine_name");
                info.device_identifier = json_str(hw, "machine_model");
                info.model_number = json_str(hw, "model_number");
                info.serial_number = json_str(hw, "serial_number");
                info.processor = {
                    let chip = json_str(hw, "chip_info");
                    if chip.is_empty() {
                        json_str(hw, "cpu_type")
                    } else {
                        chip
                    }
                };
            }
        }
    }

    let (ver, _) = runner.run("sw_vers", &["-productVersion"])?;
    if !ver.is_empty() {
        info.macos_version = ver.trim().to_string();
    }

    Ok(info)
}

fn json_str(v: &serde_json::Value, key: &str) -> String {
    v.get(key)
        .and_then(|x| x.as_str())
        .unwrap_or_default()
        .to_string()
}
