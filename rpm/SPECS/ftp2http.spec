%define name ftp2http
%define version 0.1
%define release 1

Summary: FTP to HTTP server
Name: %{name}
Version: %{version}
Release: %{release}
License: MIT
Group: System Environment/Daemons
BuildRoot: %{_tmppath}/%{package_name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: x86_64
Vendor: Raymond Butcher <randomy@gmail.com>
Url: https://github.com/apn-online/ftp2http

BuildRequires: libffi-devel
BuildRequires: openssl-devel
BuildRequires: python
BuildRequires: python-pip
BuildRequires: python-virtualenv

Requires: python

Source0: %{name}-%{version}.tar.gz

%description
FTP2HTTP is an FTP server which pushes uploaded files directly to a HTTP URL.

%prep

    rm -rf $RPM_BUILD_DIR/*
    rm -rf $RPM_BUILD_ROOT/*

%setup

%build

%install

    # Create the virtual environment.
    mkdir -p $RPM_BUILD_ROOT/usr/lib/ftp2http
    virtualenv --no-site-packages --distribute $RPM_BUILD_ROOT/usr/lib/ftp2http
    
    # Install ftp2http (and its dependencies).
    $RPM_BUILD_ROOT/usr/lib/ftp2http/bin/pip install ftp2http-0.1.tar.gz
    
    # Make the environment work when moved to another path.
    # But remove these scripts first because they have issues.
    rm $RPM_BUILD_ROOT/usr/lib/ftp2http/bin/activate.fish
    rm $RPM_BUILD_ROOT/usr/lib/ftp2http/bin/activate.csh
    virtualenv --relocatable $RPM_BUILD_ROOT/usr/lib/ftp2http
    
    # Make the ftp2http bin script available.
    mkdir -p $RPM_BUILD_ROOT/usr/bin
    echo '#!/bin/sh
/usr/lib/ftp2http/bin/ftp2http $*' > $RPM_BUILD_ROOT/usr/bin/ftp2http
    chmod a+x $RPM_BUILD_ROOT/usr/bin/ftp2http
    
    # Copy the default configuration file.
    mkdir $RPM_BUILD_ROOT/etc
    cp ftp2http.conf $RPM_BUILD_ROOT/etc/ftp2http.conf

%clean

    rm -rf $RPM_BUILD_DIR/*
    rm -rf $RPM_BUILD_ROOT/*

%files

    /usr/bin/ftp2http
    /usr/lib/ftp2http

%config(noreplace) /etc/ftp2http.conf

%defattr(-,root,root)
