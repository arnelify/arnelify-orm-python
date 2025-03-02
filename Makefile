# Boot Makefile
# See https://www.gnu.org/software/make/manual/make.html for more about make.

# ENGINE
ENGINE = g++
ENGINE_FLAGS = -std=c++2b

# PATH
PATH_BIN = $(CURDIR)/tests/bin/index.bin
PATH_SRC = $(CURDIR)/tests/index.py

# INC
INC_CPP = -I $(CURDIR)/src/cpp
INC_INCLUDE = -L /usr/include
INC_JSONCPP = -I /usr/include/jsoncpp/json
INC = ${INC_CPP} ${INC_INCLUDE} ${INC_JSONCPP}

# LINK
LINK_JSONCPP = -ljsoncpp
LINK_ZLIB = -lz
LINK = ${LINK_JSONCPP} ${LINK_ZLIB}

# PYTHON
PYTHON = venv/bin/python
PYTHON_FLAGS = -m
PYPI = venv/bin/pip

# NUITKA
NUITKA = venv/bin/nuitka
NUITKA_FLAGS = --standalone --onefile

# SCRIPTS
install:
	clear && find . -type d -name '__pycache__' -exec rm -r {} +
	rm -rf build && rm -rf dist && rm -rf venv
	python ${PYTHON_FLAGS} venv venv
	${PYPI} install -r requirements.txt

build:
	clear && rm -rf build/* && rm -rf dist/*
	${PYTHON} setup.py sdist bdist_wheel --plat-name=manylinux2014_x86_64
	${PYTHON} ${PYTHON_FLAGS} index

test:
	clear && mkdir -p tests/bin && rm -rf tests/bin/*
	${PYTHON} ${PYTHON_FLAGS} tests.index

test_nuitka:
	clear && mkdir -p tests/bin && rm -rf tests/bin/*
	${NUITKA} ${NUITKA_FLAGS} --output-dir=tests/bin ${PATH_SRC} && clear
	${PATH_BIN}

.PHONY: build test