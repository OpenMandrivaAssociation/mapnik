%define major	2
%define libname %mklibname %{name} %{major}
%define devname %mklibname -d %{name}

Summary:	Free Toolkit for developing mapping applications
Name:		mapnik
Version:	2.1.0
Release:	2
Group:		Communications
License:	LGPLv2+
URL:		http://mapnik.org/
Source0:	https://github.com/downloads/mapnik/mapnik/%{name}-v%{version}.tar.bz2
Source1:	mapnik-data.license
Source2:	no_date_footer.html
Source3:	viewer.desktop
Source4:	.abf.yml

BuildRequires:	chrpath
BuildRequires:	desktop-file-utils
BuildRequires:	doxygen
BuildRequires:	scons
BuildRequires:	pkgconfig(libagg)
BuildRequires:	boost-devel
BuildRequires:	gdal-devel
BuildRequires:	pkgconfig(icu-i18n)
BuildRequires:	jpeg-devel
BuildRequires:	libtool-devel
BuildRequires:	postgresql-devel
BuildRequires:	qt4-devel
BuildRequires:	tiff-devel
BuildRequires:	pkgconfig(cairomm-1.0)
BuildRequires:	pkgconfig(freetype2)
BuildRequires:	pkgconfig(libpng)
BuildRequires:	pkgconfig(libxml-2.0)
BuildRequires:	pkgconfig(proj)
BuildRequires:	pkgconfig(pycairo)
BuildRequires:	pkgconfig(python)

Requires:	fonts-ttf-dejavu

%description
Mapnik is a Free Toolkit for developing mapping applications.
It's written in C++ and there are Python bindings to
facilitate fast-paced agile development. It can comfortably
be used for both desktop and web development, which was something
I wanted from the beginning.

Mapnik is about making beautiful maps. It uses the AGG library
and offers world class anti-aliasing rendering with subpixel
accuracy for geographic data. It is written from scratch in
modern C++ and doesn't suffer from design decisions made a decade
ago. When it comes to handling common software tasks such as memory
management, filesystem access, regular expressions, parsing and so
on, Mapnik doesn't re-invent the wheel, but utilises best of breed
industry standard libraries from boost.org 

%package -n %{libname}
Summary: Mapnik is a Free toolkit for developing mapping applications
Group: System/Libraries

%description -n %{libname}
This package contains the shared library for %{name}.

%package -n %{devname}
Summary: Mapnik is a Free toolkit for developing mapping applications
Group: Development/C++
Requires: %{libname} = %{version}-%{release}
Provides: %{name}-devel = %{version}-%{release}
Obsoletes: %{name}-devel

%description -n %{devname}
This package contains the development files for %{name}.

%package python
Summary:  Python bindings for the Mapnik spatial visualization library
License:  GPLv2+
Group:    Development/Python
Requires: %{name} = %{version}-%{release}
Requires: python-imaging
Requires: python-lxml

%description python
Language bindings to enable the Mapnik library to be used from python

%package utils
License:  GPLv2+
Summary:  Utilities distributed with the Mapnik spatial visualization library
Group:    Communications
Requires: %{name} = %{version}-%{release}

%description utils
Miscellaneous utilities distributed with the Mapnik spatial visualization
library

%prep
%setup -q -n %{name}-v%{version}
%apply_patches

# clean SVN
find . -type d -name .svn -exec rm -rf '{}' +

# get rid of local agg, tinyxml and fonts
rm -rf agg tinyxml fonts

set +x
for f in `find . -type f` ; do
   if file $f | grep -q ISO-8859 ; then
      set -x
      iconv -f ISO-8859-1 -t UTF-8 $f > ${f}.tmp && \
         mv -f ${f}.tmp $f
      set +x
   fi
   if file $f | grep -q CRLF ; then
      set -x
      sed -i -e 's|\r||g' $f
      set +x
   fi
done
set -x

