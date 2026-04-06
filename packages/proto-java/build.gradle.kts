plugins {
    `java-library`
    `maven-publish`
}

group = "io.macp"
version = "0.1.0"

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
    api("com.google.protobuf:protobuf-java:4.29.3")
    api("io.grpc:grpc-protobuf:1.72.0")
    api("io.grpc:grpc-stub:1.72.0")
    compileOnly("org.apache.tomcat:annotations-api:6.0.53")
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
