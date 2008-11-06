%define name mapnik
%define version 0.5.2
%define svn 750
%define rel 2
%define release %mkrel 0.%{svn}.%{rel}

Name:      %{name}
Version:   %{version}
Release:   %{release}
Summary:   Free Toolkit for developing mapping applications
Group:     Communications
License:   LGPLv2+
URL:       http://mapnik.org/
Source0:   http://download.berlios.de/mapnik/mapnik_src-%{version}.svn%{svn}.tar.gz
Source1:   mapnik-data.license
Source2:   no_date_footer.html
Source3:   viewer.desktop
Patch0:    use-system-fonts.patch
# (blino) use pkgconfig to build with freetype2
Patch1:	   mapnik-freetype2.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Requires:  fonts-ttf-dejavu

BuildRequires: postgresql-devel pkgconfig
BuildRequires: gdal-devel proj-devel agg-devel
BuildRequires: scons doxygen desktop-file-utils
BuildRequires: libltdl-devel qt4-devel > 4.3
BuildRequires: libxml2-devel boost-devel libicu-devel
BuildRequires: libtiff-devel libjpeg-devel libpng-devel
BuildRequires: cairomm-devel pycairo-devel
BuildRequires: freetype2-devel
BuildRequires: python-devel

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

%package devel
Summary: Mapnik is a Free toolkit for developing mapping applications
Group: Development/C++
Requires: %{name} = %{version}-%{release}
Requires: libpng-devel libjpeg-devel freetype-devel agg-devel

%description devel
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

%package python
Summary:  Python bindings for the Mapnik spatial visualization library
License:  GPLv2+
Group:    Development/Python
Requires: %{name} = %{version}-%{release}
Requires: python-imaging python-lxml

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

%package demo
Summary:  Demo utility and some sample data distributed with mapnik
License:  GPLv2+ GeoGratis
Group:    Development/Other
Requires: %{name}-devel = %{version}-%{release}
Requires: %{name}-python = %{version}-%{release}
Requires: freetype2-devel

%description demo
Demo application and sample vector datas distributed with the Mapnik
spatial visualization library

%prep
%setup -q -n %{name}
%patch0 -p0
%patch1 -p1 -b .freetype2

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
sed -i -e 's|/opt/boost/include/boost-1_34_1|%{_includedir}/boost|g' demo/viewer/viewer.pro
sed -i -e 's|-L/opt/mapnik/lib|-L../../src/|g' demo/viewer/viewer.pro
sed -i -e 's|/usr/local|/usr|g' demo/viewer/viewer.pro

%build

# linkage errors
sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\',|g" plugins/input/gdal/SConscript
sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\',|g" plugins/input/postgis/SConscript
sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\',|g" plugins/input/shape/SConscript
sed -i -e "s|libraries \= \[|libraries \= \[\'mapnik\'|g" plugins/input/raster/SConscript

# fix build flags
sed -i -e "s|common_cxx_flags = .-D\%s|common_cxx_flags = \'-D\%s $RPM_OPT_FLAGS |g" SConstruct

# WARNING smp may break build
# %{?_smp_mflags}
scons         PREFIX=%{_prefix} \
              THREADING=multi \
              XMLPARSER=libxml2 \
              GDAL_INCLUDES=%{_includedir}/gdal \
              INTERNAL_LIBAGG=False

# build mapnik viewer app
pushd demo/viewer
qmake viewer.pro
# WARNING smp may break build
# %{?_smp_mflags}
make
popd

# build doxygen docs
# use multilib aware footer
sed -i -e 's|HTML_FOOTER|HTML_FOOTER=no_date_footer.html\n\#|g' docs/doxygen/Doxyfile
install -p -m 644 %{SOURCE2} docs/doxygen/
pushd docs/doxygen
doxygen
popd

%install

rm -rf %{buildroot}

scons install DESTDIR=%{buildroot} \
              PREFIX=%{_prefix} \
              THREADING=multi \
              XMLPARSER=libxml2 \
              GDAL_INCLUDES=%{_includedir}/gdal \
              INTERNAL_LIBAGG=False

# get rid of fonts use external instead
rm -rf %{buildroot}%{_libdir}/%{name}/fonts

# install more utils
mkdir -p %{buildroot}%{_bindir}
install -p -m 755 demo/viewer/viewer %{buildroot}%{_bindir}/
install -p -m 755 utils/stats/mapdef_stats.py %{buildroot}%{_bindir}/
install -p -m 644 %{SOURCE1} demo/data/

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

# install desktop file
desktop-file-install --vendor="mandriva" \
        --dir=%{buildroot}%{_datadir}/applications %{SOURCE3}

%check

# export test enviroment
export PYTHONPATH=$PYTHONPATH:%{buildroot}%{python_sitearch}
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH%{buildroot}%{_libdir}

pushd tests/python/
./test_load_map.py || true
./test_save_map.py || true
popd

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc AUTHORS COPYING README
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/input
%{_libdir}/%{name}/input/*.input
%{_libdir}/lib%{name}.so.*

%files devel
%defattr(-,root,root,-)
%doc docs/doxygen/html
%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*
%{_libdir}/lib%{name}.so
%{_datadir}/pkgconfig/%{name}.pc

%files python
%defattr(-,root,root,-)
%{python_sitearch}/%{name}
%{_bindir}/mapdef_stats.py

%files utils
%defattr(-,root,root,-)
%{_bindir}/shapeindex
%{_bindir}/viewer
%{_datadir}/applications/mandriva-viewer.desktop

%files demo
%defattr(-,root,root,-)
%doc demo/c++
%doc demo/data
%doc demo/python demo/test