# fix spurious exec flag
chmod -x demo/viewer/images/*.png
chmod -x demo/data/test/regenerate.sh
find . -type d -perm /g+s -exec chmod -s '{}' \;

# fix wrong path in some demo files
sed -i -e 's|/lib/mapnik/input/|/%{name}/input/|g' demo/c++/rundemo.cpp

sed -i -e 's|/opt/%{name}/include|../../include|g' demo/viewer/viewer.pro
sed -i -e 's|/opt/boost/include/boost-1_39|%{_includedir}/boost|g' demo/viewer/viewer.pro
sed -i -e 's|/usr/X11/include/freetype2|%{_includedir}/freetype2|g' demo/viewer/viewer.pro
sed -i -e 's|-L/opt/mapnik/lib|-L../../src/|g' demo/viewer/viewer.pro
sed -i -e 's|-L/opt/boost/lib|-L/usr/%{_lib}|g' demo/viewer/viewer.pro
sed -i -e 's|/usr/local|/usr|g' demo/viewer/viewer.pro

%build
# linkage errors
#sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\',|g" plugins/input/gdal/SConscript
#sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\',|g" plugins/input/postgis/SConscript
#sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\',|g" plugins/input/shape/SConscript
#sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\'|g" plugins/input/raster/SConscript

# fix build flags
sed -i -e "s|common_cxx_flags = .-D\%s|common_cxx_flags = \'-D\%s %optflags -DBOOST_FILESYSTEM_VERSION=3 |g" SConstruct


# WARNING smp may break build
# %{?_smp_mflags}
scons         PREFIX=%{_prefix} \
              THREADING=multi \
              XMLPARSER=libxml2 \
              GDAL_INCLUDES=%{_includedir}/gdal \
              INTERNAL_LIBAGG=False \
              LIBDIR_SCHEMA=%{_lib} \
	      SYSTEM_FONTS=True

%install
scons install DESTDIR=%{buildroot} \
              PREFIX=%{_prefix} \
              THREADING=multi \
              XMLPARSER=libxml2 \
              GDAL_INCLUDES=%{_includedir}/gdal \
              INTERNAL_LIBAGG=False \
              LIBDIR_SCHEMA=%{_lib} \
	      SYSTEM_FONTS=True

# get rid of fonts use external instead
rm -rf %{buildroot}%{_libdir}/%{name}/fonts

# install more utils
mkdir -p %{buildroot}%{_bindir}
#install -p -m 755 demo/viewer/viewer %{buildroot}%{_bindir}/
install -p -m 755 utils/stats/mapdef_stats.py %{buildroot}%{_bindir}/
#install -p -m 644 %{SOURCE1} demo/data/

# install pkgconfig file
cat > %{name}.pc <<EOF
prefix=%{_prefix}
exec_prefix=%{_prefix}
includedir=%{_includedir}

Name: %{name}
Description: Free Toolkit for developing mapping applications
Version: %{version}
Libs: -lmapnik
Cflags: -I${includedir}/%{name} -I${includedir}/agg
EOF

mkdir -p %{buildroot}%{_datadir}/pkgconfig/
install -p -m 644 %{name}.pc %{buildroot}%{_datadir}/pkgconfig/

chrpath -d %{buildroot}%{_libdir}/mapnik/input/shape.input \
	%{buildroot}%{_libdir}/mapnik/input/raster.input \
	%{buildroot}%{_libdir}/mapnik/input/postgis.input \
	%{buildroot}%{_bindir}/shapeindex

%check
# export test enviroment
export PYTHONPATH=$PYTHONPATH:%{buildroot}%{python_sitearch}
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH%{buildroot}%{_libdir}

pushd tests/
./run_tests.py || true
popd

%files
%doc AUTHORS.md COPYING README.md
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/input
%{_libdir}/%{name}/input/*.input

%files -n %{libname}
%{_libdir}/lib%{name}.so.%{major}*

%files -n %{devname}
%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*.hpp
%{_includedir}/%{name}/*/*.hpp
%{_libdir}/lib%{name}.so
%{_datadir}/pkgconfig/%{name}.pc

