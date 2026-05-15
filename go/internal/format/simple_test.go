package format

import (
	"testing"

	"github.com/marknorgren/about-this-mac/go/internal/hw"
)

func TestSimpleMatchesShape(t *testing.T) {
	info := hw.Info{
		ModelName:    "MacBook Pro",
		ModelSize:    "14-inch",
		ReleaseDate:  "Mar 2024",
		Processor:    "Apple M3",
		SerialNumber: "ABC123",
		MacOSVersion: "14.4",
	}
	info.Memory.Total = "16GB"

	got := Simple(info)
	want := "MacBook Pro\n" +
		"14-inch, Mar 2024\n" +
		"\n" +
		"Chip          Apple M3\n" +
		"Memory        16 GB\n" +
		"Startup disk  Macintosh HD\n" +
		"Serial number ABC123\n" +
		"macOS         Sonoma 14.4"

	if got != want {
		t.Errorf("simple format mismatch\n--- got ---\n%s\n--- want ---\n%s", got, want)
	}
}
