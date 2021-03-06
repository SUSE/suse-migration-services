version := $(shell python3 -c 'from suse_migration_services.version import __VERSION__; print(__VERSION__)')

build: check test
	rm -f dist/*
	# create setup.py variant for rpm build.
	# delete module versions from setup.py for building an rpm
	# the dependencies to the python module rpm packages is
	# managed in the spec file
	sed -ie "s@>=[0-9.]*'@'@g" setup.py
	# build the sdist source tarball
	python3 setup.py sdist
	# restore original setup.py backed up from sed
	mv setup.pye setup.py
	# provide rpm source tarball
	mv dist/suse_migration_services-${version}.tar.gz \
		dist/suse-migration-services.tar.gz
	# update rpm changelog using reference file
	helper/update_changelog.py \
		--since package/suse-migration-services.changes.ref --utc > \
        dist/suse-migration-services.changes
	helper/update_changelog.py \
		--file package/suse-migration-services.changes >> \
        dist/suse-migration-services.changes
	# update package version in spec file
	cat package/suse-migration-services-spec-template \
		| sed -e s'@%%VERSION@${version}@' \
		> dist/suse-migration-services.spec
	# provide rpm rpmlintrc
	cp package/suse-migration-services-rpmlintrc dist

sle15_activation: check
	rm -f dist/*
	# update rpm changelog using reference file
	helper/update_changelog.py \
		--since package/suse-migration-sle15-activation.changes.ref \
		--from package/suse-migration-sle15-activation-spec-template \
		--from grub.d --utc > \
		dist/suse-migration-sle15-activation.changes
	helper/update_changelog.py \
		--file package/suse-migration-sle15-activation.changes >> \
		dist/suse-migration-sle15-activation.changes
	# update package version in spec file
	cat package/suse-migration-sle15-activation-spec-template \
		| sed -e s'@%%VERSION@${version}@' \
		> dist/suse-migration-sle15-activation.spec
	tar -czf dist/suse-migration-sle15-activation.tar.gz grub.d

.PHONY: test
test:
	tox -e unit_py3

check:
	tox -e check
