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
                info.processor = first_json_str(hw, &["chip_info", "chip_type", "cpu_type"]);
                apply_marketing_name(&mut info, &json_str(hw, "machine_name"));
                info.memory.total = normalize_memory_total(&json_str(hw, "physical_memory"));
            }
        }
    }

    let (memsize, _) = runner.run("sysctl", &["-n", "hw.memsize"])?;
    if let Some(total) = memory_gb(memsize.trim()) {
        info.memory.total = total;
    }
    if info.model_size.is_empty() {
        info.model_size = model_size_from_displays(runner)?;
    }
    if info.release_date.is_empty() {
        info.release_date = release_date_from_chip(&info.processor);
    }
    if info.model_year.is_empty() {
        info.model_year = first_year(&info.release_date);
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

fn first_json_str(v: &serde_json::Value, keys: &[&str]) -> String {
    for key in keys {
        let value = json_str(v, key);
        if !value.is_empty() {
            return value;
        }
    }
    String::new()
}

fn memory_gb(raw: &str) -> Option<String> {
    let bytes = raw.parse::<u64>().ok()?;
    if bytes == 0 {
        return None;
    }
    Some(format!("{}GB", bytes / 1024 / 1024 / 1024))
}

fn normalize_memory_total(raw: &str) -> String {
    raw.trim().replace(" GB", "GB")
}

fn apply_marketing_name(info: &mut Info, marketing_name: &str) {
    if marketing_name.is_empty() {
        return;
    }
    if let Some((name, _)) = marketing_name.split_once('(') {
        let name = name.trim();
        if !name.is_empty() {
            info.model_name = name.to_string();
        }
    }
    let size = model_size_from_marketing_name(marketing_name);
    if !size.is_empty() {
        info.model_size = size;
    }
    let year = first_year(marketing_name);
    if !year.is_empty() {
        info.model_year = year;
    }
}

fn model_size_from_marketing_name(name: &str) -> String {
    let Some(idx) = name.find("-inch") else {
        return String::new();
    };
    let bytes = name.as_bytes();
    let mut start = idx;
    while start > 0 && bytes[start - 1].is_ascii_digit() {
        start -= 1;
    }
    if start == idx {
        return String::new();
    }
    name[start..idx + "-inch".len()].to_string()
}

fn model_size_from_displays(runner: &dyn Runner) -> std::io::Result<String> {
    let (out, _) = runner.run("system_profiler", &["SPDisplaysDataType", "-json"])?;
    if out.is_empty() {
        return Ok(String::new());
    }
    let Ok(parsed) = serde_json::from_str::<serde_json::Value>(&out) else {
        return Ok(String::new());
    };
    let Some(cards) = parsed
        .get("SPDisplaysDataType")
        .and_then(serde_json::Value::as_array)
    else {
        return Ok(String::new());
    };
    for card in cards {
        let Some(displays) = card
            .get("spdisplays_ndrvs")
            .and_then(serde_json::Value::as_array)
        else {
            continue;
        };
        for display in displays {
            let connection = json_str(display, "spdisplays_connection_type").to_lowercase();
            if !connection.contains("internal") {
                continue;
            }
            let size = screen_size_from_resolution(&json_str(display, "_spdisplays_pixels"));
            if !size.is_empty() {
                return Ok(size);
            }
        }
    }
    Ok(String::new())
}

fn screen_size_from_resolution(resolution: &str) -> String {
    let normalized = resolution.to_lowercase();
    let Some((width, _)) = normalized.split_once('x') else {
        return String::new();
    };
    match width.trim().parse::<u32>() {
        Ok(3456) => "16-inch".to_string(),
        Ok(3024) => "14-inch".to_string(),
        Ok(2560 | 1440 | 1680) => "13-inch".to_string(),
        Ok(2880 | 1920) => "15-inch".to_string(),
        Ok(2304) => "12-inch".to_string(),
        _ => String::new(),
    }
}

fn release_date_from_chip(chip: &str) -> String {
    for (token, date) in [
        ("M4", "Mar 2024"),
        ("M3", "Oct 2023"),
        ("M2", "Jan 2023"),
        ("M1", "Nov 2020"),
    ] {
        if chip.contains(token) {
            return date.to_string();
        }
    }
    String::new()
}

fn first_year(value: &str) -> String {
    for field in value.split(|c: char| !c.is_ascii_digit()) {
        if field.len() == 4 && field.starts_with("20") {
            return field.to_string();
        }
    }
    String::new()
}
