use crate::hw::Info;

/// Render the macOS About-This-Mac-style summary. Target: byte-identical to
/// the Python `format_output_as_simple`. Phase 1 minimal shape.
pub fn simple(info: &Info) -> String {
    let device = device_display_name(info);
    let size_date = if info.release_date.is_empty() {
        info.model_size.clone()
    } else if info.model_size.is_empty() {
        info.release_date.clone()
    } else {
        format!("{}, {}", info.model_size, info.release_date)
    };
    let memory = info.memory.total.replacen("GB", " GB", 1);
    let chip = info.processor.replace(':', "");
    let chip = chip.trim();
    let chip = if chip.is_empty() { "Unknown" } else { chip };
    let macos = macos_version_name(&info.macos_version);
    let serial = if info.serial_number.trim().is_empty() {
        "Unknown".to_string()
    } else {
        info.serial_number.clone()
    };

    [
        device,
        size_date,
        String::new(),
        format!("Chip          {}", chip),
        format!("Memory        {}", memory),
        "Startup disk  Macintosh HD".to_string(),
        format!("Serial number {}", serial),
        format!("macOS         {}", macos),
    ]
    .join("\n")
}

fn device_display_name(info: &Info) -> String {
    if !info.model_name.is_empty() {
        return info.model_name.clone();
    }
    if !info.device_identifier.is_empty() {
        return info.device_identifier.clone();
    }
    "Mac".to_string()
}

fn macos_version_name(v: &str) -> String {
    for (prefix, name) in [
        ("15", "Sequoia"),
        ("14", "Sonoma"),
        ("13", "Ventura"),
        ("12", "Monterey"),
        ("11", "Big Sur"),
    ] {
        if v.starts_with(prefix) {
            return format!("{} {}", name, v);
        }
    }
    v.to_string()
}
