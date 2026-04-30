# Convenience targets for GeoIPS Docker builds and local Ansible runs.
#
#   make build-base
#   make build-full
#   make build-site EXTRA_PLUGINS=my_plugin
#   make testdata-full TESTDATA=/path/to/testdata  # download via ansible
#   make test-base     TESTDATA=/path/to/testdata  # run integration tests
#   make ansible-base                              # bare-metal install
#   make ansible-testdata-full                     # bare-metal test data download
#
SHELL := /bin/bash
IMAGE_NAME ?= geoips
TAG        ?= dev
TESTDATA   ?= $(GEOIPS_TESTDATA_DIR)
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

build-production:
	DOCKER_BUILDKIT=1 docker build \
		--target production \
		--tag $(IMAGE_NAME):prod-$(TAG) \
		.

# --- Docker tests (test data mounted, never baked in) -----------------------

test-base: build-full
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(IMAGE_NAME):full-$(TAG) \
		pytest -vv -m "base and integration"

test-full: build-full
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(IMAGE_NAME):full-$(TAG) \
		pytest -vv -m "full and integration"

test-unit: build-base
	docker run --rm $(IMAGE_NAME):base-$(TAG) \
		pytest -vv tests/unit_tests

# --- Test data download (via ansible) ----------------------------------------
# Docker targets run the ansible playbook inside the container with the
# testdata directory mounted as a volume so downloads persist on the host.
# geoips config install is idempotent — cached data is a fast no-op.

testdata-base: build-base
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(IMAGE_NAME):base-$(TAG) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base \
				-e geoips_testdata_dir=/geoips_testdata -v"

testdata-full: build-full
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(IMAGE_NAME):full-$(TAG) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base,full \
				-e geoips_testdata_dir=/geoips_testdata -v"

testdata-site: build-site
	mkdir -p $(TESTDATA)
	docker run --rm \
		-v $(TESTDATA):/geoips_testdata \
		$(IMAGE_NAME):site-$(TAG) \
		bash -c "cd /packages/geoips/tests/ansible \
			&& ansible-playbook playbooks/test_data.yml \
				--tags base,full,site \
				-e geoips_testdata_dir=/geoips_testdata \
				-e geoips_use_private_plugins=$(GEOIPS_USE_PRIVATE_PLUGINS) -v"

# --- Bare-metal Ansible (no Docker) -----------------------------------------

ansible-base:
	cd tests/ansible && ansible-playbook playbooks/install.yml --tags base \
		-e pip_editable=true -v

ansible-full:
	cd tests/ansible && ansible-playbook playbooks/install.yml --tags base,full \
		-e pip_editable=true -v

ansible-site:
	cd tests/ansible && ansible-playbook playbooks/install.yml --tags base,full,site \
		-e pip_editable=true \
		-e "extra_plugins=$(EXTRA_PLUGINS)" \
		-e "geoips_use_private_plugins=$(GEOIPS_USE_PRIVATE_PLUGINS)" -v

# Bare-metal test data download (requires geoips already installed)
ansible-testdata-base:
	cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base -v

ansible-testdata-full:
	cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base,full -v

ansible-testdata-site:
	cd tests/ansible && ansible-playbook playbooks/test_data.yml --tags base,full,site \
		-e "geoips_use_private_plugins=$(GEOIPS_USE_PRIVATE_PLUGINS)" -v

.PHONY: build-base build-full build-site build-production \
        test-base test-full test-unit \
        testdata-base testdata-full testdata-site \
        ansible-base ansible-full ansible-site \
        ansible-testdata-base ansible-testdata-full ansible-testdata-site
