package execx

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

type Runner interface {
	Run(cmd string, args ...string) (stdout string, exitCode int, err error)
}

type System struct{}

func (System) Run(cmd string, args ...string) (string, int, error) {
	c := exec.Command(cmd, args...)
	out, err := c.Output()
	exit := 0
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			exit = ee.ExitCode()
		} else {
			return "", -1, err
		}
	}
	return string(out), exit, nil
}

type Fixture struct {
	Dir string
}

func (f Fixture) Run(cmd string, args ...string) (string, int, error) {
	path := filepath.Join(f.Dir, FixtureKey(cmd, args)+".txt")
	b, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return "", 1, nil
		}
		return "", -1, err
	}
	return string(b), 0, nil
}

func FixtureKey(cmd string, args []string) string {
	parts := []string{sanitize(cmd)}
	for _, a := range args {
		parts = append(parts, sanitize(a))
	}
	return strings.Join(parts, "__")
}

func sanitize(s string) string {
	r := strings.NewReplacer("/", "_", " ", "_")
	return r.Replace(s)
}
