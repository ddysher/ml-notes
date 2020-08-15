#include "proxy_wasm_intrinsics.h"

class ExampleRootContext: public RootContext {
public:
  explicit ExampleRootContext(uint32_t id, StringView root_id): RootContext(id, root_id) {}

  bool onStart(size_t) override;
};

class ExampleContext: public Context {
public:
  explicit ExampleContext(uint32_t id, RootContext* root) : Context(id, root) {}

  FilterHeadersStatus onResponseHeaders(uint32_t, bool) override;

  FilterStatus onDownstreamData(size_t, bool) override;
};

static RegisterContextFactory register_FilterContext(CONTEXT_FACTORY(ExampleContext),
                                                      ROOT_FACTORY(ExampleRootContext),
                                                      "my_root_id");

// onStart is called once when wasm module is loaded.
bool ExampleRootContext::onStart(size_t n) {
  LOG_DEBUG("ready to process streams");
  return true;
}

FilterHeadersStatus ExampleContext::onResponseHeaders(uint32_t, bool) {
  addResponseHeader("resp-header-demo", "added by our filter");
  return FilterHeadersStatus::Continue;
}

FilterStatus ExampleContext::onDownstreamData(size_t, bool) {
  auto res = setBuffer(WasmBufferType::NetworkDownstreamData, 0, 0, "prepend payload to downstream data");

   if (res != WasmResult::Ok) {
     LOG_ERROR("Modifying downstream data failed: " + toString(res));
      return FilterStatus::StopIteration;
   }
   return FilterStatus::Continue;
}
