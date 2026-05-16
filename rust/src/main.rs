mod execx;
mod format;
mod hw;

use clap::{Parser, ValueEnum};
use std::path::PathBuf;
use std::process::ExitCode;

#[derive(Copy, Clone, Debug, ValueEnum)]
enum Format {
    Simple,
    Text,
    Json,
    Yaml,
    Markdown,
    Public,
}

#[derive(Parser, Debug)]
#[command(version, about = "Gather detailed information about your Mac.")]
struct Cli {
    #[arg(long, value_enum, default_value_t = Format::Simple)]
    format: Format,

    /// Read data from a fixture directory instead of running real commands.
    #[arg(long)]
    fixture_dir: Option<PathBuf>,
}

fn main() -> ExitCode {
    let cli = Cli::parse();

    let runner: Box<dyn execx::Runner> = match cli.fixture_dir {
        Some(dir) => Box::new(execx::Fixture { dir }),
        None => Box::new(execx::System),
    };

    let info = match hw::gather(runner.as_ref()) {
        Ok(i) => i,
        Err(e) => {
            eprintln!("error: {e}");
            return ExitCode::from(1);
        }
    };

    match cli.format {
        Format::Simple => println!("{}", format::simple(&info)),
        other => {
            eprintln!("format {other:?} not yet implemented in Rust port");
            return ExitCode::from(2);
        }
    }

    ExitCode::SUCCESS
}
