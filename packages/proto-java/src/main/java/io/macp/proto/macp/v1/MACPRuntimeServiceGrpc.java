package io.macp.proto.macp.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@io.grpc.stub.annotations.GrpcGenerated
public final class MACPRuntimeServiceGrpc {

  private MACPRuntimeServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "macp.v1.MACPRuntimeService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.InitializeRequest,
      io.macp.proto.macp.v1.InitializeResponse> getInitializeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Initialize",
      requestType = io.macp.proto.macp.v1.InitializeRequest.class,
      responseType = io.macp.proto.macp.v1.InitializeResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.InitializeRequest,
      io.macp.proto.macp.v1.InitializeResponse> getInitializeMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.InitializeRequest, io.macp.proto.macp.v1.InitializeResponse> getInitializeMethod;
    if ((getInitializeMethod = MACPRuntimeServiceGrpc.getInitializeMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getInitializeMethod = MACPRuntimeServiceGrpc.getInitializeMethod) == null) {
          MACPRuntimeServiceGrpc.getInitializeMethod = getInitializeMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.InitializeRequest, io.macp.proto.macp.v1.InitializeResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Initialize"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.InitializeRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.InitializeResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("Initialize"))
              .build();
        }
      }
    }
    return getInitializeMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.SendRequest,
      io.macp.proto.macp.v1.SendResponse> getSendMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Send",
      requestType = io.macp.proto.macp.v1.SendRequest.class,
      responseType = io.macp.proto.macp.v1.SendResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.SendRequest,
      io.macp.proto.macp.v1.SendResponse> getSendMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.SendRequest, io.macp.proto.macp.v1.SendResponse> getSendMethod;
    if ((getSendMethod = MACPRuntimeServiceGrpc.getSendMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getSendMethod = MACPRuntimeServiceGrpc.getSendMethod) == null) {
          MACPRuntimeServiceGrpc.getSendMethod = getSendMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.SendRequest, io.macp.proto.macp.v1.SendResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Send"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.SendRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.SendResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("Send"))
              .build();
        }
      }
    }
    return getSendMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.StreamSessionRequest,
      io.macp.proto.macp.v1.StreamSessionResponse> getStreamSessionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "StreamSession",
      requestType = io.macp.proto.macp.v1.StreamSessionRequest.class,
      responseType = io.macp.proto.macp.v1.StreamSessionResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.StreamSessionRequest,
      io.macp.proto.macp.v1.StreamSessionResponse> getStreamSessionMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.StreamSessionRequest, io.macp.proto.macp.v1.StreamSessionResponse> getStreamSessionMethod;
    if ((getStreamSessionMethod = MACPRuntimeServiceGrpc.getStreamSessionMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getStreamSessionMethod = MACPRuntimeServiceGrpc.getStreamSessionMethod) == null) {
          MACPRuntimeServiceGrpc.getStreamSessionMethod = getStreamSessionMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.StreamSessionRequest, io.macp.proto.macp.v1.StreamSessionResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "StreamSession"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.StreamSessionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.StreamSessionResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("StreamSession"))
              .build();
        }
      }
    }
    return getStreamSessionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetSessionRequest,
      io.macp.proto.macp.v1.GetSessionResponse> getGetSessionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetSession",
      requestType = io.macp.proto.macp.v1.GetSessionRequest.class,
      responseType = io.macp.proto.macp.v1.GetSessionResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetSessionRequest,
      io.macp.proto.macp.v1.GetSessionResponse> getGetSessionMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetSessionRequest, io.macp.proto.macp.v1.GetSessionResponse> getGetSessionMethod;
    if ((getGetSessionMethod = MACPRuntimeServiceGrpc.getGetSessionMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getGetSessionMethod = MACPRuntimeServiceGrpc.getGetSessionMethod) == null) {
          MACPRuntimeServiceGrpc.getGetSessionMethod = getGetSessionMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.GetSessionRequest, io.macp.proto.macp.v1.GetSessionResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetSession"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.GetSessionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.GetSessionResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("GetSession"))
              .build();
        }
      }
    }
    return getGetSessionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.CancelSessionRequest,
      io.macp.proto.macp.v1.CancelSessionResponse> getCancelSessionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CancelSession",
      requestType = io.macp.proto.macp.v1.CancelSessionRequest.class,
      responseType = io.macp.proto.macp.v1.CancelSessionResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.CancelSessionRequest,
      io.macp.proto.macp.v1.CancelSessionResponse> getCancelSessionMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.CancelSessionRequest, io.macp.proto.macp.v1.CancelSessionResponse> getCancelSessionMethod;
    if ((getCancelSessionMethod = MACPRuntimeServiceGrpc.getCancelSessionMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getCancelSessionMethod = MACPRuntimeServiceGrpc.getCancelSessionMethod) == null) {
          MACPRuntimeServiceGrpc.getCancelSessionMethod = getCancelSessionMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.CancelSessionRequest, io.macp.proto.macp.v1.CancelSessionResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CancelSession"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.CancelSessionRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.CancelSessionResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("CancelSession"))
              .build();
        }
      }
    }
    return getCancelSessionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetManifestRequest,
      io.macp.proto.macp.v1.GetManifestResponse> getGetManifestMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetManifest",
      requestType = io.macp.proto.macp.v1.GetManifestRequest.class,
      responseType = io.macp.proto.macp.v1.GetManifestResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetManifestRequest,
      io.macp.proto.macp.v1.GetManifestResponse> getGetManifestMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetManifestRequest, io.macp.proto.macp.v1.GetManifestResponse> getGetManifestMethod;
    if ((getGetManifestMethod = MACPRuntimeServiceGrpc.getGetManifestMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getGetManifestMethod = MACPRuntimeServiceGrpc.getGetManifestMethod) == null) {
          MACPRuntimeServiceGrpc.getGetManifestMethod = getGetManifestMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.GetManifestRequest, io.macp.proto.macp.v1.GetManifestResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetManifest"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.GetManifestRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.GetManifestResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("GetManifest"))
              .build();
        }
      }
    }
    return getGetManifestMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListModesRequest,
      io.macp.proto.macp.v1.ListModesResponse> getListModesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ListModes",
      requestType = io.macp.proto.macp.v1.ListModesRequest.class,
      responseType = io.macp.proto.macp.v1.ListModesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListModesRequest,
      io.macp.proto.macp.v1.ListModesResponse> getListModesMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListModesRequest, io.macp.proto.macp.v1.ListModesResponse> getListModesMethod;
    if ((getListModesMethod = MACPRuntimeServiceGrpc.getListModesMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getListModesMethod = MACPRuntimeServiceGrpc.getListModesMethod) == null) {
          MACPRuntimeServiceGrpc.getListModesMethod = getListModesMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.ListModesRequest, io.macp.proto.macp.v1.ListModesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ListModes"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListModesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListModesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("ListModes"))
              .build();
        }
      }
    }
    return getListModesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchModeRegistryRequest,
      io.macp.proto.macp.v1.WatchModeRegistryResponse> getWatchModeRegistryMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "WatchModeRegistry",
      requestType = io.macp.proto.macp.v1.WatchModeRegistryRequest.class,
      responseType = io.macp.proto.macp.v1.WatchModeRegistryResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchModeRegistryRequest,
      io.macp.proto.macp.v1.WatchModeRegistryResponse> getWatchModeRegistryMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchModeRegistryRequest, io.macp.proto.macp.v1.WatchModeRegistryResponse> getWatchModeRegistryMethod;
    if ((getWatchModeRegistryMethod = MACPRuntimeServiceGrpc.getWatchModeRegistryMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getWatchModeRegistryMethod = MACPRuntimeServiceGrpc.getWatchModeRegistryMethod) == null) {
          MACPRuntimeServiceGrpc.getWatchModeRegistryMethod = getWatchModeRegistryMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.WatchModeRegistryRequest, io.macp.proto.macp.v1.WatchModeRegistryResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "WatchModeRegistry"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchModeRegistryRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchModeRegistryResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("WatchModeRegistry"))
              .build();
        }
      }
    }
    return getWatchModeRegistryMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListRootsRequest,
      io.macp.proto.macp.v1.ListRootsResponse> getListRootsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ListRoots",
      requestType = io.macp.proto.macp.v1.ListRootsRequest.class,
      responseType = io.macp.proto.macp.v1.ListRootsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListRootsRequest,
      io.macp.proto.macp.v1.ListRootsResponse> getListRootsMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListRootsRequest, io.macp.proto.macp.v1.ListRootsResponse> getListRootsMethod;
    if ((getListRootsMethod = MACPRuntimeServiceGrpc.getListRootsMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getListRootsMethod = MACPRuntimeServiceGrpc.getListRootsMethod) == null) {
          MACPRuntimeServiceGrpc.getListRootsMethod = getListRootsMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.ListRootsRequest, io.macp.proto.macp.v1.ListRootsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ListRoots"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListRootsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListRootsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("ListRoots"))
              .build();
        }
      }
    }
    return getListRootsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchRootsRequest,
      io.macp.proto.macp.v1.WatchRootsResponse> getWatchRootsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "WatchRoots",
      requestType = io.macp.proto.macp.v1.WatchRootsRequest.class,
      responseType = io.macp.proto.macp.v1.WatchRootsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchRootsRequest,
      io.macp.proto.macp.v1.WatchRootsResponse> getWatchRootsMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchRootsRequest, io.macp.proto.macp.v1.WatchRootsResponse> getWatchRootsMethod;
    if ((getWatchRootsMethod = MACPRuntimeServiceGrpc.getWatchRootsMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getWatchRootsMethod = MACPRuntimeServiceGrpc.getWatchRootsMethod) == null) {
          MACPRuntimeServiceGrpc.getWatchRootsMethod = getWatchRootsMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.WatchRootsRequest, io.macp.proto.macp.v1.WatchRootsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "WatchRoots"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchRootsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchRootsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("WatchRoots"))
              .build();
        }
      }
    }
    return getWatchRootsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListExtModesRequest,
      io.macp.proto.macp.v1.ListExtModesResponse> getListExtModesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ListExtModes",
      requestType = io.macp.proto.macp.v1.ListExtModesRequest.class,
      responseType = io.macp.proto.macp.v1.ListExtModesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListExtModesRequest,
      io.macp.proto.macp.v1.ListExtModesResponse> getListExtModesMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListExtModesRequest, io.macp.proto.macp.v1.ListExtModesResponse> getListExtModesMethod;
    if ((getListExtModesMethod = MACPRuntimeServiceGrpc.getListExtModesMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getListExtModesMethod = MACPRuntimeServiceGrpc.getListExtModesMethod) == null) {
          MACPRuntimeServiceGrpc.getListExtModesMethod = getListExtModesMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.ListExtModesRequest, io.macp.proto.macp.v1.ListExtModesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ListExtModes"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListExtModesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListExtModesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("ListExtModes"))
              .build();
        }
      }
    }
    return getListExtModesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.RegisterExtModeRequest,
      io.macp.proto.macp.v1.RegisterExtModeResponse> getRegisterExtModeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "RegisterExtMode",
      requestType = io.macp.proto.macp.v1.RegisterExtModeRequest.class,
      responseType = io.macp.proto.macp.v1.RegisterExtModeResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.RegisterExtModeRequest,
      io.macp.proto.macp.v1.RegisterExtModeResponse> getRegisterExtModeMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.RegisterExtModeRequest, io.macp.proto.macp.v1.RegisterExtModeResponse> getRegisterExtModeMethod;
    if ((getRegisterExtModeMethod = MACPRuntimeServiceGrpc.getRegisterExtModeMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getRegisterExtModeMethod = MACPRuntimeServiceGrpc.getRegisterExtModeMethod) == null) {
          MACPRuntimeServiceGrpc.getRegisterExtModeMethod = getRegisterExtModeMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.RegisterExtModeRequest, io.macp.proto.macp.v1.RegisterExtModeResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "RegisterExtMode"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.RegisterExtModeRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.RegisterExtModeResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("RegisterExtMode"))
              .build();
        }
      }
    }
    return getRegisterExtModeMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.UnregisterExtModeRequest,
      io.macp.proto.macp.v1.UnregisterExtModeResponse> getUnregisterExtModeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UnregisterExtMode",
      requestType = io.macp.proto.macp.v1.UnregisterExtModeRequest.class,
      responseType = io.macp.proto.macp.v1.UnregisterExtModeResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.UnregisterExtModeRequest,
      io.macp.proto.macp.v1.UnregisterExtModeResponse> getUnregisterExtModeMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.UnregisterExtModeRequest, io.macp.proto.macp.v1.UnregisterExtModeResponse> getUnregisterExtModeMethod;
    if ((getUnregisterExtModeMethod = MACPRuntimeServiceGrpc.getUnregisterExtModeMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getUnregisterExtModeMethod = MACPRuntimeServiceGrpc.getUnregisterExtModeMethod) == null) {
          MACPRuntimeServiceGrpc.getUnregisterExtModeMethod = getUnregisterExtModeMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.UnregisterExtModeRequest, io.macp.proto.macp.v1.UnregisterExtModeResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UnregisterExtMode"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.UnregisterExtModeRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.UnregisterExtModeResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("UnregisterExtMode"))
              .build();
        }
      }
    }
    return getUnregisterExtModeMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.PromoteModeRequest,
      io.macp.proto.macp.v1.PromoteModeResponse> getPromoteModeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "PromoteMode",
      requestType = io.macp.proto.macp.v1.PromoteModeRequest.class,
      responseType = io.macp.proto.macp.v1.PromoteModeResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.PromoteModeRequest,
      io.macp.proto.macp.v1.PromoteModeResponse> getPromoteModeMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.PromoteModeRequest, io.macp.proto.macp.v1.PromoteModeResponse> getPromoteModeMethod;
    if ((getPromoteModeMethod = MACPRuntimeServiceGrpc.getPromoteModeMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getPromoteModeMethod = MACPRuntimeServiceGrpc.getPromoteModeMethod) == null) {
          MACPRuntimeServiceGrpc.getPromoteModeMethod = getPromoteModeMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.PromoteModeRequest, io.macp.proto.macp.v1.PromoteModeResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "PromoteMode"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.PromoteModeRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.PromoteModeResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("PromoteMode"))
              .build();
        }
      }
    }
    return getPromoteModeMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchSignalsRequest,
      io.macp.proto.macp.v1.WatchSignalsResponse> getWatchSignalsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "WatchSignals",
      requestType = io.macp.proto.macp.v1.WatchSignalsRequest.class,
      responseType = io.macp.proto.macp.v1.WatchSignalsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchSignalsRequest,
      io.macp.proto.macp.v1.WatchSignalsResponse> getWatchSignalsMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchSignalsRequest, io.macp.proto.macp.v1.WatchSignalsResponse> getWatchSignalsMethod;
    if ((getWatchSignalsMethod = MACPRuntimeServiceGrpc.getWatchSignalsMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getWatchSignalsMethod = MACPRuntimeServiceGrpc.getWatchSignalsMethod) == null) {
          MACPRuntimeServiceGrpc.getWatchSignalsMethod = getWatchSignalsMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.WatchSignalsRequest, io.macp.proto.macp.v1.WatchSignalsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "WatchSignals"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchSignalsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchSignalsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("WatchSignals"))
              .build();
        }
      }
    }
    return getWatchSignalsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.RegisterPolicyRequest,
      io.macp.proto.macp.v1.RegisterPolicyResponse> getRegisterPolicyMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "RegisterPolicy",
      requestType = io.macp.proto.macp.v1.RegisterPolicyRequest.class,
      responseType = io.macp.proto.macp.v1.RegisterPolicyResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.RegisterPolicyRequest,
      io.macp.proto.macp.v1.RegisterPolicyResponse> getRegisterPolicyMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.RegisterPolicyRequest, io.macp.proto.macp.v1.RegisterPolicyResponse> getRegisterPolicyMethod;
    if ((getRegisterPolicyMethod = MACPRuntimeServiceGrpc.getRegisterPolicyMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getRegisterPolicyMethod = MACPRuntimeServiceGrpc.getRegisterPolicyMethod) == null) {
          MACPRuntimeServiceGrpc.getRegisterPolicyMethod = getRegisterPolicyMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.RegisterPolicyRequest, io.macp.proto.macp.v1.RegisterPolicyResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "RegisterPolicy"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.RegisterPolicyRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.RegisterPolicyResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("RegisterPolicy"))
              .build();
        }
      }
    }
    return getRegisterPolicyMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.UnregisterPolicyRequest,
      io.macp.proto.macp.v1.UnregisterPolicyResponse> getUnregisterPolicyMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UnregisterPolicy",
      requestType = io.macp.proto.macp.v1.UnregisterPolicyRequest.class,
      responseType = io.macp.proto.macp.v1.UnregisterPolicyResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.UnregisterPolicyRequest,
      io.macp.proto.macp.v1.UnregisterPolicyResponse> getUnregisterPolicyMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.UnregisterPolicyRequest, io.macp.proto.macp.v1.UnregisterPolicyResponse> getUnregisterPolicyMethod;
    if ((getUnregisterPolicyMethod = MACPRuntimeServiceGrpc.getUnregisterPolicyMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getUnregisterPolicyMethod = MACPRuntimeServiceGrpc.getUnregisterPolicyMethod) == null) {
          MACPRuntimeServiceGrpc.getUnregisterPolicyMethod = getUnregisterPolicyMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.UnregisterPolicyRequest, io.macp.proto.macp.v1.UnregisterPolicyResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UnregisterPolicy"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.UnregisterPolicyRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.UnregisterPolicyResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("UnregisterPolicy"))
              .build();
        }
      }
    }
    return getUnregisterPolicyMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetPolicyRequest,
      io.macp.proto.macp.v1.GetPolicyResponse> getGetPolicyMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetPolicy",
      requestType = io.macp.proto.macp.v1.GetPolicyRequest.class,
      responseType = io.macp.proto.macp.v1.GetPolicyResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetPolicyRequest,
      io.macp.proto.macp.v1.GetPolicyResponse> getGetPolicyMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.GetPolicyRequest, io.macp.proto.macp.v1.GetPolicyResponse> getGetPolicyMethod;
    if ((getGetPolicyMethod = MACPRuntimeServiceGrpc.getGetPolicyMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getGetPolicyMethod = MACPRuntimeServiceGrpc.getGetPolicyMethod) == null) {
          MACPRuntimeServiceGrpc.getGetPolicyMethod = getGetPolicyMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.GetPolicyRequest, io.macp.proto.macp.v1.GetPolicyResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetPolicy"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.GetPolicyRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.GetPolicyResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("GetPolicy"))
              .build();
        }
      }
    }
    return getGetPolicyMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListPoliciesRequest,
      io.macp.proto.macp.v1.ListPoliciesResponse> getListPoliciesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ListPolicies",
      requestType = io.macp.proto.macp.v1.ListPoliciesRequest.class,
      responseType = io.macp.proto.macp.v1.ListPoliciesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListPoliciesRequest,
      io.macp.proto.macp.v1.ListPoliciesResponse> getListPoliciesMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.ListPoliciesRequest, io.macp.proto.macp.v1.ListPoliciesResponse> getListPoliciesMethod;
    if ((getListPoliciesMethod = MACPRuntimeServiceGrpc.getListPoliciesMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getListPoliciesMethod = MACPRuntimeServiceGrpc.getListPoliciesMethod) == null) {
          MACPRuntimeServiceGrpc.getListPoliciesMethod = getListPoliciesMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.ListPoliciesRequest, io.macp.proto.macp.v1.ListPoliciesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ListPolicies"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListPoliciesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.ListPoliciesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("ListPolicies"))
              .build();
        }
      }
    }
    return getListPoliciesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchPoliciesRequest,
      io.macp.proto.macp.v1.WatchPoliciesResponse> getWatchPoliciesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "WatchPolicies",
      requestType = io.macp.proto.macp.v1.WatchPoliciesRequest.class,
      responseType = io.macp.proto.macp.v1.WatchPoliciesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
  public static io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchPoliciesRequest,
      io.macp.proto.macp.v1.WatchPoliciesResponse> getWatchPoliciesMethod() {
    io.grpc.MethodDescriptor<io.macp.proto.macp.v1.WatchPoliciesRequest, io.macp.proto.macp.v1.WatchPoliciesResponse> getWatchPoliciesMethod;
    if ((getWatchPoliciesMethod = MACPRuntimeServiceGrpc.getWatchPoliciesMethod) == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        if ((getWatchPoliciesMethod = MACPRuntimeServiceGrpc.getWatchPoliciesMethod) == null) {
          MACPRuntimeServiceGrpc.getWatchPoliciesMethod = getWatchPoliciesMethod =
              io.grpc.MethodDescriptor.<io.macp.proto.macp.v1.WatchPoliciesRequest, io.macp.proto.macp.v1.WatchPoliciesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "WatchPolicies"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchPoliciesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  io.macp.proto.macp.v1.WatchPoliciesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new MACPRuntimeServiceMethodDescriptorSupplier("WatchPolicies"))
              .build();
        }
      }
    }
    return getWatchPoliciesMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static MACPRuntimeServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceStub>() {
        @java.lang.Override
        public MACPRuntimeServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new MACPRuntimeServiceStub(channel, callOptions);
        }
      };
    return MACPRuntimeServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports all types of calls on the service
   */
  public static MACPRuntimeServiceBlockingV2Stub newBlockingV2Stub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceBlockingV2Stub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceBlockingV2Stub>() {
        @java.lang.Override
        public MACPRuntimeServiceBlockingV2Stub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new MACPRuntimeServiceBlockingV2Stub(channel, callOptions);
        }
      };
    return MACPRuntimeServiceBlockingV2Stub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static MACPRuntimeServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceBlockingStub>() {
        @java.lang.Override
        public MACPRuntimeServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new MACPRuntimeServiceBlockingStub(channel, callOptions);
        }
      };
    return MACPRuntimeServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static MACPRuntimeServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<MACPRuntimeServiceFutureStub>() {
        @java.lang.Override
        public MACPRuntimeServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new MACPRuntimeServiceFutureStub(channel, callOptions);
        }
      };
    return MACPRuntimeServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void initialize(io.macp.proto.macp.v1.InitializeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.InitializeResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getInitializeMethod(), responseObserver);
    }

    /**
     */
    default void send(io.macp.proto.macp.v1.SendRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.SendResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getSendMethod(), responseObserver);
    }

    /**
     */
    default io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.StreamSessionRequest> streamSession(
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.StreamSessionResponse> responseObserver) {
      return io.grpc.stub.ServerCalls.asyncUnimplementedStreamingCall(getStreamSessionMethod(), responseObserver);
    }

    /**
     */
    default void getSession(io.macp.proto.macp.v1.GetSessionRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetSessionResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetSessionMethod(), responseObserver);
    }

    /**
     */
    default void cancelSession(io.macp.proto.macp.v1.CancelSessionRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.CancelSessionResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCancelSessionMethod(), responseObserver);
    }

    /**
     */
    default void getManifest(io.macp.proto.macp.v1.GetManifestRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetManifestResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetManifestMethod(), responseObserver);
    }

    /**
     */
    default void listModes(io.macp.proto.macp.v1.ListModesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListModesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getListModesMethod(), responseObserver);
    }

    /**
     */
    default void watchModeRegistry(io.macp.proto.macp.v1.WatchModeRegistryRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchModeRegistryResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getWatchModeRegistryMethod(), responseObserver);
    }

    /**
     */
    default void listRoots(io.macp.proto.macp.v1.ListRootsRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListRootsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getListRootsMethod(), responseObserver);
    }

    /**
     */
    default void watchRoots(io.macp.proto.macp.v1.WatchRootsRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchRootsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getWatchRootsMethod(), responseObserver);
    }

    /**
     * <pre>
     * Extension mode lifecycle
     * </pre>
     */
    default void listExtModes(io.macp.proto.macp.v1.ListExtModesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListExtModesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getListExtModesMethod(), responseObserver);
    }

    /**
     */
    default void registerExtMode(io.macp.proto.macp.v1.RegisterExtModeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.RegisterExtModeResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getRegisterExtModeMethod(), responseObserver);
    }

    /**
     */
    default void unregisterExtMode(io.macp.proto.macp.v1.UnregisterExtModeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.UnregisterExtModeResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUnregisterExtModeMethod(), responseObserver);
    }

    /**
     */
    default void promoteMode(io.macp.proto.macp.v1.PromoteModeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.PromoteModeResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getPromoteModeMethod(), responseObserver);
    }

    /**
     * <pre>
     * Ambient Signal observation
     * </pre>
     */
    default void watchSignals(io.macp.proto.macp.v1.WatchSignalsRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchSignalsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getWatchSignalsMethod(), responseObserver);
    }

    /**
     * <pre>
     * Governance policy lifecycle (RFC-MACP-0012)
     * </pre>
     */
    default void registerPolicy(io.macp.proto.macp.v1.RegisterPolicyRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.RegisterPolicyResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getRegisterPolicyMethod(), responseObserver);
    }

    /**
     */
    default void unregisterPolicy(io.macp.proto.macp.v1.UnregisterPolicyRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.UnregisterPolicyResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUnregisterPolicyMethod(), responseObserver);
    }

    /**
     */
    default void getPolicy(io.macp.proto.macp.v1.GetPolicyRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetPolicyResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetPolicyMethod(), responseObserver);
    }

    /**
     */
    default void listPolicies(io.macp.proto.macp.v1.ListPoliciesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListPoliciesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getListPoliciesMethod(), responseObserver);
    }

    /**
     */
    default void watchPolicies(io.macp.proto.macp.v1.WatchPoliciesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchPoliciesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getWatchPoliciesMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service MACPRuntimeService.
   */
  public static abstract class MACPRuntimeServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return MACPRuntimeServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service MACPRuntimeService.
   */
  public static final class MACPRuntimeServiceStub
      extends io.grpc.stub.AbstractAsyncStub<MACPRuntimeServiceStub> {
    private MACPRuntimeServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected MACPRuntimeServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new MACPRuntimeServiceStub(channel, callOptions);
    }

    /**
     */
    public void initialize(io.macp.proto.macp.v1.InitializeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.InitializeResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getInitializeMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void send(io.macp.proto.macp.v1.SendRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.SendResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getSendMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.StreamSessionRequest> streamSession(
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.StreamSessionResponse> responseObserver) {
      return io.grpc.stub.ClientCalls.asyncBidiStreamingCall(
          getChannel().newCall(getStreamSessionMethod(), getCallOptions()), responseObserver);
    }

    /**
     */
    public void getSession(io.macp.proto.macp.v1.GetSessionRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetSessionResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetSessionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void cancelSession(io.macp.proto.macp.v1.CancelSessionRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.CancelSessionResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCancelSessionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getManifest(io.macp.proto.macp.v1.GetManifestRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetManifestResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetManifestMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void listModes(io.macp.proto.macp.v1.ListModesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListModesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getListModesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void watchModeRegistry(io.macp.proto.macp.v1.WatchModeRegistryRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchModeRegistryResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncServerStreamingCall(
          getChannel().newCall(getWatchModeRegistryMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void listRoots(io.macp.proto.macp.v1.ListRootsRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListRootsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getListRootsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void watchRoots(io.macp.proto.macp.v1.WatchRootsRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchRootsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncServerStreamingCall(
          getChannel().newCall(getWatchRootsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Extension mode lifecycle
     * </pre>
     */
    public void listExtModes(io.macp.proto.macp.v1.ListExtModesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListExtModesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getListExtModesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void registerExtMode(io.macp.proto.macp.v1.RegisterExtModeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.RegisterExtModeResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getRegisterExtModeMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void unregisterExtMode(io.macp.proto.macp.v1.UnregisterExtModeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.UnregisterExtModeResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUnregisterExtModeMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void promoteMode(io.macp.proto.macp.v1.PromoteModeRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.PromoteModeResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getPromoteModeMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Ambient Signal observation
     * </pre>
     */
    public void watchSignals(io.macp.proto.macp.v1.WatchSignalsRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchSignalsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncServerStreamingCall(
          getChannel().newCall(getWatchSignalsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Governance policy lifecycle (RFC-MACP-0012)
     * </pre>
     */
    public void registerPolicy(io.macp.proto.macp.v1.RegisterPolicyRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.RegisterPolicyResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getRegisterPolicyMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void unregisterPolicy(io.macp.proto.macp.v1.UnregisterPolicyRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.UnregisterPolicyResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUnregisterPolicyMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void getPolicy(io.macp.proto.macp.v1.GetPolicyRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetPolicyResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetPolicyMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void listPolicies(io.macp.proto.macp.v1.ListPoliciesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListPoliciesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getListPoliciesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void watchPolicies(io.macp.proto.macp.v1.WatchPoliciesRequest request,
        io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchPoliciesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncServerStreamingCall(
          getChannel().newCall(getWatchPoliciesMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service MACPRuntimeService.
   */
  public static final class MACPRuntimeServiceBlockingV2Stub
      extends io.grpc.stub.AbstractBlockingStub<MACPRuntimeServiceBlockingV2Stub> {
    private MACPRuntimeServiceBlockingV2Stub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected MACPRuntimeServiceBlockingV2Stub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new MACPRuntimeServiceBlockingV2Stub(channel, callOptions);
    }

    /**
     */
    public io.macp.proto.macp.v1.InitializeResponse initialize(io.macp.proto.macp.v1.InitializeRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getInitializeMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.SendResponse send(io.macp.proto.macp.v1.SendRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getSendMethod(), getCallOptions(), request);
    }

    /**
     */
    @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/10918")
    public io.grpc.stub.BlockingClientCall<io.macp.proto.macp.v1.StreamSessionRequest, io.macp.proto.macp.v1.StreamSessionResponse>
        streamSession() {
      return io.grpc.stub.ClientCalls.blockingBidiStreamingCall(
          getChannel(), getStreamSessionMethod(), getCallOptions());
    }

    /**
     */
    public io.macp.proto.macp.v1.GetSessionResponse getSession(io.macp.proto.macp.v1.GetSessionRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getGetSessionMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.CancelSessionResponse cancelSession(io.macp.proto.macp.v1.CancelSessionRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getCancelSessionMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.GetManifestResponse getManifest(io.macp.proto.macp.v1.GetManifestRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getGetManifestMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.ListModesResponse listModes(io.macp.proto.macp.v1.ListModesRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getListModesMethod(), getCallOptions(), request);
    }

    /**
     */
    @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/10918")
    public io.grpc.stub.BlockingClientCall<?, io.macp.proto.macp.v1.WatchModeRegistryResponse>
        watchModeRegistry(io.macp.proto.macp.v1.WatchModeRegistryRequest request) {
      return io.grpc.stub.ClientCalls.blockingV2ServerStreamingCall(
          getChannel(), getWatchModeRegistryMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.ListRootsResponse listRoots(io.macp.proto.macp.v1.ListRootsRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getListRootsMethod(), getCallOptions(), request);
    }

    /**
     */
    @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/10918")
    public io.grpc.stub.BlockingClientCall<?, io.macp.proto.macp.v1.WatchRootsResponse>
        watchRoots(io.macp.proto.macp.v1.WatchRootsRequest request) {
      return io.grpc.stub.ClientCalls.blockingV2ServerStreamingCall(
          getChannel(), getWatchRootsMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Extension mode lifecycle
     * </pre>
     */
    public io.macp.proto.macp.v1.ListExtModesResponse listExtModes(io.macp.proto.macp.v1.ListExtModesRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getListExtModesMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.RegisterExtModeResponse registerExtMode(io.macp.proto.macp.v1.RegisterExtModeRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getRegisterExtModeMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.UnregisterExtModeResponse unregisterExtMode(io.macp.proto.macp.v1.UnregisterExtModeRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getUnregisterExtModeMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.PromoteModeResponse promoteMode(io.macp.proto.macp.v1.PromoteModeRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getPromoteModeMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Ambient Signal observation
     * </pre>
     */
    @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/10918")
    public io.grpc.stub.BlockingClientCall<?, io.macp.proto.macp.v1.WatchSignalsResponse>
        watchSignals(io.macp.proto.macp.v1.WatchSignalsRequest request) {
      return io.grpc.stub.ClientCalls.blockingV2ServerStreamingCall(
          getChannel(), getWatchSignalsMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Governance policy lifecycle (RFC-MACP-0012)
     * </pre>
     */
    public io.macp.proto.macp.v1.RegisterPolicyResponse registerPolicy(io.macp.proto.macp.v1.RegisterPolicyRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getRegisterPolicyMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.UnregisterPolicyResponse unregisterPolicy(io.macp.proto.macp.v1.UnregisterPolicyRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getUnregisterPolicyMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.GetPolicyResponse getPolicy(io.macp.proto.macp.v1.GetPolicyRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getGetPolicyMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.ListPoliciesResponse listPolicies(io.macp.proto.macp.v1.ListPoliciesRequest request) throws io.grpc.StatusException {
      return io.grpc.stub.ClientCalls.blockingV2UnaryCall(
          getChannel(), getListPoliciesMethod(), getCallOptions(), request);
    }

    /**
     */
    @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/10918")
    public io.grpc.stub.BlockingClientCall<?, io.macp.proto.macp.v1.WatchPoliciesResponse>
        watchPolicies(io.macp.proto.macp.v1.WatchPoliciesRequest request) {
      return io.grpc.stub.ClientCalls.blockingV2ServerStreamingCall(
          getChannel(), getWatchPoliciesMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do limited synchronous rpc calls to service MACPRuntimeService.
   */
  public static final class MACPRuntimeServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<MACPRuntimeServiceBlockingStub> {
    private MACPRuntimeServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected MACPRuntimeServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new MACPRuntimeServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public io.macp.proto.macp.v1.InitializeResponse initialize(io.macp.proto.macp.v1.InitializeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getInitializeMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.SendResponse send(io.macp.proto.macp.v1.SendRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getSendMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.GetSessionResponse getSession(io.macp.proto.macp.v1.GetSessionRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetSessionMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.CancelSessionResponse cancelSession(io.macp.proto.macp.v1.CancelSessionRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCancelSessionMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.GetManifestResponse getManifest(io.macp.proto.macp.v1.GetManifestRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetManifestMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.ListModesResponse listModes(io.macp.proto.macp.v1.ListModesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getListModesMethod(), getCallOptions(), request);
    }

    /**
     */
    public java.util.Iterator<io.macp.proto.macp.v1.WatchModeRegistryResponse> watchModeRegistry(
        io.macp.proto.macp.v1.WatchModeRegistryRequest request) {
      return io.grpc.stub.ClientCalls.blockingServerStreamingCall(
          getChannel(), getWatchModeRegistryMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.ListRootsResponse listRoots(io.macp.proto.macp.v1.ListRootsRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getListRootsMethod(), getCallOptions(), request);
    }

    /**
     */
    public java.util.Iterator<io.macp.proto.macp.v1.WatchRootsResponse> watchRoots(
        io.macp.proto.macp.v1.WatchRootsRequest request) {
      return io.grpc.stub.ClientCalls.blockingServerStreamingCall(
          getChannel(), getWatchRootsMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Extension mode lifecycle
     * </pre>
     */
    public io.macp.proto.macp.v1.ListExtModesResponse listExtModes(io.macp.proto.macp.v1.ListExtModesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getListExtModesMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.RegisterExtModeResponse registerExtMode(io.macp.proto.macp.v1.RegisterExtModeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getRegisterExtModeMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.UnregisterExtModeResponse unregisterExtMode(io.macp.proto.macp.v1.UnregisterExtModeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUnregisterExtModeMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.PromoteModeResponse promoteMode(io.macp.proto.macp.v1.PromoteModeRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getPromoteModeMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Ambient Signal observation
     * </pre>
     */
    public java.util.Iterator<io.macp.proto.macp.v1.WatchSignalsResponse> watchSignals(
        io.macp.proto.macp.v1.WatchSignalsRequest request) {
      return io.grpc.stub.ClientCalls.blockingServerStreamingCall(
          getChannel(), getWatchSignalsMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Governance policy lifecycle (RFC-MACP-0012)
     * </pre>
     */
    public io.macp.proto.macp.v1.RegisterPolicyResponse registerPolicy(io.macp.proto.macp.v1.RegisterPolicyRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getRegisterPolicyMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.UnregisterPolicyResponse unregisterPolicy(io.macp.proto.macp.v1.UnregisterPolicyRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUnregisterPolicyMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.GetPolicyResponse getPolicy(io.macp.proto.macp.v1.GetPolicyRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetPolicyMethod(), getCallOptions(), request);
    }

    /**
     */
    public io.macp.proto.macp.v1.ListPoliciesResponse listPolicies(io.macp.proto.macp.v1.ListPoliciesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getListPoliciesMethod(), getCallOptions(), request);
    }

    /**
     */
    public java.util.Iterator<io.macp.proto.macp.v1.WatchPoliciesResponse> watchPolicies(
        io.macp.proto.macp.v1.WatchPoliciesRequest request) {
      return io.grpc.stub.ClientCalls.blockingServerStreamingCall(
          getChannel(), getWatchPoliciesMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service MACPRuntimeService.
   */
  public static final class MACPRuntimeServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<MACPRuntimeServiceFutureStub> {
    private MACPRuntimeServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected MACPRuntimeServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new MACPRuntimeServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.InitializeResponse> initialize(
        io.macp.proto.macp.v1.InitializeRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getInitializeMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.SendResponse> send(
        io.macp.proto.macp.v1.SendRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getSendMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.GetSessionResponse> getSession(
        io.macp.proto.macp.v1.GetSessionRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetSessionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.CancelSessionResponse> cancelSession(
        io.macp.proto.macp.v1.CancelSessionRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCancelSessionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.GetManifestResponse> getManifest(
        io.macp.proto.macp.v1.GetManifestRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetManifestMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.ListModesResponse> listModes(
        io.macp.proto.macp.v1.ListModesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getListModesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.ListRootsResponse> listRoots(
        io.macp.proto.macp.v1.ListRootsRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getListRootsMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Extension mode lifecycle
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.ListExtModesResponse> listExtModes(
        io.macp.proto.macp.v1.ListExtModesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getListExtModesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.RegisterExtModeResponse> registerExtMode(
        io.macp.proto.macp.v1.RegisterExtModeRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getRegisterExtModeMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.UnregisterExtModeResponse> unregisterExtMode(
        io.macp.proto.macp.v1.UnregisterExtModeRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUnregisterExtModeMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.PromoteModeResponse> promoteMode(
        io.macp.proto.macp.v1.PromoteModeRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getPromoteModeMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Governance policy lifecycle (RFC-MACP-0012)
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.RegisterPolicyResponse> registerPolicy(
        io.macp.proto.macp.v1.RegisterPolicyRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getRegisterPolicyMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.UnregisterPolicyResponse> unregisterPolicy(
        io.macp.proto.macp.v1.UnregisterPolicyRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUnregisterPolicyMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.GetPolicyResponse> getPolicy(
        io.macp.proto.macp.v1.GetPolicyRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetPolicyMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<io.macp.proto.macp.v1.ListPoliciesResponse> listPolicies(
        io.macp.proto.macp.v1.ListPoliciesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getListPoliciesMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_INITIALIZE = 0;
  private static final int METHODID_SEND = 1;
  private static final int METHODID_GET_SESSION = 2;
  private static final int METHODID_CANCEL_SESSION = 3;
  private static final int METHODID_GET_MANIFEST = 4;
  private static final int METHODID_LIST_MODES = 5;
  private static final int METHODID_WATCH_MODE_REGISTRY = 6;
  private static final int METHODID_LIST_ROOTS = 7;
  private static final int METHODID_WATCH_ROOTS = 8;
  private static final int METHODID_LIST_EXT_MODES = 9;
  private static final int METHODID_REGISTER_EXT_MODE = 10;
  private static final int METHODID_UNREGISTER_EXT_MODE = 11;
  private static final int METHODID_PROMOTE_MODE = 12;
  private static final int METHODID_WATCH_SIGNALS = 13;
  private static final int METHODID_REGISTER_POLICY = 14;
  private static final int METHODID_UNREGISTER_POLICY = 15;
  private static final int METHODID_GET_POLICY = 16;
  private static final int METHODID_LIST_POLICIES = 17;
  private static final int METHODID_WATCH_POLICIES = 18;
  private static final int METHODID_STREAM_SESSION = 19;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_INITIALIZE:
          serviceImpl.initialize((io.macp.proto.macp.v1.InitializeRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.InitializeResponse>) responseObserver);
          break;
        case METHODID_SEND:
          serviceImpl.send((io.macp.proto.macp.v1.SendRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.SendResponse>) responseObserver);
          break;
        case METHODID_GET_SESSION:
          serviceImpl.getSession((io.macp.proto.macp.v1.GetSessionRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetSessionResponse>) responseObserver);
          break;
        case METHODID_CANCEL_SESSION:
          serviceImpl.cancelSession((io.macp.proto.macp.v1.CancelSessionRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.CancelSessionResponse>) responseObserver);
          break;
        case METHODID_GET_MANIFEST:
          serviceImpl.getManifest((io.macp.proto.macp.v1.GetManifestRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetManifestResponse>) responseObserver);
          break;
        case METHODID_LIST_MODES:
          serviceImpl.listModes((io.macp.proto.macp.v1.ListModesRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListModesResponse>) responseObserver);
          break;
        case METHODID_WATCH_MODE_REGISTRY:
          serviceImpl.watchModeRegistry((io.macp.proto.macp.v1.WatchModeRegistryRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchModeRegistryResponse>) responseObserver);
          break;
        case METHODID_LIST_ROOTS:
          serviceImpl.listRoots((io.macp.proto.macp.v1.ListRootsRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListRootsResponse>) responseObserver);
          break;
        case METHODID_WATCH_ROOTS:
          serviceImpl.watchRoots((io.macp.proto.macp.v1.WatchRootsRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchRootsResponse>) responseObserver);
          break;
        case METHODID_LIST_EXT_MODES:
          serviceImpl.listExtModes((io.macp.proto.macp.v1.ListExtModesRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListExtModesResponse>) responseObserver);
          break;
        case METHODID_REGISTER_EXT_MODE:
          serviceImpl.registerExtMode((io.macp.proto.macp.v1.RegisterExtModeRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.RegisterExtModeResponse>) responseObserver);
          break;
        case METHODID_UNREGISTER_EXT_MODE:
          serviceImpl.unregisterExtMode((io.macp.proto.macp.v1.UnregisterExtModeRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.UnregisterExtModeResponse>) responseObserver);
          break;
        case METHODID_PROMOTE_MODE:
          serviceImpl.promoteMode((io.macp.proto.macp.v1.PromoteModeRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.PromoteModeResponse>) responseObserver);
          break;
        case METHODID_WATCH_SIGNALS:
          serviceImpl.watchSignals((io.macp.proto.macp.v1.WatchSignalsRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchSignalsResponse>) responseObserver);
          break;
        case METHODID_REGISTER_POLICY:
          serviceImpl.registerPolicy((io.macp.proto.macp.v1.RegisterPolicyRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.RegisterPolicyResponse>) responseObserver);
          break;
        case METHODID_UNREGISTER_POLICY:
          serviceImpl.unregisterPolicy((io.macp.proto.macp.v1.UnregisterPolicyRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.UnregisterPolicyResponse>) responseObserver);
          break;
        case METHODID_GET_POLICY:
          serviceImpl.getPolicy((io.macp.proto.macp.v1.GetPolicyRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.GetPolicyResponse>) responseObserver);
          break;
        case METHODID_LIST_POLICIES:
          serviceImpl.listPolicies((io.macp.proto.macp.v1.ListPoliciesRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.ListPoliciesResponse>) responseObserver);
          break;
        case METHODID_WATCH_POLICIES:
          serviceImpl.watchPolicies((io.macp.proto.macp.v1.WatchPoliciesRequest) request,
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.WatchPoliciesResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_STREAM_SESSION:
          return (io.grpc.stub.StreamObserver<Req>) serviceImpl.streamSession(
              (io.grpc.stub.StreamObserver<io.macp.proto.macp.v1.StreamSessionResponse>) responseObserver);
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getInitializeMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.InitializeRequest,
              io.macp.proto.macp.v1.InitializeResponse>(
                service, METHODID_INITIALIZE)))
        .addMethod(
          getSendMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.SendRequest,
              io.macp.proto.macp.v1.SendResponse>(
                service, METHODID_SEND)))
        .addMethod(
          getStreamSessionMethod(),
          io.grpc.stub.ServerCalls.asyncBidiStreamingCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.StreamSessionRequest,
              io.macp.proto.macp.v1.StreamSessionResponse>(
                service, METHODID_STREAM_SESSION)))
        .addMethod(
          getGetSessionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.GetSessionRequest,
              io.macp.proto.macp.v1.GetSessionResponse>(
                service, METHODID_GET_SESSION)))
        .addMethod(
          getCancelSessionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.CancelSessionRequest,
              io.macp.proto.macp.v1.CancelSessionResponse>(
                service, METHODID_CANCEL_SESSION)))
        .addMethod(
          getGetManifestMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.GetManifestRequest,
              io.macp.proto.macp.v1.GetManifestResponse>(
                service, METHODID_GET_MANIFEST)))
        .addMethod(
          getListModesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.ListModesRequest,
              io.macp.proto.macp.v1.ListModesResponse>(
                service, METHODID_LIST_MODES)))
        .addMethod(
          getWatchModeRegistryMethod(),
          io.grpc.stub.ServerCalls.asyncServerStreamingCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.WatchModeRegistryRequest,
              io.macp.proto.macp.v1.WatchModeRegistryResponse>(
                service, METHODID_WATCH_MODE_REGISTRY)))
        .addMethod(
          getListRootsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.ListRootsRequest,
              io.macp.proto.macp.v1.ListRootsResponse>(
                service, METHODID_LIST_ROOTS)))
        .addMethod(
          getWatchRootsMethod(),
          io.grpc.stub.ServerCalls.asyncServerStreamingCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.WatchRootsRequest,
              io.macp.proto.macp.v1.WatchRootsResponse>(
                service, METHODID_WATCH_ROOTS)))
        .addMethod(
          getListExtModesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.ListExtModesRequest,
              io.macp.proto.macp.v1.ListExtModesResponse>(
                service, METHODID_LIST_EXT_MODES)))
        .addMethod(
          getRegisterExtModeMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.RegisterExtModeRequest,
              io.macp.proto.macp.v1.RegisterExtModeResponse>(
                service, METHODID_REGISTER_EXT_MODE)))
        .addMethod(
          getUnregisterExtModeMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.UnregisterExtModeRequest,
              io.macp.proto.macp.v1.UnregisterExtModeResponse>(
                service, METHODID_UNREGISTER_EXT_MODE)))
        .addMethod(
          getPromoteModeMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.PromoteModeRequest,
              io.macp.proto.macp.v1.PromoteModeResponse>(
                service, METHODID_PROMOTE_MODE)))
        .addMethod(
          getWatchSignalsMethod(),
          io.grpc.stub.ServerCalls.asyncServerStreamingCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.WatchSignalsRequest,
              io.macp.proto.macp.v1.WatchSignalsResponse>(
                service, METHODID_WATCH_SIGNALS)))
        .addMethod(
          getRegisterPolicyMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.RegisterPolicyRequest,
              io.macp.proto.macp.v1.RegisterPolicyResponse>(
                service, METHODID_REGISTER_POLICY)))
        .addMethod(
          getUnregisterPolicyMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.UnregisterPolicyRequest,
              io.macp.proto.macp.v1.UnregisterPolicyResponse>(
                service, METHODID_UNREGISTER_POLICY)))
        .addMethod(
          getGetPolicyMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.GetPolicyRequest,
              io.macp.proto.macp.v1.GetPolicyResponse>(
                service, METHODID_GET_POLICY)))
        .addMethod(
          getListPoliciesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.ListPoliciesRequest,
              io.macp.proto.macp.v1.ListPoliciesResponse>(
                service, METHODID_LIST_POLICIES)))
        .addMethod(
          getWatchPoliciesMethod(),
          io.grpc.stub.ServerCalls.asyncServerStreamingCall(
            new MethodHandlers<
              io.macp.proto.macp.v1.WatchPoliciesRequest,
              io.macp.proto.macp.v1.WatchPoliciesResponse>(
                service, METHODID_WATCH_POLICIES)))
        .build();
  }

  private static abstract class MACPRuntimeServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    MACPRuntimeServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return io.macp.proto.macp.v1.CoreProto.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("MACPRuntimeService");
    }
  }

  private static final class MACPRuntimeServiceFileDescriptorSupplier
      extends MACPRuntimeServiceBaseDescriptorSupplier {
    MACPRuntimeServiceFileDescriptorSupplier() {}
  }

  private static final class MACPRuntimeServiceMethodDescriptorSupplier
      extends MACPRuntimeServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    MACPRuntimeServiceMethodDescriptorSupplier(java.lang.String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (MACPRuntimeServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new MACPRuntimeServiceFileDescriptorSupplier())
              .addMethod(getInitializeMethod())
              .addMethod(getSendMethod())
              .addMethod(getStreamSessionMethod())
              .addMethod(getGetSessionMethod())
              .addMethod(getCancelSessionMethod())
              .addMethod(getGetManifestMethod())
              .addMethod(getListModesMethod())
              .addMethod(getWatchModeRegistryMethod())
              .addMethod(getListRootsMethod())
              .addMethod(getWatchRootsMethod())
              .addMethod(getListExtModesMethod())
              .addMethod(getRegisterExtModeMethod())
              .addMethod(getUnregisterExtModeMethod())
              .addMethod(getPromoteModeMethod())
              .addMethod(getWatchSignalsMethod())
              .addMethod(getRegisterPolicyMethod())
              .addMethod(getUnregisterPolicyMethod())
              .addMethod(getGetPolicyMethod())
              .addMethod(getListPoliciesMethod())
              .addMethod(getWatchPoliciesMethod())
              .build();
        }
      }
    }
    return result;
  }
}
