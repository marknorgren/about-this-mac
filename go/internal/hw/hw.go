package hw

import (
	"encoding/json"
	"strings"

	"github.com/marknorgren/about-this-mac/go/internal/execx"
)

type Memory struct {
	Total        string `json:"total"`
	Type         string `json:"type"`
	Speed        string `json:"speed"`
	Manufacturer string `json:"manufacturer"`
	ECC          bool   `json:"ecc"`
}

type Storage struct {
	Name        string `json:"name"`
	Model       string `json:"model"`
	Revision    string `json:"revision"`
	Serial      string `json:"serial"`
	Size        string `json:"size"`
	Type        string `json:"type"`
	Protocol    string `json:"protocol"`
	Trim        bool   `json:"trim"`
	SmartStatus string `json:"smart_status"`
	Removable   bool   `json:"removable"`
	Internal    bool   `json:"internal"`
}

type Info struct {
	ModelName         string              `json:"model_name"`
	DeviceIdentifier  string              `json:"device_identifier"`
	ModelNumber       string              `json:"model_number"`
	SerialNumber      string              `json:"serial_number"`
	Processor         string              `json:"processor"`
	CPUCores          int                 `json:"cpu_cores"`
	PerformanceCores  int                 `json:"performance_cores"`
	EfficiencyCores   int                 `json:"efficiency_cores"`
	GPUCores          int                 `json:"gpu_cores"`
	Memory            Memory              `json:"memory"`
	Storage           Storage             `json:"storage"`
	Graphics          []map[string]string `json:"graphics"`
	BluetoothChipset  string              `json:"bluetooth_chipset"`
	BluetoothFirmware string              `json:"bluetooth_firmware"`
	BluetoothTrans    string              `json:"bluetooth_transport"`
	MacOSVersion      string              `json:"macos_version"`
	MacOSBuild        string              `json:"macos_build"`
	Uptime            *int64              `json:"uptime"`
	ReleaseDate       string              `json:"release_date"`
	ModelSize         string              `json:"model_size"`
	ModelYear         string              `json:"model_year"`
}

type spHardware struct {
	SPHardwareDataType []map[string]any `json:"SPHardwareDataType"`
}

// Gather collects hardware info via the provided runner. This is a phase-1
// stub: it populates the bare minimum needed for --format simple. Subsequent
// patches will fill in the rest field-by-field, with byte-parity tests against
// Python output.
func Gather(r execx.Runner) (Info, error) {
	var info Info

	out, _, err := r.Run("system_profiler", "SPHardwareDataType", "-json")
	if err == nil && out != "" {
		var parsed spHardware
		if jerr := json.Unmarshal([]byte(out), &parsed); jerr == nil && len(parsed.SPHardwareDataType) > 0 {
			hw := parsed.SPHardwareDataType[0]
			info.ModelName = asString(hw["machine_name"])
			info.DeviceIdentifier = asString(hw["machine_model"])
			info.ModelNumber = asString(hw["model_number"])
			info.SerialNumber = asString(hw["serial_number"])
			info.Processor = asString(hw["chip_info"])
			if info.Processor == "" {
				info.Processor = asString(hw["cpu_type"])
			}
		}
	}

	if ver, _, _ := r.Run("sw_vers", "-productVersion"); ver != "" {
		info.MacOSVersion = strings.TrimSpace(ver)
	}

	return info, nil
}

func asString(v any) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}
