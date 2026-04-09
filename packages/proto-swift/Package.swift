// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MACPProto",
    platforms: [
        .macOS(.v13),
        .iOS(.v16),
    ],
    products: [
        .library(name: "MACPProto", targets: ["MACPProto"]),
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-protobuf.git", from: "1.28.0"),
        .package(url: "https://github.com/grpc/grpc-swift.git", from: "2.0.0"),
        .package(url: "https://github.com/grpc/grpc-swift-protobuf.git", from: "1.0.0"),
    ],
    targets: [
        .target(
            name: "MACPProto",
            dependencies: [
                .product(name: "SwiftProtobuf", package: "swift-protobuf"),
                .product(name: "GRPCCore", package: "grpc-swift"),
                .product(name: "GRPCProtobuf", package: "grpc-swift-protobuf"),
            ],
            path: "Sources/MACPProto"
        ),
    ]
)
