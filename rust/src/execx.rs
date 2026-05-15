use std::path::PathBuf;
use std::process::Command;

pub trait Runner {
    fn run(&self, cmd: &str, args: &[&str]) -> std::io::Result<(String, i32)>;
}

pub struct System;

impl Runner for System {
    fn run(&self, cmd: &str, args: &[&str]) -> std::io::Result<(String, i32)> {
        let output = Command::new(cmd).args(args).output()?;
        let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
        let code = output.status.code().unwrap_or(-1);
        Ok((stdout, code))
    }
}

pub struct Fixture {
    pub dir: PathBuf,
}

impl Runner for Fixture {
    fn run(&self, cmd: &str, args: &[&str]) -> std::io::Result<(String, i32)> {
        let path = self.dir.join(format!("{}.txt", fixture_key(cmd, args)));
        match std::fs::read_to_string(&path) {
            Ok(s) => Ok((s, 0)),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok((String::new(), 1)),
            Err(e) => Err(e),
        }
    }
}

pub fn fixture_key(cmd: &str, args: &[&str]) -> String {
    let mut parts: Vec<String> = vec![sanitize(cmd)];
    for a in args {
        parts.push(sanitize(a));
    }
    parts.join("__")
}

fn sanitize(s: &str) -> String {
    s.replace('/', "_").replace(' ', "_")
}
