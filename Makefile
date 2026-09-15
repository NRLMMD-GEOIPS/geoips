# Convenience targets for GeoIPS Docker builds and local Ansible runs.
#
#   make build-base
#   make build-full
#   make build-site EXTRA_PLUGINS=my_plugin
#   make build-dev                        # full dev image with editable install
#   make build-dev-quick                  # fast dev image (base only)
#   make testdata-full TESTDATA=/path/to/testdata  # download via ansible
#   make test-base     TESTDATA=/path/to/testdata  # run integration tests
#   make ansible-base                              # bare-metal install
#   make ansible-testdata-full                     # bare-metal test data download
#
# Test data default path is shared across worktrees.
# Override with TESTDATA=... or set GEOIPS_TESTDATA_DIR.
#
SHELL := /bin/bash
IMAGE_NAME ?= geoips
TAG        ?= dev
SHARED_DATA ?= $(HOME)/.geoips
TESTDATA   ?= $(or $(GEOIPS_TESTDATA_DIR),$(SHARED_DATA)/testdata)
TESTDATA_IMAGE ?= $(IMAGE_NAME):full-$(TAG)
EXTRA_PLUGINS ?=
GEOIPS_USE_PRIVATE_PLUGINS ?= false

# --- Docker builds -----------------------------------------------------------

build-base:
	DOCKER_BUILDKIT=1 docker build \
		--target geoips-base \
		--tag $(IMAGE_NAME):base-$(TAG) \
		--build-arg EXTRA_PLUGINS="$(EXTRA_PLUGINS)" \
		.

build-full:
	DOCKER_BUILDKIT=1 docker build \
		--target geoips-full \
		--tag $(IMAGE_NAME):full-$(TAG) \
		--build-arg EXTRA_PLUGINS="$(EXTRA_PLUGINS)" \
		.

build-site:
	DOCKER_BUILDKIT=1 docker build \
		--target geoips-site \
		--tag $(IMAGE_NAME):site-$(TAG) \
		--build-arg EXTRA_PLUGINS="$(EXTRA_PLUGINS)" \
		--build-arg GEOIPS_USE_PRIVATE_PLUGINS="$(GEOIPS_USE_PRIVATE_PLUGINS)" \
		.

build-dev:
	DOCKER_BUILDKIT=1 docker build \
		--target dev \
		--tag $(IMAGE_NAME):dev-$(TAG) \
		--build-arg EXTRA_PLUGINS="$(EXTRA_PLUGINS)" \
		--build-arg GEOIPS_USE_PRIVATE_PLUGINS="$(GEOIPS_USE_PRIVATE_PLUGINS)" \
		.

build-dev-quick:
	DOCKER_BUILDKIT=1 docker build \
		--target dev-quick \
		--tag $(IMAGE_NAME):dev-quick-$(TAG) \
		.

build-production:
	DOCKER_BUILDKIT=1 docker build \
		--target production \
		--tag $(IMAGE_NAME):prod-$(TAG) \
		.

# --- Docker tests (test data mounted, never baked in) -----------------------

test-base:
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(TESTDATA_IMAGE) \
		pytest -vv -m "base and integration"

test-full:
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(TESTDATA_IMAGE) \
		pytest -vv -m "full and integration"

test-unit:
	docker run --rm $(IMAGE_NAME):base-$(TAG) \
		pytest -vv tests/unit_tests

# --- Test data download (via ansible) ----------------------------------------
# Test data target builds its image only if it doesn't exist yet.
# Set TESTDATA_IMAGE to a pre-built tag to skip building entirely.
# Downloads persist on the host via the mounted volume.
# geoips config install is idempotent — cached data is a fast no-op.

_testdata-image-check:
	@if ! docker image inspect $(TESTDATA_IMAGE) >/dev/null 2>&1; then \
		echo "Image $(TESTDATA_IMAGE) not found, building..."; \
		DOCKER_BUILDKIT=1 docker build \
			--target geoips-full \
			--tag $(TESTDATA_IMAGE) \
			--build-arg EXTRA_PLUGINS="$(EXTRA_PLUGINS)" \
			.; \
	fi

testdata-base: _testdata-image-check
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(TESTDATA_IMAGE) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base \
				-e geoips_testdata_dir=/geoips_testdata -v"

testdata-full: _testdata-image-check
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(TESTDATA_IMAGE) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base,full \
				-e geoips_testdata_dir=/geoips_testdata -v"

testdata-site: _testdata-image-check
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(TESTDATA_IMAGE) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base,full,site \
				-e geoips_testdata_dir=/geoips_testdata \
				-e geoips_use_private_plugins=$(GEOIPS_USE_PRIVATE_PLUGINS) -v"

# For testing CI: explicit build + data + test cycle (no image reuse)
testdata-full-build: build-full
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(IMAGE_NAME):full-$(TAG) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base,full \
				-e geoips_testdata_dir=/geoips_testdata -v"

testdata-site-build: build-site
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(IMAGE_NAME):site-$(TAG) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base,full,site \
				-e geoips_testdata_dir=/geoips_testdata \
				-e geoips_use_private_plugins=$(GEOIPS_USE_PRIVATE_PLUGINS) -v"

# --- Test data verification (checksums, no re-download) -----------------------

testdata-verify:
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(TESTDATA_IMAGE) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base,full \
				-e geoips_testdata_dir=/geoips_testdata -v"

# --- Bare-metal Ansible (no Docker) -----------------------------------------

ansible-base:
	cd tests/ansible && ansible-playbook playbooks/install.yml --tags base \
		-e editable_pip_install=true -v

ansible-full:
	cd tests/ansible && ansible-playbook playbooks/install.yml --tags base,full \
		-e editable_pip_install=true -v

ansible-site:
	cd tests/ansible && ansible-playbook playbooks/install.yml --tags base,full,site \
		-e editable_pip_install=true \
		-e "extra_plugin_packages=$(EXTRA_PLUGINS)" \
		-e "geoips_use_private_plugins=$(GEOIPS_USE_PRIVATE_PLUGINS)" -v

# Bare-metal test data download (requires geoips already installed)
ansible-testdata-base:
	cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base -v

ansible-testdata-full:
	cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base,full -v

ansible-testdata-site:
	cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base,full,site \
		-e "geoips_use_private_plugins=$(GEOIPS_USE_PRIVATE_PLUGINS)" -v

.PHONY: build-base build-full build-site build-dev build-dev-quick \
        build-production \
        test-base test-full test-unit \
        testdata-base testdata-full testdata-site \
        testdata-full-build testdata-site-build \
        testdata-verify \
        _testdata-image-check \
        ansible-base ansible-full ansible-site \
        ansible-testdata-base ansible-testdata-full ansible-testdata-site
