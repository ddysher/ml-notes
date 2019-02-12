# docker run -e uid="$(id -u)" -e gid="$(id -g)" -v $PWD:/work -w /work wasmsdk:v2 /build_wasm.sh

PROXY_WASM_CPP_SDK=/sdk

all: hellworld.wasm
	chown ${uid}.${gid} $^

include ${PROXY_WASM_CPP_SDK}/Makefile.base_lite
