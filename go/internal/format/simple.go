package format

import (
	"fmt"
	"strings"

	"github.com/marknorgren/about-this-mac/go/internal/hw"
)

// Simple renders the macOS About-This-Mac-style summary, byte-equivalent to
// the Python format_output_as_simple output. Phase 1: minimal shape; will be
// extended once fixtures land.
func Simple(info hw.Info) string {
	device := deviceDisplayName(info)
	sizeDate := info.ModelSize
	if info.ReleaseDate != "" {
		if sizeDate == "" {
			sizeDate = info.ReleaseDate
		} else {
			sizeDate = sizeDate + ", " + info.ReleaseDate
		}
	}
	memory := strings.Replace(info.Memory.Total, "GB", " GB", 1)
	chip := strings.TrimSpace(strings.ReplaceAll(info.Processor, ":", ""))
	if chip == "" {
		chip = "Unknown"
	}
	macos := macosVersionName(info.MacOSVersion)

	return strings.Join([]string{
		device,
		sizeDate,
		"",
		fmt.Sprintf("Chip          %s", chip),
		fmt.Sprintf("Memory        %s", memory),
		"Startup disk  Macintosh HD",
		fmt.Sprintf("Serial number %s", orUnknown(info.SerialNumber)),
		fmt.Sprintf("macOS         %s", macos),
	}, "\n")
}

func deviceDisplayName(info hw.Info) string {
	if info.ModelName != "" {
		return info.ModelName
	}
	if info.DeviceIdentifier != "" {
		return info.DeviceIdentifier
	}
	return "Mac"
}

func macosVersionName(v string) string {
	prefixes := [][2]string{
		{"15", "Sequoia"},
		{"14", "Sonoma"},
		{"13", "Ventura"},
		{"12", "Monterey"},
		{"11", "Big Sur"},
	}
	for _, p := range prefixes {
		if strings.HasPrefix(v, p[0]) {
			return p[1] + " " + v
		}
	}
	return v
}

func orUnknown(s string) string {
	if strings.TrimSpace(s) == "" {
		return "Unknown"
	}
	return s
}
