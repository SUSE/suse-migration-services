#
# spec file for package suse-migration-rpm
#
# Copyright (c) 2018 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           suse-migration-rpm
Version:        1.0.1
Release:        0
Summary:        Migration enablement package
License:        GPL-3.0-or-later
Group:          System/Management
Url:            https://github.com/SUSE/suse-migration-services
Source:         %{name}.tar.gz
BuildRequires:  filesystem
Requires:       suse-migration-services
Requires:       build
Requires:       perl(Date::Parse)
Requires:       p7zip-full
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
OBS kiwi_post_run hook to wrap the kiwi-produced Migration live
ISO image in an rpm package.

%prep
%setup -q -n %{name}

%build

%install
mkdir -p %{buildroot}/usr/lib/build/
install -m 644 image.spec.in %{buildroot}/usr/lib/build/
install -m 755 kiwi_post_run %{buildroot}/usr/lib/build/

%files
%defattr(-,root,root)
/usr/lib/build/kiwi_post_run
/usr/lib/build/image.spec.in

%changelog
