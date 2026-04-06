/// Returns the absolute path to the directory containing MACP .proto files.
///
/// This is typically consumed via the Cargo `links` metadata mechanism
/// (`DEP_MACP_PROTO_PROTO_DIR` env var in downstream build scripts),
/// but is also available at runtime for tools that need it.
pub fn proto_dir() -> std::path::PathBuf {
    std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("proto")
}
