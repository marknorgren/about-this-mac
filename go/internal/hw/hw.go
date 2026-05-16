package hw

import (
	"encoding/json"
	"strconv"
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

type spDisplays struct {
	SPDisplaysDataType []struct {
		Displays []struct {
			Pixels     string `json:"_spdisplays_pixels"`
			Connection string `json:"spdisplays_connection_type"`
		} `json:"spdisplays_ndrvs"`
	} `json:"SPDisplaysDataType"`
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
			info.Processor = firstString(hw, "chip_info", "chip_type", "cpu_type")
			applyMarketingName(&info, info.ModelName)
		}
	}

	if mem, _, _ := r.Run("sysctl", "-n", "hw.memsize"); mem != "" {
		info.Memory.Total = memoryGB(strings.TrimSpace(mem))
	}
	if info.Memory.Total == "" && out != "" {
		var parsed spHardware
		if jerr := json.Unmarshal([]byte(out), &parsed); jerr == nil && len(parsed.SPHardwareDataType) > 0 {
			info.Memory.Total = normalizeMemoryTotal(asString(parsed.SPHardwareDataType[0]["physical_memory"]))
		}
	}
	if info.ModelSize == "" {
		info.ModelSize = modelSizeFromDisplays(r)
	}
	if info.ReleaseDate == "" {
		info.ReleaseDate = releaseDateFromChip(info.Processor)
	}
	if info.ModelYear == "" {
		info.ModelYear = yearFromReleaseDate(info.ReleaseDate)
	}

	if ver, _, _ := r.Run("sw_vers", "-productVersion"); ver != "" {
		info.MacOSVersion = strings.TrimSpace(ver)
	}

	return info, nil
}

func firstString(values map[string]any, keys ...string) string {
	for _, key := range keys {
		if value := asString(values[key]); value != "" {
			return value
		}
	}
	return ""
}

func asString(v any) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

func memoryGB(raw string) string {
	bytes, err := strconv.ParseInt(strings.TrimSpace(raw), 10, 64)
	if err != nil || bytes <= 0 {
		return ""
	}
	return strconv.FormatInt(bytes/(1024*1024*1024), 10) + "GB"
}

func normalizeMemoryTotal(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ""
	}
	return strings.ReplaceAll(raw, " GB", "GB")
}

func applyMarketingName(info *Info, marketingName string) {
	if marketingName == "" {
		return
	}
	if before, _, ok := strings.Cut(marketingName, "("); ok {
		if name := strings.TrimSpace(before); name != "" {
			info.ModelName = name
		}
	}
	if size := modelSizeFromMarketingName(marketingName); size != "" {
		info.ModelSize = size
	}
	if year := firstYear(marketingName); year != "" {
		info.ModelYear = year
	}
}

func modelSizeFromMarketingName(name string) string {
	idx := strings.Index(name, "-inch")
	if idx == -1 {
		return ""
	}
	start := idx
	for start > 0 && name[start-1] >= '0' && name[start-1] <= '9' {
		start--
	}
	if start == idx {
		return ""
	}
	return name[start : idx+len("-inch")]
}

func modelSizeFromDisplays(r execx.Runner) string {
	out, _, err := r.Run("system_profiler", "SPDisplaysDataType", "-json")
	if err != nil || out == "" {
		return ""
	}
	var parsed spDisplays
	if err := json.Unmarshal([]byte(out), &parsed); err != nil {
		return ""
	}
	for _, card := range parsed.SPDisplaysDataType {
		for _, display := range card.Displays {
			if !strings.Contains(strings.ToLower(display.Connection), "internal") {
				continue
			}
			if size := screenSizeFromResolution(display.Pixels); size != "" {
				return size
			}
		}
	}
	return ""
}

func screenSizeFromResolution(resolution string) string {
	parts := strings.Split(strings.ToLower(resolution), "x")
	if len(parts) == 0 {
		return ""
	}
	width, err := strconv.Atoi(strings.TrimSpace(parts[0]))
	if err != nil {
		return ""
	}
	switch width {
	case 3456:
		return "16-inch"
	case 3024:
		return "14-inch"
	case 2560, 1440, 1680:
		return "13-inch"
	case 2880, 1920:
		return "15-inch"
	case 2304:
		return "12-inch"
	default:
		return ""
	}
}

func releaseDateFromChip(chip string) string {
	for _, candidate := range []struct {
		token string
		date  string
	}{
		{"M4", "Mar 2024"},
		{"M3", "Oct 2023"},
		{"M2", "Jan 2023"},
		{"M1", "Nov 2020"},
	} {
		if strings.Contains(chip, candidate.token) {
			return candidate.date
		}
	}
	return ""
}

func yearFromReleaseDate(date string) string {
	return firstYear(date)
}

func firstYear(s string) string {
	fields := strings.FieldsFunc(s, func(r rune) bool { return r < '0' || r > '9' })
	for _, field := range fields {
		if len(field) == 4 && strings.HasPrefix(field, "20") {
			return field
		}
	}
	return ""
}
