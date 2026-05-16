package hw

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/marknorgren/about-this-mac/go/internal/execx"
)

func TestGatherPopulatesSimpleParityFields(t *testing.T) {
	dir := t.TempDir()
	writeFixture(t, dir, "system_profiler__SPHardwareDataType__-json.txt", `{
		"SPHardwareDataType": [{
			"machine_name": "MacBook Pro",
			"machine_model": "Mac16,6",
			"model_number": "G1FGULL/A",
			"serial_number": "SER123",
			"chip_type": "Apple M4 Max",
			"physical_memory": "128 GB"
		}]
	}`)
	writeFixture(t, dir, "system_profiler__SPDisplaysDataType__-json.txt", `{
		"SPDisplaysDataType": [{
			"spdisplays_ndrvs": [{
				"_spdisplays_pixels": "3024 x 1964",
				"spdisplays_connection_type": "spdisplays_internal"
			}]
		}]
	}`)
	writeFixture(t, dir, "sysctl__-n__hw.memsize.txt", "137438953472")
	writeFixture(t, dir, "sw_vers__-productVersion.txt", "26.4.1")

	info, err := Gather(execx.Fixture{Dir: dir})
	if err != nil {
		t.Fatal(err)
	}

	if info.Processor != "Apple M4 Max" {
		t.Fatalf("processor = %q", info.Processor)
	}
	if info.Memory.Total != "128GB" {
		t.Fatalf("memory total = %q", info.Memory.Total)
	}
	if info.ModelSize != "14-inch" {
		t.Fatalf("model size = %q", info.ModelSize)
	}
	if info.ReleaseDate != "Mar 2024" {
		t.Fatalf("release date = %q", info.ReleaseDate)
	}
	if info.ModelYear != "2024" {
		t.Fatalf("model year = %q", info.ModelYear)
	}
	if info.MacOSVersion != "26.4.1" {
		t.Fatalf("macOS version = %q", info.MacOSVersion)
	}
}

func writeFixture(t *testing.T, dir string, name string, body string) {
	t.Helper()
	path := filepath.Join(dir, name)
	if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
}
