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
		--file package/suse-migration-services.changes --utc >> \
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
	# include grub.d dir in MANIFEST
	sed -ie s'@prune grub.d@graft grub.d@' MANIFEST.in
	rm MANIFEST.ine
	python3 setup.py sdist
	# create tarball with grub.d + suse-migration-services
	mv dist/suse_migration_services-*.tar.gz  \
		dist/suse-migration-sle15-activation.tar.gz
	# restore MANIFEST.ini
	git checkout MANIFEST.in
	# check MANIFEST.in has prune grub.d
	# raise error if not
	$(eval current_value = $(shell grep "prune grub.d" MANIFEST.in))
	$(eval expected_value = "prune grub.d")

	@if [ "$(current_value)" != $(expected_value) ]; then\
	   echo "MANIFEST.in does not have '$(expected_value)'";\
           exit 1;\
	fi

.PHONY: test
test:
	tox

check:
	tox -e check
