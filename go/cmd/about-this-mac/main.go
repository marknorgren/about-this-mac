package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/marknorgren/about-this-mac/go/internal/execx"
	"github.com/marknorgren/about-this-mac/go/internal/format"
	"github.com/marknorgren/about-this-mac/go/internal/hw"
)

func main() {
	formatFlag := flag.String("format", "simple", "Output format (simple|text|json|yaml|markdown|public)")
	fixtureDir := flag.String("fixture-dir", "", "Read data from fixture directory instead of running commands")
	flag.Parse()

	var runner execx.Runner = execx.System{}
	if *fixtureDir != "" {
		runner = execx.Fixture{Dir: *fixtureDir}
	}

	info, err := hw.Gather(runner)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}

	switch *formatFlag {
	case "simple":
		fmt.Println(format.Simple(info))
	default:
		fmt.Fprintf(os.Stderr, "format %q not yet implemented in Go port\n", *formatFlag)
		os.Exit(2)
	}
}
