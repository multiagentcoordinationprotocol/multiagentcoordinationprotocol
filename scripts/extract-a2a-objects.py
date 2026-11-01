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
      by its POSITION wherever it can, so a malformed object is validated and fails
      instead of being skipped:
        AgentExtension        capabilities.extensions[*] whose uri is under the MACP
                              extension prefix (any version, so a wrong /vN still lands
                              here). A card with no such entry, or with two, fails.
        EnvelopePart          any object whose mediaType starts application/macp-envelope.
                              This one is selected by the pinned property itself, so two
                              positional guards back it up: every SendMessage request
                              (all of them carry an Envelope here) MUST have exactly one
                              such Part (§5.1), and Artifact parts reach EnvelopePart
                              through ObservationArtifact.parts.items anyway.
        AckMessage            result.message of a JSON-RPC response. A SendMessage
                              response whose result is not a Message fails (§5.2).
        ObservationArtifact   artifactUpdate.artifact, and every Task.artifacts[*]
        SessionStateMetadata  the metadata (or {} if absent) of every object whose
                              status.state is a TASK_STATE_* value: a Task or a
                              TaskStatusUpdateEvent
        ErrorInfo             error.data[*] with the google.rpc.ErrorInfo @type and the
                              MACP domain -- the selection rule of RFC-MACP-0014 §11.1.
                              Because that rule keys on the very domain the schema pins,
                              an entry with a wrong domain is dropped rather than failed;
                              the per-$def count validate-json.sh pins catches that drop.
                              Not every A2A error carries one (VersionNotSupportedError has
                              no MACP reason, §11.3), so absence alone is not an error; two
                              entries in one error are.
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
                n = 0
                for i, e in enumerate(caps["extensions"]):
                    if isinstance(e, dict) and str(e.get("uri", "")).startswith(EXT_PREFIX):
                        n += 1
                        found.append(("AgentExtension", e, "%s/capabilities/extensions/%d" % (path, i)))
                if n != 1:
                    bad.append("%s/capabilities/extensions declares the MACP extension %d times, "
                               "not exactly once (RFC-MACP-0014 §3)" % (path, n))
            req = node.get("request")
            req_body = req.get("body") if isinstance(req, dict) else None
            if isinstance(req_body, dict) and req_body.get("method") == "SendMessage":
                msg = (req_body.get("params") or {}).get("message") or {}
                parts = msg.get("parts") if isinstance(msg.get("parts"), list) else []
                n = sum(1 for pt in parts if isinstance(pt, dict)
                        and str(pt.get("mediaType", "")).startswith("application/macp-envelope"))
                if n != 1:
                    bad.append("%s/request carries %d Envelope Parts, not exactly 1 "
                               "(RFC-MACP-0014 §5.1)" % (path, n))
                resp = node.get("response")
                resp_body = resp.get("body") if isinstance(resp, dict) else None
                if isinstance(resp_body, dict) and "result" in resp_body and not (
                        isinstance(resp_body["result"], dict) and "message" in resp_body["result"]):
                    bad.append("%s/response answers SendMessage with a result that is not a "
                               "Message (RFC-MACP-0014 §5.2)" % path)
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
                hits = [(i, d) for i, d in enumerate(data) if isinstance(d, dict)
                        and d.get("@type") == ERRORINFO_TYPE and d.get("domain") == MACP_DOMAIN]
                if len(hits) > 1:
                    bad.append("%s/error carries %d MACP ErrorInfo entries, not at most 1 "
                               "(RFC-MACP-0014 §11.1)" % (path, len(hits)))
                for i, h in hits:
                    found.append(("ErrorInfo", h, "%s/error/data/%d" % (path, i)))
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
