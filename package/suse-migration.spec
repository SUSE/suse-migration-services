#
# spec file for package suse-migration
#
# Copyright (c) 2024 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.
#
# Please submit bugfixes or comments via https://bugs.opensuse.org/
#
Name:             suse-migration
Version:          1.1.0
Release:          0
Url:              https://github.com/SUSE/suse-migration-services
Summary:          SUSE Distribution Migration tools
License:          GPL-3.0+
Group:            System/Management
Source:           migrate
BuildRoot:        %{_tmppath}/%{name}-%{version}-build
Requires:         podman
Requires:         sudo
BuildArch:        noarch

%description
The migrate tool to start the migration as container based process

%prep
#%setup -q -n suse_migration_services-%{version}

%build

%install
install -D -m 755 %SOURCE0 \
    %{buildroot}%{_sbindir}/migrate

%files
%{_sbindir}/migrate

%changelog
