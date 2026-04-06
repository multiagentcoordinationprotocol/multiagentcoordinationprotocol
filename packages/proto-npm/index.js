'use strict';

const path = require('path');

/**
 * Absolute path to the directory containing MACP .proto files.
 * Use this to configure protobufjs, @grpc/proto-loader, or any
 * other tool that needs to locate the raw .proto schemas.
 *
 * Example:
 *   const { protoDir } = require('@macp/proto');
 *   // protoDir => "/path/to/node_modules/@macp/proto/proto"
 *   // Proto files are at: protoDir + "/macp/v1/core.proto", etc.
 */
const protoDir = path.resolve(__dirname, 'proto');

module.exports = { protoDir };
