plugins {
    `java-library`
    `maven-publish`
}

group = "io.macp"
version = "0.1.3"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    withSourcesJar()
    withJavadocJar()
}

repositories {
    mavenCentral()
}

dependencies {
    // Floors MUST match what the pinned generators in buf/buf.gen.java.yaml emit
    // (protocolbuffers/java:v36.1 -> gencode 4.36.1, grpc/java:v1.84.0).
    // Bump the pins and these together — VERSIONING.md §8.
    api("com.google.protobuf:protobuf-java:4.36.1")
    api("io.grpc:grpc-protobuf:1.84.0")
    api("io.grpc:grpc-stub:1.84.0")
    compileOnly("org.apache.tomcat:annotations-api:6.0.53")
}

// Emits the resolved runtime classpath so CI can load-test the generated classes
// against the DECLARED floors (see scripts/java-loadtest/LoadTest.java).
tasks.register("printRuntimeClasspath") {
    val runtimeClasspath = configurations.named("runtimeClasspath")
    doLast { println(runtimeClasspath.get().asPath) }
}

publishing {
    publications {
        create<MavenPublication>("maven") {
            from(components["java"])
            pom {
                name.set("MACP Proto")
                description.set("Pre-generated Java protobuf and gRPC bindings for the Multi-Agent Coordination Protocol")
                url.set("https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol")
                licenses {
                    license {
                        name.set("Apache-2.0")
                        url.set("https://www.apache.org/licenses/LICENSE-2.0")
                    }
                }
            }
        }
    }
    repositories {
        maven {
            name = "GitHubPackages"
            url = uri("https://maven.pkg.github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol")
            credentials {
                username = System.getenv("GITHUB_ACTOR")
                password = System.getenv("GITHUB_TOKEN")
            }
        }
    }
}
