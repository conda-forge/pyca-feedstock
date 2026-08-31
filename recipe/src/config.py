"""Host configuration information using EPICS names and build flags.

conda-forge note: this is a trimmed-down, vendored copy of
epicscorelibs.config (see
https://github.com/mdavidsaver/epicscorelibs/blob/master/src/python/epicscorelibs/config.py)
adapted so that pyca no longer needs setuptools_dso or epicscorelibs at
build time.

Upstream epicscorelibs.config determines 'CMPLR_CLASS' (and the
ABI-related C++ define, below) by actually invoking a C/C++ compiler's
preprocessor at build time (via setuptools_dso.probe.ProbeToolchain).
Since conda-forge's compiler family and C++ ABI are fixed and coherent
per-platform across the whole ecosystem (set by conda-forge's global
pinning, not by whatever compiler happens to be on PATH), we can hard
code the equivalent result instead of actually probing a compiler:
gcc on Linux, clang on macOS, MSVC on Windows; libstdc++ new ('=1') ABI
on Linux since conda-forge switched ecosystem-wide in 2019.
"""

import platform


__all__ = (
    'get_config_var',
    'get_config_vars',
)

_CMPLR_CLASS_BY_OS = {
    'Linux': 'gcc',
    'Darwin': 'clang',
    'WIN32': 'msvc',
}


def _makeconf():
    conf = {}

    # map from python system name to epics OS_CLASS
    osname = conf['OS_CLASS'] = {
        'Linux': 'Linux',
        'Windows': 'WIN32',
        'Darwin': 'Darwin',
    }[platform.system()]

    conf['CMPLR_CLASS'] = _CMPLR_CLASS_BY_OS[osname]

    machine = platform.machine().lower()  # host CPU
    bits = {
        '32bit': 32,
        '64bit': 64,
    }[platform.architecture()[0]]

    conf['POSIX'] = osname != 'WIN32'

    # pick a host arch (must match epics-base's EPICS_HOST_ARCH)
    HA = None
    if osname == 'Linux':
        if machine == 'x86_64':
            HA = 'linux-x86_64'
        elif machine == 'ppc':
            HA = 'linux-ppc'
        elif machine.startswith('arm') or machine == 'aarch64':
            HA = 'linux-aarch64' if machine == 'aarch64' else 'linux-arm'
        elif machine.endswith('86'):
            HA = 'linux-x86'
        else:
            raise RuntimeError("Unsupported Linkage: " + machine)

    elif osname == 'Darwin':
        if machine == 'arm64':
            HA = 'darwin-aarch64'
        else:
            HA = 'darwin-x86'

    elif osname == 'WIN32':
        if bits == 64:
            HA = 'windows-x64'
        else:
            HA = 'win32-x86'

    if HA is None:
        raise RuntimeError("Unable to determine host arch")

    conf['EPICS_HOST_ARCH'] = conf['T_A'] = HA
    return conf


_config = _makeconf()
del _makeconf


def _makebuild():
    build = {
        'CPPFLAGS': [],
        'CFLAGS': [],
        'CXXFLAGS': [],
        'LDFLAGS': [],
        'LDADD': [],
    }

    OS_CLASS = _config['OS_CLASS']

    if OS_CLASS == 'Linux':
        build['CPPFLAGS'] += [('_GNU_SOURCE', None), ('_DEFAULT_SOURCE', None), ('linux', None)]
        build['LDADD'] += ['m', 'rt', 'dl']
        # Only GCC's libstdc++ has the dual-ABI problem that
        # '_GLIBCXX_USE_CXX11_ABI' addresses (not applicable to
        # clang/libc++ on macOS, or MSVC on Windows). conda-forge has
        # built with the new ('=1') ABI ecosystem-wide since 2019.
        build['CPPFLAGS'] += [('_GLIBCXX_USE_CXX11_ABI', '1')]

    if OS_CLASS == 'Darwin':
        build['CPPFLAGS'] += [('darwin', None)]
        build['CXXFLAGS'] += ['-std=c++11', '-stdlib=libc++']
        build['LDFLAGS'] += ['-std=c++11', '-stdlib=libc++']

    if OS_CLASS != 'WIN32':
        build['CPPFLAGS'] += [('UNIX', None)]

    if OS_CLASS == 'WIN32':
        build['CPPFLAGS'] += [('EPICS_BUILD_DLL', None), ('EPICS_CALL_DLL', None), ('NOMINMAX', None)]
        build['CXXFLAGS'] += ['-EHsc']
        build['LDADD'] += ['netapi32', 'ws2_32', 'advapi32', 'user32']

    return build


_config.update(_makebuild())
del _makebuild


def get_config_var(key):
    from copy import deepcopy
    return deepcopy(_config.get(key))


def get_config_vars():
    from copy import deepcopy
    return deepcopy(_config)
