# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

SHELL := /bin/bash -e
SCRIPTS := $(realpath ../scripts)
FIND_PYTHON_FILES := $(SCRIPTS)/find-python-files
PIPENV := $(SCRIPTS)/run-pipenv
PYTEST := $(PIPENV) run pytest $(PYTEST_ARGS)
CYCLES := $(PIPENV) run py_import_cycles
CYCLES_THRESHOLD := 14
PYTEST_UNIT_TEST_OPTS = \
    -T unit \
    --doctest-modules \
    ../cmk/base \
    ../cmk/bi \
    ../cmk/fields \
    ../cmk/gui \
    ../cmk/post_rename_site \
    ../cmk/special_agents \
    ../cmk/update_config \
    ../cmk/utils \
    ../agent-receiver \
    ../omd/packages/omd \
    unit
PYTEST_ADDITIONAL_UNIT_TEST_OPTS = -m "not slow"
BLACK  := $(SCRIPTS)/run-black
THREE_TO_TWO := $(PIPENV) run 3to2
BANDIT := $(PIPENV) run bandit
FIND_INVALID_TEST_FILES := $(SCRIPTS)/find-invalid-autogen-files
ADDITIONAL_MYPY_ARGS := $(JUNIT_XML)
# Please note: We can currently not include defines.make as it would override
# the EDITIONS environment variable handed over by some jenkins test jobs.
# Looks like we need to cleanup the EDITION handling here.
GCC_TOOLCHAIN := /opt/gcc-$(shell make --no-print-directory --file=../defines.make print-GCC_VERSION)

# Since the unit tests (that are written for Python 3) are executed with Python
# 2.6 and 2.7, we need to convert them, just like it is done for the agent
# plugins (see agents/plugins/Makefile)
AGENT_PLUGIN_UNIT_TEST_FILES := $(wildcard agent-plugin-unit/test_*.py)
AGENT_PLUGIN_UNIT_TEST_FILES_PY2 := $(subst agent-plugin-unit,agent-plugin-unit/py2,$(AGENT_PLUGIN_UNIT_TEST_FILES))

# evaluate this only if needed, it slows down tab expansion otherwise.
# asio-asio*, googletest* and __pycache__ are excluded because they are present during CI call
SHELL_FILES_REL = $(shell cd ..; grep -rl \
    --exclude-dir="asio-asio*" \
    --exclude-dir="googletest*" \
    --exclude-dir="__pycache__" \
    --exclude-dir="deprecated" \
    --exclude-dir="node_modules" \
    --exclude-dir="omd" \
    --exclude="LIVEPROXYD" \
    --exclude="install-sh" \
    --exclude="code_examples.py" \
    '^\#!/.*sh' [^.]* 2>/dev/null)

# Due to https://github.com/pypa/pypi-support/issues/978, we need to disable Plugin tests for py2.6
# until we have a feasible solution or we drop the support for 2.6 completly.
PYTHON_VERSIONS := 2.7 3.3 3.4 3.5 3.6 3.7 3.8 3.9

.PHONY: clean sync-legacy-checks format-shell help prepare-protobuf-files prepare-playwright  bandit.ini \
	$(foreach VERS,$(PYTHON_VERSIONS),test-agent-plugin-unit-py$(VERS)-docker) \
	test-bandit test-code-quality test-code-quality-docker test-composition test-composition-docker \
	test-composition-docker-debug test-docker test-docker-docker test-format-python test-format-python-docker \
	test-format-shell test-format-js test-format-js-docker test-format-css test-format-css-docker \
	test-gui-crawl test-gui-crawl-docker test-xss-crawl test-xss-crawl-docker test-gui-e2e test-gui-e2e-docker \
	test-integration test-integration-docker test-integration-docker-debug \
	test-mypy test-mypy-raw itest-mypy-docker test-packaging test-pipenv-deps test-pylint test-pylint-docker \
	test-unit test-unit-docker test-unit-resilience test-unit-resilience-docker test-unit-coverage-html \
	test-unit-shell test-unit-shell-docker test-shellcheck test-cycles test-cycles-docker \
	test-tidy-livestatus test-tidy-core test-tidy-docker test-iwyu-livestatus test-iwyu-core test-iwyu-docker \
	test-unit-livestatus test-unit-core %-livestatus-docker %-core-docker \
	test-cargo-check test-cargo-check-docker test-cargo-test test-cargo-test-docker \
	test-cargo-fmt test-cargo-fmt-docker test-cargo-clippy test-cargo-clippy-docker

