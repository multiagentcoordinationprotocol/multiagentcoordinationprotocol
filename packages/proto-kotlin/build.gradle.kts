plugins {
    kotlin("jvm") version "2.1.21"
    `java-library`
    `maven-publish`
}

group = "io.macp"
version = "0.1.0"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    withSourcesJar()
}

repositories {
    mavenLocal()
    maven {
        name = "GitHubPackages"
        url = uri("https://maven.pkg.github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol")
        credentials {
            username = System.getenv("GITHUB_ACTOR") ?: ""
            password = System.getenv("GITHUB_TOKEN") ?: ""
        }
    }
    mavenCentral()
}

dependencies {
    api("io.macp:macp-proto:0.1.0")
    api("com.google.protobuf:protobuf-kotlin:4.34.1")
    api("io.grpc:grpc-kotlin-stub:1.4.3")
    api("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
}

publishing {
    publications {
        create<MavenPublication>("maven") {
            from(components["java"])
            pom {
                name.set("MACP Proto Kotlin")
                description.set("Kotlin DSL extensions for the MACP protobuf bindings")
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
