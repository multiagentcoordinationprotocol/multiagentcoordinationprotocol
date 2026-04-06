fn main() {
    let proto_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("proto");
    println!("cargo::metadata=proto_dir={}", proto_dir.display());
}