clean:
	$(RM) -r .mypy_cache $(AGENT_PLUGIN_UNIT_TEST_FILES_PY2)

sync-legacy-checks: $(patsubst ../checks/%,../cmk/base/legacy_checks/%.py,$(wildcard ../checks/*))
	@for i in ../cmk/base/legacy_checks/*.py; do \
	  j=$${i#../cmk/base/legacy_checks/}; \
	  test "$$j" == __init__.py && continue; \
	  test -f ../checks/$${j%.py} || rm -fv $$i; \
	done

../cmk/base/legacy_checks/%.py: ../checks/% ../checks/.header-for-pylint Makefile
	sed "s,@@ORIG-FILE@@,$(realpath $<)," ../checks/.header-for-pylint $< > $@

help:
	@echo "format-shell                        - Format shell agents"
	@for i in $(PYTHON_VERSIONS); do \
	    echo "test-agent-plugin-unit-py$${i}-docker - Run Agent plugin tests in container with Python $${i}"; \
	done
	@echo "test-bandit                         - Run bandit (security) tests"
	@echo "test-bandit-nosec-markers           - Check if all bandit #nosec markers are annotated properly"
	@echo "test-code-quality                   - Run code quality tests locally"
	@echo "test-code-quality-docker            - Run code quality tests in container"
	@echo "test-composition                    - Run composition tests locally"
	@echo "test-composition-docker             - Run composition tests in container"
	@echo "test-composition-docker-debug       - Run test container for manual debugging"
	@echo "test-docker                         - Run docker tests"
	@echo "test-docker-docker                  - Run docker tests in docker"
	@echo "test-format-python                  - Run formatting tests"
	@echo "test-format-python-docker           - Run formatting tests in docker"
	@echo "test-format-shell                   - Run the shell formatting"
	@echo "test-format-js                      - Run the JavaScript formatting"
	@echo "test-format-js-docker               - Run the JavaScript formatting in docker"
	@echo "test-format-css                     - Run the CSS formatting"
	@echo "test-format-css-docker              - Run the CSS formatting in docker"
	@echo "test-gui-crawl                      - Run GUI crawl locally"
	@echo "test-gui-crawl-docker               - Run GUI crawl in container"
	@echo "test-xss-crawl                      - Run XSS crawl locally"
	@echo "test-xss-crawl-docker               - Run XSS crawl in container"
	@echo "test-gui-e2e                        - Run GUI End-to-End locally"
	@echo "test-gui-e2e-docker                 - Run GUI End-to-End in container"
	@echo "test-integration                    - Run integration tests locally"
	@echo "test-integration-docker             - Run integration tests in container"
	@echo "test-integration-docker-debug       - Run test container for manual debugging"
	@echo "test-mypy                           - Run mypy"
	@echo "test-mypy-raw                       - Run mypy with raw edition config"
	@echo "test-mypy-docker                    - Run mypy in docker"
	@echo "test-packaging                      - Run packaging tests"
	@echo "test-pipenv-deps                    - Run pipenv dependency issue test"
	@echo "test-pylint                         - Run pylint based tests"
	@echo "test-shellcheck                     - Run shellcheck tests"
	@echo "test-unit                           - Run unit tests"
	@echo "test-unit-docker                    - Run unit tests in docker"
	@echo "test-unit-resilience                - Run unit tests multiple times and in random order"
	@echo "test-unit-resilience                - Run unit tests multiple times and in random order in docker"
	@echo "test-unit-coverage-html             - Create HTML coverage report for unit tests"
	@echo "test-unit-shell                     - Run shell unit tests"
	@echo "test-unit-shell-docker              - Run shell unit tests in docker"
	@echo "test-tidy-livestatus                - Run clang tidy for livestatus"
	@echo "test-tidy-core                      - Run clang tidy for core"
	@echo "test-tidy-docker                    - Run clang tidy for core and livestatus in docker"
	@echo "test-iwyu-livestatus                - Run the iwyu tool for livestatus"
	@echo "test-iwyu-core                      - Run the iwyu tool for the core"
	@echo "test-iwyu-docker                    - Run the iwyu tool for both in docker"
	@echo "test-unit-livestatus                - Run unit tests for livestatus"
	@echo "test-unit-core                      - Run unit tests for core"
	@echo "*-livestatus-docker                 - Run any of the livestatus tests in docker"
	@echo "test-cargo-check                    - Run 'cargo check' for all cargo projects"
	@echo "test-cargo-check-docker             - Run 'cargo check' for all cargo projects in docker"
	@echo "test-cargo-test                     - Run test cases of all cargo projects"
	@echo "test-cargo-test-docker              - Run test cases of all cargo projects in docker"
	@echo "test-cargo-fmt                      - Run rustfmt --check in all cargo projects"
	@echo "test-cargo-fmt-docker               - Run rustfmt --check in all cargo projects in docker"
	@echo "test-cargo-clippy                   - Run clippy in all cargo projects"
	@echo "test-cargo-clippy-docker            - Run clippy in all cargo projects in docker"

bandit.ini:
	( echo -n -e "[bandit]\ntargets: "; \
	  $(FIND_PYTHON_FILES) | tr '\n' ',' | sed 's/,$$//'; \
	  echo ) > bandit.ini
	( echo exclude: /tests >> bandit.ini )

format-shell:
	docker run --rm -v "$(realpath ..):/sh" -w /sh peterdavehello/shfmt shfmt -w -i 4 -ci $(SHELL_FILES_REL)

agent-plugin-unit/py2/test_%.py: agent-plugin-unit/test_%.py
	mkdir -p "$(dir $@)"
	cat "$<" | gawk -v text="# Do not test generated 2.x files\n# fmt: off\n# type: ignore" '!/^#/ && !p {print text; p=1} 1' > "$@"
	$(THREE_TO_TWO) --nofix=str --nobackups --write "$@" >/dev/null

$(foreach VERS,$(filter 2.%,$(PYTHON_VERSIONS)),test-agent-plugin-unit-py$(VERS)-docker): $(AGENT_PLUGIN_UNIT_TEST_FILES_PY2)

$(foreach VERS,$(PYTHON_VERSIONS),test-agent-plugin-unit-py$(VERS)-docker):
	# Clean up auto-generated files, which do not have a corresponding source file anymore
	flock ./agent-plugin-unit $(FIND_INVALID_TEST_FILES)
	# Recursive Makefiles suck big time...
	flock ../agents/plugins $(MAKE) -C ../agents/plugins
	PYTHON_VERSION="$(patsubst test-agent-plugin-unit-py%-docker,%,$@)" ; \
	case $$PYTHON_VERSION in \
	    2.*) SUFFIX="/py2" ;; \
	    *) SUFFIX="" ;; \
	esac ; \
	TEST_PATH="$(realpath agent-plugin-unit)$$SUFFIX" ; \
	IMAGE_HASH="$$(docker build --build-arg PYTHON_VERSION="$$PYTHON_VERSION" -q "$(realpath agent-plugin-unit)")" && \
	echo "Docker image: $$IMAGE_HASH" && \
	docker run \
	    --rm \
	    $(DOCKER_ADDOPTS) \
	    -e "PYTEST_ADDOPTS" \
	    -e "CI" \
	    -u $$(id -u):$$(id -g) \
	    -v "$$TEST_PATH:/tests" \
	    -v "$(realpath agent-plugin-unit)/datasets:/tests/datasets" \
	    -v "$(realpath ../agents):/agents" \
	    $$IMAGE_HASH \
	    python$$PYTHON_VERSION -m pytest --ignore=tests/py2/ "/tests"

test-bandit: bandit.ini
# Currently only care about high severity reported issues. Once this is reached,
# go and enable the medium/low checks.
	$(BANDIT) -c ../bandit.yaml -r -ll --ini bandit.ini $(BANDIT_OUTPUT_ARGS)

test-bandit-nosec-markers:
	$(PIPENV) run python bandit-nosec-markers/nosec_reason.py --doc bandit-nosec-markers/bandit-exclusions.md check $(realpath ..)

prepare-protobuf-files:
	$(MAKE) -C .. protobuf-files

prepare-playwright:
	../scripts/run-pipenv run playwright install-deps chromium
	../scripts/run-pipenv run playwright install chromium

test-integration-docker-debug test-composition-docker-debug:
	$(PIPENV) run scripts/run-dockerized.py debug

test-build-js:
	../scripts/check-webpack-build

test-composition-docker:
	$(PIPENV) run scripts/run-dockerized.py "test-composition"

test-composition:
	$(PYTEST) -p no:cov -T composition $(realpath composition)

test-docker-docker:
	DOCKER_RUN_ADDOPTS="-v $$HOME/.docker/config.json:$$HOME/.docker/config.json -v $$HOME/.cmk-credentials:$$HOME/.cmk-credentials --network=host -e HOME -e WORKSPACE -e VERSION -e EDITION" \
	    ../scripts/run-in-docker.sh make --quiet test-docker

test-docker:
	$(MAKE) -C ../docker test-lint-dockerfile test-lint-entrypoint
	$(PYTEST) -x -T docker --log-cli-level=INFO docker

test-format-python: test-format-python-isort test-format-python-black

test-format-python-isort: ../pyproject.toml
	if test -z "$$PYTHON_FILES"; then $(FIND_PYTHON_FILES); else echo "$$PYTHON_FILES"; fi | \
	xargs -n 1500 $(PIPENV) run isort --settings-path ../pyproject.toml --check-only --diff \
	exit $${PIPESTATUS[1]}

test-format-python-black: ../pyproject.toml
	if test -z "$$PYTHON_FILES"; then $(FIND_PYTHON_FILES); else echo "$$PYTHON_FILES"; fi | \
	xargs -n 1500 $(BLACK) --check --diff ;\
	exit $${PIPESTATUS[1]}

test-format-python-docker:
	../scripts/run-in-docker.sh make --quiet test-format-python

test-format-shell:
	docker run --rm -v "$(realpath ..):/sh" -w /sh peterdavehello/shfmt shfmt -d -i 4 -ci $(SHELL_FILES_REL)

test-format-js:
	cd ..; scripts/run-prettier --check --no-color --loglevel warn "{{enterprise/web,web}/htdocs/js/**/,}*.{j,t}s"

test-typescript-types:
	cd ..; scripts/check-typescript-types.sh

test-lint-js:
	cd ..; scripts/check-js-lint.sh

test-lint-js-docker:
	../scripts/run-in-docker.sh make --quiet test-lint-js

test-format-js-docker:
	../scripts/run-in-docker.sh make --quiet test-format-js

test-typescript-types-docker:
	../scripts/run-in-docker.sh make --quiet test-typescript-types

test-format-css:
	cd ..; scripts/run-prettier --check --no-color --loglevel warn "web/htdocs/themes/**/*.scss"

test-format-css-docker:
	../scripts/run-in-docker.sh make --quiet test-format-css

test-gui-crawl: prepare-playwright
	$(PYTEST) -T gui_crawl --log-cli-level=INFO $(realpath gui_crawl/test_gui_crawl.py)

test-gui-crawl-docker:
	$(PIPENV) run scripts/run-dockerized.py "test-gui-crawl"

test-xss-crawl: prepare-playwright
	XSS_CRAWL=1 $(PYTEST) -T gui_crawl --log-cli-level=INFO $(realpath gui_crawl/test_gui_crawl.py)

test-xss-crawl-docker:
	$(PIPENV) run scripts/run-dockerized.py "test-xss-crawl"

test-integration:
	CI=true $(PIPENV) run scripts/run-integration-test.py $(realpath integration)

test-gui-e2e: prepare-playwright
	$(PYTEST) -T gui_e2e --screenshot=only-on-failure --output="$$RESULT_PATH/" --log-cli-level=INFO $(realpath gui_e2e/)

test-gui-e2e-docker:
	$(PIPENV) run scripts/run-dockerized.py "test-gui-e2e"

test-integration-docker:
	$(PIPENV) run scripts/run-dockerized.py "test-integration"

test-license-headers:
	if test -z "$$PYTHON_FILES"; then $(FIND_PYTHON_FILES); else echo "$$PYTHON_FILES"; fi | \
	xargs -n 1500 --no-run-if-empty $(PYTEST) -T code_quality --log-cli-level=INFO $(realpath code_quality/test_license_headers.py) \
	--python-files;

test-license-headers-docker:
	../scripts/run-in-docker.sh make --quiet test-license-headers

test-pipfile:
	$(PYTEST) -T code_quality --log-cli-level=INFO $(realpath code_quality/test_pipfile.py);

test-pipfile-docker:
	../scripts/run-in-docker.sh make --quiet test-pipfile

test-file-content:
	if test -n "$$CHANGED_FILES"; then echo "--changed-files $$CHANGED_FILES"; else echo "--test-all-files"; fi | \
	xargs -n 1500 --no-run-if-empty $(PYTEST) -T code_quality --log-cli-level=INFO $(realpath code_quality/file_content);

test-file-content-docker:
	../scripts/run-in-docker.sh make --quiet test-file-content

test-werks:
	$(PYTEST) -T code_quality --log-cli-level=INFO $(realpath code_quality/test_werks.py);

test-werks-docker:
	../scripts/run-in-docker.sh make --quiet test-werks

test-code-quality: test-license-headers test-pipfile test-file-content test-werks

test-code-quality-docker:
	../scripts/run-in-docker.sh make --quiet test-code-quality

test-mypy: prepare-protobuf-files sync-legacy-checks
	cd .. ; scripts/run-mypy $(MYPY_ADDOPTS) $(ADDITIONAL_MYPY_ARGS) $$($(FIND_PYTHON_FILES) --omit-legacy-checks)

test-mypy-raw:
	$(MAKE) test-mypy ADDITIONAL_MYPY_ARGS="--config-file=$(realpath ../mypy-raw.ini)"

test-mypy-docker:
	../scripts/run-in-docker.sh make --quiet test-mypy

test-packaging:
	$(PYTEST) -T packaging packaging

test-pipenv-deps:
	$(PIPENV) check

test-pylint: prepare-protobuf-files sync-legacy-checks
	cd ..; $(PIPENV) run pylint --jobs=6 $(PYLINT_ARGS) $$($(FIND_PYTHON_FILES) --omit-legacy-checks)

test-pylint-docker:
	../scripts/run-in-docker.sh make --quiet test-pylint

test-shellcheck:
	cd .. && shellcheck $(SHELLCHECK_OUTPUT_ARGS) $(SHELL_FILES_REL)

test-cycles:
	$(CYCLES) \
		--graph no \
		--map enterprise:cee managed:cme plus:cpe \
		--packages cmk enterprise managed plus \
		--project-path $$(realpath -L ..) \
		--strategy dfs \
		--verbose 2>&1 | tee .py-import-cycles.txt || true
	(cat .py-import-cycles.txt && rm .py-import-cycles.txt) \
	| perl -ne '/Found (\d+)/ && exit ($$1 > $(CYCLES_THRESHOLD))'

test-cycles-docker:
	../scripts/run-in-docker.sh make --quiet test-cycles

test-unit: prepare-protobuf-files sync-legacy-checks
	$(PYTEST) \
		$(PYTEST_ADDITIONAL_UNIT_TEST_OPTS) \
		$(PYTEST_UNIT_TEST_OPTS)

test-unit-docker:
	../scripts/run-in-docker.sh make --quiet test-unit

test-unit-resilience: prepare-protobuf-files sync-legacy-checks
	$(PYTEST) \
		--count=2 \
		--random-order-bucket=global \
	        -m "not non_resilient" \
		$(PYTEST_ADDITIONAL_UNIT_TEST_OPTS) \
		$(PYTEST_UNIT_TEST_OPTS)

test-unit-resilience-docker:
	../scripts/run-in-docker.sh make test-unit-resilience

test-agent-plugin-docker:
	../scripts/run-in-docker.sh make $(foreach VERS,$(PYTHON_VERSIONS),test-agent-plugin-unit-py$(VERS)-docker)

test-unit-coverage-html: prepare-protobuf-files sync-legacy-checks
	$(PYTEST) \
		--cov=cmk \
		--cov-report=html \
		--cov-config=.coveragerc_unit \
		--no-cov-on-fail \
		$(PYTEST_ADDITIONAL_UNIT_TEST_OPTS) \
		$(PYTEST_UNIT_TEST_OPTS)

test-unit-shell:
	./unit-shell/runner.sh

test-unit-shell-docker:
	../scripts/run-in-docker.sh make test-unit-shell

%-livestatus-docker:
	../scripts/run-in-docker.sh make RESULTS=$(RESULTS) GERRIT_PATCHSET_REVISION=$(GERRIT_PATCHSET_REVISION) IWYU_EXTRA_ARGS="--gcc-toolchain=$(GCC_TOOLCHAIN)" CLANG_TIDY_EXTRA_ARGS="-extra-arg-before=--gcc-toolchain=$(GCC_TOOLCHAIN)" $*-livestatus

%-core-docker:
	../scripts/run-in-docker.sh make RESULTS=$(RESULTS) GERRIT_PATCHSET_REVISION=$(GERRIT_PATCHSET_REVISION) IWYU_EXTRA_ARGS="--gcc-toolchain=$(GCC_TOOLCHAIN)" CLANG_TIDY_EXTRA_ARGS="-extra-arg-before=--gcc-toolchain=$(GCC_TOOLCHAIN)" $*-core

test-tidy-livestatus:
	cd ../livestatus/src && ../../scripts/run-cxx-linter tidy $(GERRIT_PATCHSET_REVISION)

test-tidy-core:
	cd ../enterprise/core/src && ../../../scripts/run-cxx-linter tidy $(GERRIT_PATCHSET_REVISION)

test-tidy-docker:
	../scripts/run-in-docker.sh make -C .. tidy CLANG_TIDY_EXTRA_ARGS="-extra-arg-before=--gcc-toolchain=$(GCC_TOOLCHAIN)"

test-iwyu-livestatus:
	cd ../livestatus/src && ../../scripts/run-cxx-linter iwyu $(GERRIT_PATCHSET_REVISION)

test-iwyu-core:
	cd ../enterprise/core/src && ../../../scripts/run-cxx-linter iwyu $(GERRIT_PATCHSET_REVISION)

test-iwyu-docker:
	../scripts/run-in-docker.sh make -C .. iwyu IWYU_EXTRA_ARGS="--gcc-toolchain=$(GCC_TOOLCHAIN)"

test-unit-livestatus:
	cd ../livestatus/src && ./.f12

test-unit-core:
	cd ../enterprise/core/src && ./.f12

test-cargo-check:
	$(SCRIPTS)/run-cargo-command-in-projects check --all-targets

test-cargo-check-docker:
	$(SCRIPTS)/run-in-docker.sh make test-cargo-check

test-cargo-test:
	$(SCRIPTS)/run-cargo-command-in-projects test --all-targets

test-cargo-test-docker:
	$(SCRIPTS)/run-in-docker.sh make test-cargo-test

test-cargo-fmt:
	$(SCRIPTS)/run-cargo-command-in-projects fmt -- --check

test-cargo-fmt-docker:
	$(SCRIPTS)/run-in-docker.sh make test-cargo-fmt

test-cargo-clippy:
	$(SCRIPTS)/run-cargo-command-in-projects clippy --all-targets -- -D warnings

test-cargo-clippy-docker:
	$(SCRIPTS)/run-in-docker.sh make test-cargo-clippy

test-find-dirty-files-in-git:
	scripts/find_dirty_files_in_git

# Run `validate_changes` in live-mode i.e. not creating a JSON file
# containing build steps to be executed by Jenkins but directly running
# them.
what-gerrit-makes:
	WORKSPACE="$$(git rev-parse --show-toplevel)" ; \
	cd "$$WORKSPACE" ; \
	mkdir -p "$$WORKSPACE/results" ; \
	scripts/run-pipenv run buildscripts/scripts/validate_changes.py \
	    -e BASE_COMMIT_ID=origin/master \
	    -e WORKSPACE="$$WORKSPACE" \
	    -e RESULTS="$$WORKSPACE/results"