%files python
%{python_sitearch}/%{name}
%{_bindir}/mapdef_stats.py
%{_bindir}/upgrade_map_xml.py
%{python_sitearch}/%{name}%{major}/__init__.py

%files utils
%{_bindir}/shapeindex
%{_bindir}/%{name}-config
%{_bindir}/%{name}-speed-check
%{_bindir}/svg2png



%changelog
* Sun Jun 10 2012 Matthew Dawkins <mattydaw@mandriva.org> 0.7.1-7
+ Revision: 804364
- rebuild
- added p0 for png15 build (upstream)
- cleaned up spec
- chrpath fixes

* Sun Jun 05 2011 Funda Wang <fwang@mandriva.org> 0.7.1-6
+ Revision: 682856
- update br
- rebuild for new icu

* Mon Mar 14 2011 Funda Wang <fwang@mandriva.org> 0.7.1-5
+ Revision: 644600
- force version 2 for filesystem
- rebuild for new icu

* Tue Nov 02 2010 Michael Scherer <misc@mandriva.org> 0.7.1-4mdv2011.0
+ Revision: 592416
- rebuild for python 2.7

* Mon Aug 23 2010 Funda Wang <fwang@mandriva.org> 0.7.1-3mdv2011.0
+ Revision: 572389
- rebuild for new boost

* Wed Aug 04 2010 Funda Wang <fwang@mandriva.org> 0.7.1-2mdv2011.0
+ Revision: 566007
- rebuild for new boost

* Mon Apr 26 2010 Emmanuel Andry <eandry@mandriva.org> 0.7.1-1mdv2010.1
+ Revision: 539350
- New version 0.7.1

* Sun Mar 21 2010 Funda Wang <fwang@mandriva.org> 0.7.0-4mdv2010.1
+ Revision: 526121
- rebuild for new icu

* Mon Feb 08 2010 Anssi Hannula <anssi@mandriva.org> 0.7.0-3mdv2010.1
+ Revision: 501882
- rebuild for new boost

* Wed Feb 03 2010 Funda Wang <fwang@mandriva.org> 0.7.0-2mdv2010.1
+ Revision: 500088
- rebuild for new boost

* Wed Jan 20 2010 Funda Wang <fwang@mandriva.org> 0.7.0-1mdv2010.1
+ Revision: 494015
- new version 0.7.0

* Thu Aug 20 2009 Emmanuel Andry <eandry@mandriva.org> 0.6.1-1mdv2010.0
+ Revision: 418585
- disable demo (breaks build)
- fix major
- use system fonts
- fix include path for demo viewer
- New version 0.6.1
- drop patches
- use mandriva library policy

* Thu Mar 12 2009 Emmanuel Andry <eandry@mandriva.org> 0.5.2-0.750.7mdv2009.1
+ Revision: 354290
- rebuild for new boost

* Thu Jan 29 2009 Funda Wang <fwang@mandriva.org> 0.5.2-0.750.6mdv2009.1
+ Revision: 335157
- rebuild

* Sat Jan 24 2009 Funda Wang <fwang@mandriva.org> 0.5.2-0.750.5mdv2009.1
+ Revision: 333279
- rebuild for new python

* Sun Dec 21 2008 Funda Wang <fwang@mandriva.org> 0.5.2-0.750.4mdv2009.1
+ Revision: 316865
- rebuild for new boost

* Fri Nov 07 2008 Olivier Blin <blino@mandriva.org> 0.5.2-0.750.3mdv2009.1
+ Revision: 300461
- remove hardcoded requires in devel package

* Fri Nov 07 2008 Olivier Blin <blino@mandriva.org> 0.5.2-0.750.2mdv2009.1
+ Revision: 300397
- fix font requires
- buildrequire python-devel
- fix groups
- fix build with freetype2
- initial Mandriva package (based on Fedora)
- create mapnik

