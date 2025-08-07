buildroot = /
python_version = 3
python_lookup_name = python$(python_version)
python = $(shell which $(python_lookup_name))
sc_disable = SC1091,SC1090,SC2001,SC2174,SC1117

version := $(shell \
	$(python) -c \
	'from suse_migration_services.version import __VERSION__; print(__VERSION__)'\
)

tar: clean check test
	# build the sdist source tarball
	poetry build --format=sdist

build: tar
	# provide rpm source tarball
	mv dist/suse_migration_services-${version}.tar.gz \
		dist/suse-migration-services.tar.gz
	# update rpm changelog using reference file
	helper/update_changelog.py \
		--since package/suse-migration-services.changes.ref --utc > \
        dist/suse-migration-services.changes
	helper/update_changelog.py \
		--file package/suse-migration-services.changes --utc >> \
        dist/suse-migration-services.changes
	# update package version in spec file
	cat package/suse-migration-services-spec-template \
		| sed -e s'@%%VERSION@${version}@' \
		> dist/suse-migration-services.spec
	# provide rpm rpmlintrc
	cp package/suse-migration-services-rpmlintrc dist

sle15_activation: tar
	# provide rpm source tarball
	mv dist/suse_migration_services-*.tar.gz  \
		dist/suse-migration-sle15-activation.tar.gz
	# update rpm changelog using reference file
	helper/update_changelog.py \
		--since package/suse-migration-sle15-activation.changes.ref \
		--from package/suse-migration-sle15-activation-spec-template \
		--from grub.d --utc > \
		dist/suse-migration-sle15-activation.changes
	helper/update_changelog.py \
		--file package/suse-migration-sle15-activation.changes --utc >> \
		dist/suse-migration-sle15-activation.changes
	# update package version in spec file
	cat package/suse-migration-sle15-activation-spec-template \
		| sed -e s'@%%VERSION@${version}@' \
		> dist/suse-migration-sle15-activation.spec

sle16_activation: tar
	# provide rpm source tarball
	mv dist/suse_migration_services-*.tar.gz  \
		dist/suse-migration-sle16-activation.tar.gz
	# update rpm changelog using reference file
	helper/update_changelog.py \
		--since package/suse-migration-sle16-activation.changes.ref \
		--from package/suse-migration-sle16-activation-spec-template \
		--from grub.d --utc > \
		dist/suse-migration-sle16-activation.changes
	helper/update_changelog.py \
		--file package/suse-migration-sle16-activation.changes --utc >> \
		dist/suse-migration-sle16-activation.changes
	# update package version in spec file
	cat package/suse-migration-sle16-activation-spec-template \
		| sed -e s'@%%VERSION@${version}@' \
		> dist/suse-migration-sle16-activation.spec

suse-migration-rpm: clean check test
	mkdir -p dist
	tar --sort=name --owner=0 --group=0 --numeric-owner \
		-czf dist/suse-migration-rpm.tar.gz \
		-C image/package suse-migration-rpm
	cp image/package/suse-migration-rpm.spec dist/suse-migration-rpm.spec
	cp image/package/suse-migration-rpm.changes dist/suse-migration-rpm.changes

SLES15-SAP_Migration: clean check test
	mkdir -p dist
	tar --sort=name --owner=0 --group=0 --numeric-owner \
		--transform 's,^\./,,' \
		-czf dist/root.tar.gz \
		-C image/pubcloud/product/sles_sap/root .
	cp image/pubcloud/product/sles_sap/config.kiwi dist/config.kiwi
	cp image/pubcloud/product/sles_sap/config.sh dist/config.sh
	cp image/pubcloud/product/sles_sap/SLES15-SAP_Migration.changes dist/SLES15-SAP_Migration.changes

SLES16-Migration: clean check test
	mkdir -p dist
	tar --sort=name --owner=0 --group=0 --numeric-owner \
		--transform 's,^\./,,' \
		-czf dist/root.tar.gz \
		-C image/generic/sle16/root .
	cp image/generic/sle16/config.kiwi dist/config.kiwi
	cp image/generic/sle16/config.sh dist/config.sh
	cp image/generic/sle16/SLES16-Migration.changes dist/SLES16-Migration.changes

SLES15-Migration: clean check test
	mkdir -p dist
	tar --sort=name --owner=0 --group=0 --numeric-owner \
		--transform 's,^\./,,' \
		-czf dist/root.tar.gz \
		-C image/pubcloud/sle15/root .
	cp image/pubcloud/sle15/config.kiwi dist/config.kiwi
	cp image/pubcloud/sle15/config.sh dist/config.sh

setup:
	poetry install --all-extras

check: setup
	# shell code checks
	bash -c 'shellcheck -e ${sc_disable} tools/* grub.d/* -s bash'
	# python flake tests
	poetry run flake8 --statistics -j auto --count suse_migration_services
	poetry run flake8 --statistics -j auto --count test/unit

test: setup
	# python static code checks
	poetry run mypy suse_migration_services
	# unit tests
	poetry run bash -c 'pushd test/unit && pytest -n 5 \
		--doctest-modules \
		--cov=suse_migration_services \
		--no-cov-on-fail \
		--cov-report=term-missing \
		--cov-fail-under=100 \
		--cov-config .coveragerc'

clean:
	rm -rf dist
