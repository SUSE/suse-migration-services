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
BuildRequires:  sed
Requires:       suse-migration-services
Requires:       build
Requires:       perl(Date::Parse)
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
OBS kiwi_post_run hook to wrap the kiwi-produced Migration live
ISO image in an rpm package.

%prep
%setup -q -n %{name}

%build

%install
mkdir -p %{buildroot}/usr/lib/build/

%if 0%{?suse_version} >= 1600 && 0%{?is_opensuse}
# suse-migration-rpm building for SLE16, is used when building the SLE16
# based live migration image for SLE15. As such the later package with
# the image gets installed to a SLE15 system. The min SLE version must
# be set to 15.4 (SLE15 SP4)
sed -ie 's@__MINVERSION__@15.4@' image.spec.in
%elif 0%{?sle_version} >= 150000 && !0%{?is_opensuse}
# suse-migration-rpm building for SLE15, is used when building the SLE15
# based live migration image for SLE12. As such the later package with
# the image gets installed to a SLE12 system. The min SLE version must
# be set to 12.3 (SLE12 SP3)
sed -ie 's@__MINVERSION__@12.3@' image.spec.in
%else
# suse-migration-rpm building for unknown SLES, set min SLE version
# to the lowest we support
sed -ie 's@__MINVERSION__@12.3@' image.spec.in
%endif

install -m 644 image.spec.in %{buildroot}/usr/lib/build/
install -m 755 kiwi_post_run %{buildroot}/usr/lib/build/

%files
%defattr(-,root,root)
/usr/lib/build/kiwi_post_run
/usr/lib/build/image.spec.in

%changelog
