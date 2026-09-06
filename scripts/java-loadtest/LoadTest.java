/**
 * Loads generated protobuf/gRPC classes against the runtime versions declared in
 * packages/proto-java/build.gradle.kts.
 *
 * This exists because compiling is not sufficient. protobuf-java gencode calls
 * RuntimeVersion.validateProtobufGencodeVersion(...) from a static initializer,
 * so a gencode/floor mismatch compiles clean and throws only at class load —
 * exactly the failure in issue #53, which published four unusable artifacts
 * while CI was green. Class loading is the cheapest check that actually
 * exercises the assertion.
 *
 * See VERSIONING.md §8.
 */
public class LoadTest {
    private static final String[] CLASSES = {
        "io.macp.proto.macp.v1.Envelope",
        "io.macp.proto.macp.v1.MACPRuntimeServiceGrpc",
    };

    public static void main(String[] args) throws Exception {
        for (String name : CLASSES) {
            Class.forName(name);
            System.out.println("  loaded " + name);
        }
        System.out.println("Java gencode loads at the declared floors OK");
    }
}
