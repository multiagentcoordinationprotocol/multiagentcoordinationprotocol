#!/usr/bin/env python3
"""Split RFC-MACP-0014 A2A objects out for validation against macp-a2a-binding.schema.json.

ajv-cli validates a document against a whole schema file, not against one of its
$defs, so validate-json.sh needs two things this script provides:

  wrap <schema> <out-dir>
      For every $def in the A2A binding schema, write <out-dir>/a2a-<Def>.schema.json:
      a copy of the schema whose root is {"$ref": "#/$defs/<Def>"}. Copying (rather
      than a one-line wrapper that $refs the schema by $id) keeps ajv's schemaPaths
      rooted at "#/$defs/<Def>/...", which the fixture-isolation guard groups on.
      Prints one <Def> per line.

  extract <transcript> <out-dir>
      Find each A2A object in an RFC-MACP-0014 transcript (examples/a2a-binding-session.json)
      by its POSITION, never by the property the schema checks, so a malformed object
      is validated and fails instead of being skipped:
        AgentExtension        capabilities.extensions[*] whose uri is under the MACP
                              extension prefix (any version, so a wrong /vN still lands here)
        EnvelopePart          any object whose mediaType starts application/macp-envelope
        AckMessage            result.message of a JSON-RPC response
        ObservationArtifact   artifactUpdate.artifact, and every Task.artifacts[*]
        SessionStateMetadata  the metadata (or {} if absent) of every object whose
                              status.state is a TASK_STATE_* value: a Task or a
                              TaskStatusUpdateEvent
        ErrorInfo             error.data[*] with the google.rpc.ErrorInfo @type and the
                              MACP domain -- the selection rule of RFC-MACP-0014 §11.1.
                              Because that rule keys on the very domain the schema pins,
                              this script also fails unless EVERY JSON-RPC error object
                              carries exactly one such entry (§11.1: every A2A error the
                              binding produces MUST carry one).
      Writes <out-dir>/<Def>__NNN.json per object and prints "<Def>\t<path>" per object.

Stdlib only.
"""
import json
import os
import sys

EXT_PREFIX = "https://multiagentcoordinationprotocol.io/a2a/extensions/macp/"
ERRORINFO_TYPE = "type.googleapis.com/google.rpc.ErrorInfo"
MACP_DOMAIN = "multiagentcoordinationprotocol.io"


def wrap(schema_path, out_dir):
    with open(schema_path) as f:
        schema = json.load(f)
    for name in schema.get("$defs", {}):
        copy = dict(schema)
        copy["$ref"] = "#/$defs/" + name
        with open(os.path.join(out_dir, "a2a-%s.schema.json" % name), "w") as f:
            json.dump(copy, f)
        print(name)


def extract(transcript_path, out_dir):
    with open(transcript_path) as f:
        doc = json.load(f)
    found = []
    bad = []

    def walk(node, path):
        if isinstance(node, dict):
            media = node.get("mediaType")
            if isinstance(media, str) and media.startswith("application/macp-envelope"):
                found.append(("EnvelopePart", node, path))
            caps = node.get("capabilities")
            if isinstance(caps, dict) and isinstance(caps.get("extensions"), list):
                for i, e in enumerate(caps["extensions"]):
                    if isinstance(e, dict) and str(e.get("uri", "")).startswith(EXT_PREFIX):
                        found.append(("AgentExtension", e, "%s/capabilities/extensions/%d" % (path, i)))
            res = node.get("result")
            if isinstance(res, dict) and "message" in res:
                found.append(("AckMessage", res["message"], path + "/result/message"))
            if "artifact" in node:
                found.append(("ObservationArtifact", node["artifact"], path + "/artifact"))
            if isinstance(node.get("artifacts"), list):
                for i, a in enumerate(node["artifacts"]):
                    found.append(("ObservationArtifact", a, "%s/artifacts/%d" % (path, i)))
            status = node.get("status")
            if isinstance(status, dict) and str(status.get("state", "")).startswith("TASK_STATE_"):
                found.append(("SessionStateMetadata", node.get("metadata", {}), path + "/metadata"))
            err = node.get("error")
            if isinstance(err, dict) and "code" in err:
                data = err.get("data") if isinstance(err.get("data"), list) else []
                hits = [d for d in data if isinstance(d, dict)
                        and d.get("@type") == ERRORINFO_TYPE and d.get("domain") == MACP_DOMAIN]
                if len(hits) != 1:
                    bad.append("%s/error carries %d MACP ErrorInfo entries, not exactly 1 "
                               "(RFC-MACP-0014 §11.1)" % (path, len(hits)))
                for h in hits:
                    found.append(("ErrorInfo", h, path + "/error/data"))
            for k, v in node.items():
                walk(v, "%s/%s" % (path, k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, "%s/%d" % (path, i))

    walk(doc, "")
    if bad:
        for b in bad:
            print("[X] " + b, file=sys.stderr)
        sys.exit(1)
    for i, (name, obj, path) in enumerate(found):
        with open(os.path.join(out_dir, "%s__%03d.json" % (name, i)), "w") as f:
            json.dump(obj, f)
        print("%s\t%s" % (name, path or "/"))


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("wrap", "extract"):
        print("usage: extract-a2a-objects.py wrap|extract <input> <out-dir>", file=sys.stderr)
        sys.exit(2)
    (wrap if sys.argv[1] == "wrap" else extract)(sys.argv[2], sys.argv[3])
